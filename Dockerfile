ARG IMAGE_VERSION=3.12-slim@sha256:2e683fc3e18a248aa23b8022f2a3474b072b04fb851efe9b49f6b516a8944939
#--------------------------------------------------------------------------------
# Build the package
#--------------------------------------------------------------------------------
FROM python:${IMAGE_VERSION} AS builder
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8
# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
COPY . .
RUN uv sync --frozen --no-cache
RUN uv build

#--------------------------------------------------------------------------------
# Install the package in a clean runtime environment
#--------------------------------------------------------------------------------
FROM python:${IMAGE_VERSION} AS runtime-builder
# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONIOENCODING=utf-8
# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
COPY --from=builder /app/dist/ ./dist/
RUN uv venv && \
    uv pip install --no-cache ./dist/*.whl

#--------------------------------------------------------------------------------
# Final stage
#--------------------------------------------------------------------------------
FROM python:${IMAGE_VERSION}
ENV VIRTUAL_ENV="/app/.venv"
ENV PATH="$VIRTUAL_ENV/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    WEB_CONCURRENCY=1 \
    WORKER_TIMEOUT=1200 \
    PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=info

WORKDIR /app

# Copy files from builder and local
COPY --from=runtime-builder /app/.venv /app/.venv
COPY prompts/ /app/prompts/
COPY config/ /app/config/
COPY public/ /app/public/
COPY .chainlit/ /app/.chainlit/
COPY src/. .

# Create user and set up directories,
# set permissions and prepare runtime environment
RUN adduser --system --no-create-home --group nonroot && \
    mkdir -p /app/.files && \
    chmod +x /app/startup.sh && \
    chown -R nonroot:nonroot /app/config /app/.files && \
    chmod 700 /app/.files && \
    touch /app/.env && \
    chown nonroot:nonroot /app/.env

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"

USER nonroot
EXPOSE 8000
# Run the application
CMD ["/app/startup.sh"]
