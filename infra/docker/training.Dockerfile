# Training Dockerfile
# Full ML environment for model training

# ============================================
# Stage 1: Base
# ============================================
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    libhdf5-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Upgrade pip
RUN pip install --no-cache-dir --upgrade pip

# ============================================
# Stage 2: Dependencies
# ============================================
FROM base as dependencies

# Install ML dependencies
RUN pip install --no-cache-dir \
    tensorflow==2.15.* \
    numpy \
    pandas \
    scikit-learn \
    pillow \
    matplotlib \
    seaborn \
    mlflow \
    pyyaml \
    tqdm

# Install training utilities
RUN pip install --no-cache-dir \
    tensorboard \
    keras-tuner \
    optuna

# ============================================
# Stage 3: Training Image
# ============================================
FROM python:3.11-slim as training

WORKDIR /app

# Create training user
RUN groupadd --gid 1000 trainer && \
    useradd --uid 1000 --gid trainer --shell /bin/bash --create-home trainer

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    libhdf5-103 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment
COPY --from=dependencies /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy application code
COPY ml/ ./ml/
COPY scripts/ ./scripts/

# Create directories
RUN mkdir -p /app/data /app/models /app/logs /app/artifacts && \
    chown -R trainer:trainer /app

# Switch to non-root user
USER trainer

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=1 \
    MLFLOW_TRACKING_URI=/app/mlruns \
    DATA_DIR=/app/data \
    MODEL_DIR=/app/models \
    LOG_DIR=/app/logs

# Volume mounts
VOLUME ["/app/data", "/app/models", "/app/logs", "/app/artifacts"]

# Default command: run training script
CMD ["python", "-m", "ml.training.train"]

# ============================================
# Stage 4: GPU Training
# ============================================
FROM nvidia/cuda:12.2.0-devel-ubuntu22.04 as gpu-training

WORKDIR /app

# Install Python and dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3.11-dev \
    python3-pip \
    curl \
    git \
    libhdf5-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Create and activate venv
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install TensorFlow with CUDA support
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    tensorflow[and-cuda] \
    numpy \
    pandas \
    scikit-learn \
    pillow \
    matplotlib \
    mlflow \
    tensorboard \
    keras-tuner \
    optuna \
    pyyaml \
    tqdm

# Copy application
COPY ml/ ./ml/
COPY scripts/ ./scripts/

# Create trainer user and directories
RUN groupadd --gid 1000 trainer && \
    useradd --uid 1000 --gid trainer --shell /bin/bash --create-home trainer && \
    mkdir -p /app/data /app/models /app/logs /app/artifacts && \
    chown -R trainer:trainer /app

USER trainer

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=1 \
    NVIDIA_VISIBLE_DEVICES=all \
    MLFLOW_TRACKING_URI=/app/mlruns

VOLUME ["/app/data", "/app/models", "/app/logs", "/app/artifacts"]

CMD ["python", "-m", "ml.training.train"]

# ============================================
# Stage 5: Jupyter Notebook
# ============================================
FROM training as notebook

USER root

# Install Jupyter
RUN pip install --no-cache-dir \
    jupyter \
    jupyterlab \
    ipywidgets

USER trainer

# Expose Jupyter port
EXPOSE 8888

# Run Jupyter Lab
CMD ["jupyter", "lab", "--ip=0.0.0.0", "--port=8888", "--no-browser", "--NotebookApp.token=''"]
