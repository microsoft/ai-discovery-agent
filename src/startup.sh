#!/bin/bash
set -e

# List of essential files for the application
ESSENTIAL_FILES=("pyproject.toml" "aida/__main__.py")

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
for file in "${ESSENTIAL_FILES[@]}"; do
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

SECRETS_DIR="${SECRETS_DIR:-/home/site/wwwroot/secrets}"
APP_CONFIG_DIR="${APP_CONFIG_DIR:-/app/config}"
echo "Starting application with the following settings:"
echo "  - Port: $PORT"
echo "  - Host: $HOST"
echo "  - Workers: $WEB_CONCURRENCY"
echo "  - Worker timeout: $WORKER_TIMEOUT seconds"

# Link auth-config.yaml from secrets directory if it exists when running
# inside Azure App Service
if [ -f "$SECRETS_DIR/auth-config.yaml" ]; then
    echo "Preparing to link auth-config.yaml from secrets directory ($SECRETS_DIR)..."
    # Ensure /app/config exists
    if [ ! -d "$APP_CONFIG_DIR" ]; then
        echo "Directory $APP_CONFIG_DIR does not exist. Creating it..."
        if ! mkdir -p "$APP_CONFIG_DIR"; then
            echo "ERROR: Failed to create $APP_CONFIG_DIR directory!"
            exit 1
        fi
    fi
    # Check if $APP_CONFIG_DIR is writable
    if [ ! -w "$APP_CONFIG_DIR" ]; then
        echo "ERROR: $APP_CONFIG_DIR is not writable!"
        exit 1
    fi
    # Check if $APP_CONFIG_DIR/auth-config.yaml exists as a regular file (not a symlink)
    if [ -f "$APP_CONFIG_DIR/auth-config.yaml" ] && [ ! -L "$APP_CONFIG_DIR/auth-config.yaml" ]; then
        echo "ERROR: $APP_CONFIG_DIR/auth-config.yaml exists as a regular file and will NOT be overwritten to avoid data loss."
        echo "Please remove or backup the file before running this script."
        exit 1
    fi
    # Attempt to create the symlink
    # Check ownership and permissions before symlinking
    AUTH_CONFIG_SOURCE="$SECRETS_DIR/auth-config.yaml"
    EXPECTED_UID=$(id -u)
    FILE_UID=$(stat -c %u "$AUTH_CONFIG_SOURCE")
    FILE_PERMS=$(stat -c %a "$AUTH_CONFIG_SOURCE")
    if [ "$FILE_UID" != "$EXPECTED_UID" ]; then
        echo "ERROR: $AUTH_CONFIG_SOURCE is not owned by the expected user ($(whoami))!"
        exit 1
    fi
    if [ "$FILE_PERMS" -ne 600 ] && [ "$FILE_PERMS" -ne 640 ]; then
        echo "ERROR: $AUTH_CONFIG_SOURCE permissions ($FILE_PERMS) are not secure! Must be 600 or 640."
        exit 1
    fi
    if ! ln -sf "$AUTH_CONFIG_SOURCE" "$APP_CONFIG_DIR/auth-config.yaml"; then
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
