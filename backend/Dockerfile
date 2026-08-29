# ============================================================
# Production Dockerfile — OTP Backend
# Multi-stage build: builder stage compiles wheels, runtime
# stage copies only what's needed. Runs as non-root user.
# ============================================================

# ── Stage 1: builder ────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build-time deps (some wheels need compilation)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# ── Stage 2: runtime ────────────────────────────────────────
FROM python:3.11-slim AS runtime

# Runtime deps only (libpq for psycopg2-binary at import time)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 curl && \
    rm -rf /var/lib/apt/lists/*

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Create non-root user
RUN groupadd -r app && useradd -r -g app -d /app -s /sbin/nologin app

WORKDIR /app

# Copy application code
COPY . .

# Make entrypoint executable
RUN chmod +x start.sh

# Own everything to app user
RUN chown -R app:app /app

USER app

EXPOSE 8000

# Healthcheck — hits root endpoint every 30s
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8000/ || exit 1

# Entrypoint: run migrations, then boot uvicorn
CMD ["./start.sh"]
