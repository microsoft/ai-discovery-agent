# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""FastAPI application factory for AI Discovery Agent.

This module provides the FastAPI application factory that creates and configures
the main application instance. It includes health check endpoints for monitoring
and integrates with Chainlit for the chat interface.

The application is designed to be deployed on Azure App Service and includes
proper health check endpoints for container orchestration.
"""

import os
import shutil
from pathlib import Path

from chainlit.utils import mount_chainlit
from fastapi import FastAPI, status
from fastapi.responses import FileResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


def ensure_folder_from_static(target_folder: str, static_subfolder: str) -> None:
    """
    Ensure that the target folder exists by copying it from the static assets if necessary.

    Args:
        target_folder: The name of the folder to create (e.g., "public").
        static_subfolder: The subfolder in static to copy from (e.g., "public").
    """
    if not os.path.exists(target_folder):
        logger.info(f"Creating {target_folder} folder from static assets")
        src_folder = os.path.join(
            os.path.dirname(__file__), f"static/{static_subfolder}"
        )
        if not os.path.exists(src_folder):
            logger.error(f"Source {target_folder} folder does not exist: {src_folder}")
        else:
            try:
                shutil.copytree(src_folder, target_folder)
            except Exception as e:
                logger.error(
                    f"Failed to copy {target_folder} folder from {src_folder} to '{target_folder}': {e}",
                    exc_info=True,
                )


def init_app():
    """Initialize application by ensuring necessary folders exist."""
    logger.info("Initializing application folders")
    ensure_folder_from_static("public", "public")
    ensure_folder_from_static("config", "config")
    ensure_folder_from_static("prompts", "prompts")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance with health check
            endpoints and Chainlit integration mounted at the root path.
    """
    init_app()

    # FastAPI application instance for the AI Discovery Agent
    # Provides REST API endpoints and serves as the main server entry point
    app = FastAPI(
        title="AI Discovery Agent",
        description="FastAPI server for AI-powered workshop facilitation with Chainlit integration",
        version="1.0.0",
    )

    @app.get(
        "/public/elements/MermaidViewer.jsx",
        name="MermaidViewer.jsx",
        tags=["static"],
        summary="Get Mermaid Diagram Source",
        response_class=FileResponse,
    )
    def get_mermaid_source() -> str:
        """Get the Mermaid diagram source from static assets.

        Returns:
            FileResponse: Mermaid diagram source as a file response.
        """
        mermaid_file_path = os.path.join(
            Path.cwd(), "public/elements/MermaidViewer.jsx"
        )
        if not os.path.exists(mermaid_file_path):
            mermaid_file_path = os.path.join(
                os.path.dirname(__file__),
                "static/elements/MermaidViewer.jsx",
            )
        return mermaid_file_path

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
    mount_chainlit(
        app, target=os.path.join(os.path.dirname(__file__), "chainlit.py"), path="/"
    )

    return app
