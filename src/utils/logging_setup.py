"""
Logging setup utilities for AI Discovery Workshop Agent.
"""

import os
from logging import WARNING, Logger, getLogger

from azure.monitor.opentelemetry import configure_azure_monitor

_LOG_LEVEL = os.getenv("LOGLEVEL", "INFO").upper()
__main__logger: Logger | None = None
_MAIN_LOGGER_NAME = "ai-discovery-agent"


def setup_logging(name: str) -> Logger:
    """
    Setup logging configuration for the application.

    Parameters:
    -----------
    name : str
        Logger name (usually __name__)
    """
    global __main__logger
    if __main__logger is None:
        if os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY") or os.getenv(
            "APPLICATIONINSIGHTS_CONNECTION_STRING"
        ):
            configure_azure_monitor(logger_name=_MAIN_LOGGER_NAME)
        # This is just to fix the issue https://github.com/Azure/azure-sdk-for-python/issues/33623
        getLogger("azure.monitor.opentelemetry.exporter.export._base").setLevel(WARNING)
        getLogger("azure.core.pipeline.policies.http_logging_policy").setLevel(WARNING)
        logger = getLogger(_MAIN_LOGGER_NAME)
        logger.setLevel(_LOG_LEVEL)
        __main__logger = logger

        if not (
            os.getenv("APPINSIGHTS_INSTRUMENTATIONKEY")
            or os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
        ):
            logger.warning(
                "Application Insights not configured. Running without telemetry."
            )

    child = __main__logger.getChild(name)
    child.setLevel(_LOG_LEVEL)
    return child


def get_logger(name: str) -> Logger:
    """
    Get a logger instance with proper level configuration.

    Parameters:
    -----------
    name : str
        Logger name (usually __name__)

    Returns:
    --------
    Logger instance with configured level
    """
    return setup_logging(name)
