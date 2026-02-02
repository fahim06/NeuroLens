# ============================================================
# NeuroLens Backend — Production Dockerfile
# ============================================================
# Multi-stage build for Django REST API
# Optimized for production with minimal image size
# ============================================================

# =====================================================
# Stage 1: Builder
# =====================================================
FROM python:3.12-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt* ./
RUN pip install --no-cache-dir --upgrade pip wheel \
    && pip wheel --no-cache-dir --wheel-dir /app/wheels -r requirements.txt

# =====================================================
# Stage 2: Production
# =====================================================
FROM python:3.12-slim as production

# Build arguments
ARG ENVIRONMENT=production
ARG VERSION=0.0.0

# Environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    ENVIRONMENT=${ENVIRONMENT} \
    VERSION=${VERSION} \
    PORT=8000

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash appuser

# Copy wheels from builder
COPY --from=builder /app/wheels /wheels
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir /wheels/* \
    && rm -rf /wheels

# Copy application code
COPY --chown=appuser:appuser . .

# Collect static files
RUN python manage.py collectstatic --noinput 2>/dev/null || true

# Switch to non-root user
USER appuser

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:${PORT}/api/health/ || exit 1

# Expose port
EXPOSE ${PORT}

# Run with gunicorn
CMD ["sh", "-c", "gunicorn neurolens.wsgi:application --bind 0.0.0.0:${PORT} --workers 4 --threads 2 --worker-class gthread --access-logfile - --error-logfile -"]
