# =============================================================================
# Dockerfile for Kannadi / DARPAN Protocol
# Multi-platform production-ready container (amd64 / arm64)
# =============================================================================

FROM python:3.11-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Install required system dependencies:
# - build-essential, cmake: for C/C++ compilation if needed by wheels
# - libgl1, libglib2.0-0: OpenCV graphics and GL dependencies
# - libgomp1: OpenMP for ONNX Runtime / InsightFace inference
# - curl: for container healthcheck
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    cmake \
    libgl1 \
    libglib2.0-0 \
    libgomp1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set up non-root user for container security
RUN groupadd -g 1001 appgroup && \
    useradd -u 1001 -g appgroup -m -s /bin/bash appuser

# Set working directory
WORKDIR /app

# Copy dependency specifications first to maximize Docker layer caching
COPY requirements.txt ./

# Upgrade pip and install Python packages
RUN pip install --no-cache-dir -U pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code and assets
COPY . .

# Ensure proper directories exist and are owned by appuser
RUN mkdir -p /app/output /home/appuser/.insightface && \
    chown -R appuser:appgroup /app /home/appuser/.insightface

# Switch to non-root user
USER appuser

# Expose Streamlit port
EXPOSE 8501

# Health check to ensure Streamlit server is active and serving traffic
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Default launch command
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
