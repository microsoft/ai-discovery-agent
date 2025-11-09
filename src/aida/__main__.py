# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Main entry point for AI Discovery Agent.

This module serves as the main entry point when running the application
with `python -m aida` or using the `aida` command. It starts the uvicorn
server with the FastAPI application.
"""

import os
import sys

import uvicorn

from aida.app import create_app, init_app
from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security


def main() -> None:
    """Entrypoint to invoke when this module is invoked on the remote server."""
    # Access command-line arguments
    arguments = sys.argv

    if(len(arguments) > 1 and arguments[1] == "init"):
        logger.info("Initializing application files...")
        init_app()
    else:
        app = create_app()

        # See the official documentations on how "0.0.0.0" makes the service available on
        # the local network - https://www.uvicorn.org/settings/#socket-binding
        # Using configurable HOST from environment variable for security
        # In production, set HOST=0.0.0.0 to bind to all interfaces when needed
        logger.info(f"Starting uvicorn server on {HOST}:{PORT}")
        uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
