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
from dotenv import load_dotenv
from fastapi import FastAPI, status
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

# Load env values from file before importing other modules
load_dotenv(".azure.env", override=False)
load_dotenv(".env", override=False)

PORT = int(os.getenv("PORT", 8000))
HOST = os.getenv("HOST", "127.0.0.1")  # Default to localhost for security


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


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


FastAPIInstrumentor.instrument_app(app)

# Mount the Chainlit application at the root path ("/")
# This integrates the Chainlit chat interface with the FastAPI server
# The target "main.py" contains the Chainlit application logic
mount_chainlit(app, target="main.py", path="/")


def main() -> None:
    """Entrypoint to invoke when this module is invoked on the remote server."""
    # See the official documentations on how "0.0.0.0" makes the service available on
    # the local network - https://www.uvicorn.org/settings/#socket-binding
    # Using configurable HOST from environment variable for security
    # In production, set HOST=0.0.0.0 to bind to all interfaces when needed
    uvicorn.run("server:app", host=HOST, port=PORT)


if __name__ == "__main__":
    main()
