# Paraguay Geodata — local dev Dockerfile
# Use: docker build -t paraguay-geodata . && docker run -p 8000:8000 paraguay-geodata
# This serves the static `exports/web/` (and runs the small CF Worker locally).
FROM python:3.12-slim AS base

WORKDIR /app

# System deps for Pillow / rasterio wheel builds
RUN apt-get update -qq && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libproj-dev \
        libgeos-dev \
        libgdal-dev \
        libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Python deps
COPY pyproject.toml /app/
RUN pip install --no-cache-dir --upgrade pip setuptools wheel && \
    pip install --no-cache-dir ".[dev]" || pip install --no-cache-dir -e .

COPY . /app/

# ----------------------------------------------------------------------------
# Local dev: serve exports/web/ on port 8000 with a tiny Python http server.
# In production we deploy to Cloudflare Pages (no server needed).
# ----------------------------------------------------------------------------
FROM base AS dev
EXPOSE 8000
CMD ["python3", "-m", "http.server", "8000", "--directory", "exports/web", "--bind", "0.0.0.0"]

# ----------------------------------------------------------------------------
# Test runner: run the full pytest suite as the ENTRYPOINT.
# ----------------------------------------------------------------------------
FROM base AS test
RUN find . -name __pycache__ -type d -exec rm -rf {} + 2>/dev/null
CMD ["pytest", "-q", "--no-header"]
