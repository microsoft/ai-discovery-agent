# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""FastAPI server module for AI Discovery Agent.

This module provides a FastAPI server that serves the Chainlit application
for AI discovery workshops. It includes health check endpoints for monitoring
and integrates with Chainlit for the main chat interface.

The server is designed to be deployed on Azure App Service and includes
proper health check endpoints for container orchestration.
"""

import os

import uvicorn
from dotenv import load_dotenv

from aida import create_app
from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)

# Load env values from file before importing other modules
load_dotenv(".azure.env", override=False)
load_dotenv(".env", override=False)

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security

app = create_app()


def main() -> None:
    """Entrypoint to invoke when this module is invoked on the remote server."""
    # See the official documentations on how "0.0.0.0" makes the service available on
    # the local network - https://www.uvicorn.org/settings/#socket-binding
    # Using configurable HOST from environment variable for security
    # In production, set HOST=0.0.0.0 to bind to all interfaces when needed

    logger.info(f"Starting uvicorn server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
