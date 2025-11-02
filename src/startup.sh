#!/bin/bash
set -e

# Enable debugging if needed
if [ "${DEBUG:-false}" = "true" ]; then
    set -x
fi

echo "=================================================="
echo "Starting AI Discovery Agent Application"
echo "=================================================="
echo "Timestamp: $(date)"
echo "Python version: $(python --version)"
echo "Working directory: $(pwd)"
echo "User: $(whoami)"
echo "Environment: ${OTEL_SERVICE_NAME:-unknown}"

# Show environment variables (excluding sensitive ones)
echo "Environment variables:"
env | grep -E "^(AZURE|CHAINLIT|PYTHON|WEB_|WORKER_|WEBSITE_|OAUTH_)" | grep -v -E "(SECRET|KEY|TOKEN)" | sort

echo "Contents of current directory:"
ls -la

# Verify essential files exist
for file in "server.py" "main.py"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file $file not found!"
        exit 1
    fi
done

# Set default values for performance
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"

# Performance and worker settings
WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}
WORKER_TIMEOUT=${WORKER_TIMEOUT:-1200}
PORT=${PORT:-8000}
HOST=${HOST:-"0.0.0.0"}
LOG_LEVEL=${LOG_LEVEL:-"info"}

echo "Starting application with the following settings:"
echo "  - Port: $PORT"
echo "  - Host: $HOST"
echo "  - Workers: $WEB_CONCURRENCY"
echo "  - Worker timeout: $WORKER_TIMEOUT seconds"

# Link auth-config.yaml from secrets directory if it exists when running
# inside Azure App Service
if [ -f /home/site/wwwroot/secrets/auth-config.yaml ]; then
    echo "Linking auth-config.yaml from secrets directory..."
    ln -sf /home/site/wwwroot/secrets/auth-config.yaml /app/config/auth-config.yaml
else
    echo "No auth-config.yaml found in secrets directory."
fi

# Start the application with error handling
echo "Starting uvicorn server..."
exec python -m uvicorn server:app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WEB_CONCURRENCY" \
    --timeout-keep-alive "$WORKER_TIMEOUT" \
    --access-log \
    --log-level "$LOG_LEVEL"
