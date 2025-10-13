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
env | grep -E "^(AZURE|CHAINLIT|PYTHON|WEB_|WORKER_|WEBSITE_)" | grep -v -E "(SECRET|KEY|TOKEN)" | sort

echo "Contents of current directory:"
ls -la

# Verify essential files exist
for file in "server.py" "main.py"; do
    if [ ! -f "$file" ]; then
        echo "ERROR: Required file $file not found!"
        exit 1
    fi
done

# Install dependencies if requirements.txt exists
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies from requirements.txt..."
    pip install --no-cache-dir -r requirements.txt
else
    echo "WARNING: No requirements.txt found, dependencies may not be installed"
fi

# Set default values for performance
export PYTHONUNBUFFERED="${PYTHONUNBUFFERED:-1}"
export PYTHONIOENCODING="${PYTHONIOENCODING:-utf-8}"
export PYTHONDONTWRITEBYTECODE="${PYTHONDONTWRITEBYTECODE:-1}"

# Performance and worker settings
WEB_CONCURRENCY=${WEB_CONCURRENCY:-1}
WORKER_TIMEOUT=${WORKER_TIMEOUT:-1200}
PORT=${PORT:-8000}

echo "Starting application with the following settings:"
echo "  - Port: $PORT"
echo "  - Workers: $WEB_CONCURRENCY"
echo "  - Worker timeout: $WORKER_TIMEOUT seconds"

# Validate Python modules can be imported
echo "Validating Python modules..."
python -c "import server, main; print('✓ All modules imported successfully')" || {
    echo "ERROR: Failed to import required modules"
    exit 1
}

# Start the application with error handling
echo "Starting uvicorn server..."
exec python -m uvicorn server:app \
    --host 0.0.0.0 \
    --port "$PORT" \
    --workers "$WEB_CONCURRENCY" \
    --timeout-keep-alive "$WORKER_TIMEOUT" \
    --access-log \
    --log-level info
