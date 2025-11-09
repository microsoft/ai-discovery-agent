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

from chainlit.utils import mount_chainlit
from fastapi import FastAPI, status
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)


class HealthCheck(BaseModel):
    """Response model to validate and return when performing a health check."""

    status: str = "OK"


def init_app():
    """Initialize application by ensuring necessary folders exist."""
    if (
        not os.path.exists("public")
        or not os.path.exists("config")
        or not os.path.exists("prompts")
    ):

        logger.info("Initializing application folders")
        # if public folder does not exist copy from src/aida/static/public
        if not os.path.exists("public"):
            logger.info("Creating public folder from static assets")
            # construct path to static assets
            shutil.copytree(
                os.path.join(os.path.dirname(__file__), "static/public"), "public"
            )
        # if config folder does not exist copy from src/aida/static/config
        if not os.path.exists("config"):
            logger.info("Creating config folder from static assets")
            # construct path to static assets
            shutil.copytree(
                os.path.join(os.path.dirname(__file__), "static/config"), "config"
            )

        if not os.path.exists("prompts"):
            logger.info("Creating prompts folder from static assets")
            # construct path to static assets
            shutil.copytree(
                os.path.join(os.path.dirname(__file__), "static/prompts"), "prompts"
            )


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
