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
for file in "pyproject.toml" "aida/__main__.py"; do
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
    echo "Preparing to link auth-config.yaml from secrets directory..."
    # Ensure /app/config exists
    if [ ! -d /app/config ]; then
        echo "Directory /app/config does not exist. Creating it..."
        mkdir -p /app/config
        if [ $? -ne 0 ]; then
            echo "ERROR: Failed to create /app/config directory!"
            exit 1
        fi
    fi
    # Check if /app/config is writable
    if [ ! -w /app/config ]; then
        echo "ERROR: /app/config is not writable!"
        exit 1
    fi
    # Check if /app/config/auth-config.yaml exists as a regular file (not a symlink)
    if [ -f /app/config/auth-config.yaml ] && [ ! -L /app/config/auth-config.yaml ]; then
        echo "ERROR: /app/config/auth-config.yaml exists as a regular file and will NOT be overwritten to avoid data loss."
        echo "Please remove or backup the file before running this script."
        exit 1
    fi
    # Attempt to create the symlink
    ln -sf /home/site/wwwroot/secrets/auth-config.yaml /app/config/auth-config.yaml
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create symlink for auth-config.yaml!"
        exit 1
    fi
    echo "✓ Successfully linked auth-config.yaml"
else
    echo "No auth-config.yaml found in secrets directory."
fi

# Start the application with error handling
echo "Starting uvicorn server..."
exec python -m uvicorn --factory aida:create_app \
    --host "$HOST" \
    --port "$PORT" \
    --workers "$WEB_CONCURRENCY" \
    --timeout-keep-alive "$WORKER_TIMEOUT" \
    --access-log \
    --log-level "$LOG_LEVEL"
