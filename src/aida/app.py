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
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from pydantic import BaseModel
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Middleware to add security headers to all responses.

    This middleware adds defense-in-depth security headers. In Azure App Service
    deployment, these headers are also set at the infrastructure level, but setting
    them in the application ensures they're present even in development environments.
    """

    def __init__(self, app: ASGIApp):
        """Initialize the security headers middleware.

        Args:
            app: The ASGI application.
        """
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        """Add security headers to the response.

        Args:
            request: The incoming request.
            call_next: The next middleware in the chain.

        Returns:
            Response with security headers added.
        """
        response = await call_next(request)

        # X-Content-Type-Options: Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Prevent clickjacking attacks
        response.headers["X-Frame-Options"] = "SAMEORIGIN"

        # Content-Security-Policy: Mitigate XSS and injection attacks
        # Note: Chainlit's React-based UI requires 'unsafe-inline' and 'unsafe-eval'
        # These directives weaken XSS protection but are necessary for framework functionality
        # Chainlit dynamically generates inline styles and uses eval for React components
        # Nonces/hashes are not feasible as Chainlit doesn't expose CSP configuration hooks
        # Mitigation: Strict input validation and output encoding at application level
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com",
            "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://fonts.googleapis.com",
            "font-src 'self' data: https://fonts.gstatic.com https://cdn.jsdelivr.net",
            "img-src 'self' data: https:",
            "connect-src 'self' wss: ws: https:",
            "frame-ancestors 'self'",
            "base-uri 'self'",
            "form-action 'self'",
        ]
        response.headers["Content-Security-Policy"] = "; ".join(csp_directives)

        # Permissions-Policy: Restrict access to browser features
        # Allow camera and microphone if needed for future voice features
        permissions_policy = [
            "geolocation=()",
            "payment=()",
            "usb=()",
        ]
        response.headers["Permissions-Policy"] = ", ".join(permissions_policy)

        # Referrer-Policy: Control referrer information
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        return response


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
    target_path = Path(target_folder)
    if not target_path.exists():
        logger.info(f"Creating {target_folder} folder from static assets")
        src_folder = Path(__file__).parent / "static" / static_subfolder
        if not src_folder.exists():
            logger.error(
                f"Source static/{static_subfolder} folder does not exist in {src_folder}"
            )
        else:
            try:
                shutil.copytree(src_folder, target_path)
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

    # Add security headers middleware for defense-in-depth
    app.add_middleware(SecurityHeadersMiddleware)

    # Configure CORS for Chainlit WebSocket support
    # Default to localhost for development; production should set ALLOWED_ORIGINS env var
    allowed_origins = os.getenv(
        "ALLOWED_ORIGINS", "http://localhost:8000,http://localhost:3000"
    ).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "Authorization", "X-Requested-With", "Accept"],
        expose_headers=["Content-Type"],
    )

    @app.get(
        "/public/elements/MermaidViewer.jsx",
        name="MermaidViewer.jsx",
        tags=["static"],
        summary="Get Mermaid Diagram Source",
    )
    def get_mermaid_source() -> FileResponse:
        """Get the Mermaid diagram source from static assets.

        Returns:
            FileResponse: Mermaid diagram source as a file response.
        """
        mermaid_file_path = Path.cwd() / "public" / "elements" / "MermaidViewer.jsx"
        if not mermaid_file_path.exists():
            mermaid_file_path = (
                Path(__file__).parent / "static" / "elements" / "MermaidViewer.jsx"
            )
        return FileResponse(mermaid_file_path)

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
    mount_chainlit(app, target=str(Path(__file__).parent / "chainlit.py"), path="/")

    return app
