#!/bin/bash
echo "Starting Chainlit application..."
python -m uvicorn server:app --host 0.0.0.0 --port 8000
