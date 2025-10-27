# Install uv
FROM python:3.12-slim AS builder
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONIOENCODING=utf-8
# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --locked --no-install-project --no-editable --no-dev

FROM python:3.12-slim
ENV VIRTUAL_ENV=/app/.venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH" \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy the environment, but not the source code
COPY --from=builder /app/.venv /app/.venv
EXPOSE 8000

ENV WEB_CONCURRENCY=1 \
    WORKER_TIMEOUT=1200 \
    PORT=8000 \
    HOST=0.0.0.0 \
    LOG_LEVEL=info

ADD . .
RUN chmod +x /app/startup.sh

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health').read()"
# Run the application
CMD ["/app/startup.sh"]
