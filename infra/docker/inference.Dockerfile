# Inference Server Dockerfile
# Optimized for low-latency model serving

# ============================================
# Stage 1: Builder
# ============================================
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install inference dependencies (minimal)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    tensorflow==2.15.* \
    numpy \
    pillow \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    pydantic>=2.0

# ============================================
# Stage 2: Production
# ============================================
FROM python:3.11-slim as production

WORKDIR /app

# Create non-root user
RUN groupadd --gid 1000 inference && \
    useradd --uid 1000 --gid inference --shell /bin/bash --create-home inference

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy ML code and models
COPY ml/ ./ml/

# Create model directory
RUN mkdir -p /app/models && chown -R inference:inference /app

# Switch to non-root user
USER inference

# Environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    MODEL_PATH=/app/models/production \
    PORT=8001

# Health check
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:${PORT}/health || exit 1

# Expose port
EXPOSE ${PORT}

# Pre-warm model on startup
ENV WARMUP_REQUESTS=5

# Run inference server
CMD ["python", "-m", "ml.inference.server"]

# ============================================
# Stage 3: GPU Support
# ============================================
FROM nvidia/cuda:12.2.0-runtime-ubuntu22.04 as gpu

WORKDIR /app

# Install Python
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3.11 \
    python3.11-venv \
    python3-pip \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Create venv
RUN python3.11 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install TensorFlow with GPU support
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
    tensorflow[and-cuda] \
    numpy \
    pillow \
    fastapi \
    uvicorn[standard] \
    python-multipart \
    pydantic>=2.0

# Copy application
COPY ml/ ./ml/

# Create non-root user
RUN groupadd --gid 1000 inference && \
    useradd --uid 1000 --gid inference --shell /bin/bash --create-home inference && \
    mkdir -p /app/models && \
    chown -R inference:inference /app

USER inference

ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    TF_CPP_MIN_LOG_LEVEL=2 \
    NVIDIA_VISIBLE_DEVICES=all \
    PORT=8001

EXPOSE ${PORT}

CMD ["python", "-m", "ml.inference.server"]
