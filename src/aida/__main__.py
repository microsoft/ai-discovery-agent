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
from chainlit.utils import mount_chainlit
from fastapi import FastAPI, status
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


def create_app() -> FastAPI:

    # FastAPI application instance for the AI Discovery Agent
    # Provides REST API endpoints and serves as the main server entry point
    app = FastAPI(
        title="AI Discovery Agent",
        description="FastAPI server for AI-powered workshop facilitation with Chainlit integration",
        version="1.0.0",
    )

    @app.get(
        "/health",
        tags=["healthcheck"],
        summary="Perform a Health Check",
        response_description="Return HTTP Status Code 200 (OK)",
        status_code=status.HTTP_200_OK,
        response_model=HealthCheck,
    )
    def get_health() -> HealthCheck:
        """
        ## Perform a Health Check
        Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
        to ensure a robust container orchestration and management is in place. Other
        services which rely on proper functioning of the API service will not deploy if this
        endpoint returns any other HTTP status code except 200 (OK).
        Returns:
            HealthCheck: Returns a JSON response with the health status
        """
        return HealthCheck(status="OK")

    logger.info("Initializing FastAPI server for AI Discovery Agent")
    FastAPIInstrumentor.instrument_app(app)

    # Mount the Chainlit application at the root path ("/")
    # This integrates the Chainlit chat interface with the FastAPI server
    # The target "aida/__main__.py" contains the Chainlit application logic
    logger.info("Mounting Chainlit application at root path '/'")
    mount_chainlit(app, target="aida/chainlit.py", path="/")

    return app


def main() -> None:
    """Entrypoint to invoke when this module is invoked on the remote server."""
    app = create_app()

    # See the official documentations on how "0.0.0.0" makes the service available on
    # the local network - https://www.uvicorn.org/settings/#socket-binding
    # Using configurable HOST from environment variable for security
    # In production, set HOST=0.0.0.0 to bind to all interfaces when needed
    logger.info(f"Starting uvicorn server on {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)


if __name__ == "__main__":
    main()
