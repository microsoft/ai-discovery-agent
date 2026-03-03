# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Logging setup utilities for AI Discovery Workshop Agent.

Provides structured logging capabilities with context enrichment for better debugging
and monitoring.
"""

import os
from logging import WARNING, Logger, LoggerAdapter, getLogger
from typing import Any

from azure.monitor.opentelemetry import configure_azure_monitor

_LOG_LEVEL = os.getenv("LOGLEVEL", "INFO").upper()
__main__logger: Logger | None = None
_MAIN_LOGGER_NAME = "ai-discovery-agent"


class StructuredLoggerAdapter(LoggerAdapter):
    """
    Logger adapter that adds structured context to log messages.

    This adapter enriches log messages with contextual information such as
    user_id, session_id, agent_key, and conversation_id for better traceability.
    """

    def process(self, msg: str, kwargs: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        """
        Process log message to add context.

        Merges per-call ``extra`` kwargs with the adapter-level ``self.extra``
        so that callers can supply additional context (e.g.
        ``logger.debug("msg", extra={"conversation_id": cid})``) without it
        being silently dropped.  Per-call values take precedence over
        adapter-level values.

        Args:
            msg: Log message
            kwargs: Additional keyword arguments

        Returns:
            Tuple of processed message and kwargs
        """
        # Merge adapter-level extra with any per-call extra (per-call takes precedence)
        merged_extra = {**(self.extra or {}), **kwargs.get("extra", {})}
        kwargs["extra"] = merged_extra

        # Build context string from merged extra data
        context_parts = []
        for key in ["user_id", "session_id", "agent_key", "conversation_id"]:
            if key in merged_extra and merged_extra[key]:
                context_parts.append(f"{key}={merged_extra[key]}")

        if context_parts:
            context_str = " | ".join(context_parts)
            msg = f"[{context_str}] {msg}"

        # Propagate merged extra so downstream handlers also see it
        kwargs["extra"] = merged_extra
        return msg, kwargs


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


def get_structured_logger(
    name: str,
    user_id: str | None = None,
    session_id: str | None = None,
    agent_key: str | None = None,
    conversation_id: str | None = None,
) -> StructuredLoggerAdapter:
    """
    Get a logger adapter with structured context.

    Parameters:
    -----------
    name : str
        Logger name (usually __name__)
    user_id : str, optional
        User identifier for context
    session_id : str, optional
        Session identifier for context
    agent_key : str, optional
        Agent key for context
    conversation_id : str, optional
        Conversation identifier for context

    Returns:
    --------
    StructuredLoggerAdapter
        Logger adapter with context information
    """
    logger = setup_logging(name)
    extra = {}
    if user_id:
        extra["user_id"] = user_id
    if session_id:
        extra["session_id"] = session_id
    if agent_key:
        extra["agent_key"] = agent_key
    if conversation_id:
        extra["conversation_id"] = conversation_id

    return StructuredLoggerAdapter(logger, extra)
