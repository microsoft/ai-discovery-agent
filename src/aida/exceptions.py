# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Custom exception classes for AI Discovery Workshop Agent.

This module defines domain-specific exceptions that provide better error handling
and diagnostics throughout the application.
"""


class AidaBaseException(Exception):
    """Base exception class for all AIDA-specific exceptions."""


class AuthenticationError(AidaBaseException):
    """Raised when authentication fails."""

    def __init__(
        self, message: str = "Authentication failed", username: str | None = None
    ):
        """
        Initialize AuthenticationError.

        Args:
            message: Error message
            username: Username that failed authentication (if applicable)
        """
        self.username = username
        super().__init__(message)


class AuthorizationError(AidaBaseException):
    """Raised when a user is not authorized to perform an action."""

    def __init__(
        self,
        message: str = "User not authorized",
        user_id: str | None = None,
        required_role: str | None = None,
    ):
        """
        Initialize AuthorizationError.

        Args:
            message: Error message
            user_id: User identifier
            required_role: Role required for the action
        """
        self.user_id = user_id
        self.required_role = required_role
        super().__init__(message)


class ConfigurationError(AidaBaseException):
    """Raised when configuration is invalid or missing."""

    def __init__(
        self, message: str = "Configuration error", config_file: str | None = None
    ):
        """
        Initialize ConfigurationError.

        Args:
            message: Error message
            config_file: Path to the configuration file with issues
        """
        self.config_file = config_file
        super().__init__(message)


class AgentError(AidaBaseException):
    """Base exception for agent-related errors."""

    def __init__(self, message: str = "Agent error", agent_key: str | None = None):
        """
        Initialize AgentError.

        Args:
            message: Error message
            agent_key: Agent identifier
        """
        self.agent_key = agent_key
        super().__init__(message)


class AgentNotFoundError(AgentError):
    """Raised when a requested agent is not found."""

    def __init__(self, agent_key: str):
        """
        Initialize AgentNotFoundError.

        Args:
            agent_key: The agent key that was not found
        """
        super().__init__(f"Agent '{agent_key}' not found in registry", agent_key)


class AgentConfigurationError(AgentError):
    """Raised when agent configuration is invalid."""

    def __init__(self, agent_key: str, details: str):
        """
        Initialize AgentConfigurationError.

        Args:
            agent_key: Agent identifier
            details: Details about the configuration issue
        """
        super().__init__(
            f"Invalid configuration for agent '{agent_key}': {details}", agent_key
        )


class StorageError(AidaBaseException):
    """Base exception for storage-related errors."""

    def __init__(
        self,
        message: str = "Storage error",
        user_id: str | None = None,
        conversation_id: str | None = None,
    ):
        """
        Initialize StorageError.

        Args:
            message: Error message
            user_id: User identifier
            conversation_id: Conversation identifier
        """
        self.user_id = user_id
        self.conversation_id = conversation_id
        super().__init__(message)


class ConversationNotFoundError(StorageError):
    """Raised when a requested conversation is not found."""

    def __init__(self, user_id: str, conversation_id: str):
        """
        Initialize ConversationNotFoundError.

        Args:
            user_id: User identifier
            conversation_id: Conversation identifier
        """
        super().__init__(
            f"Conversation '{conversation_id}' not found for user '{user_id}'",
            user_id,
            conversation_id,
        )


class StorageAccessError(StorageError):
    """Raised when storage access fails due to permissions or connectivity."""

    def __init__(
        self,
        message: str,
        user_id: str | None = None,
        conversation_id: str | None = None,
    ):
        """
        Initialize StorageAccessError.

        Args:
            message: Error message
            user_id: User identifier
            conversation_id: Conversation identifier
        """
        super().__init__(message, user_id, conversation_id)


class PromptLoadError(AidaBaseException):
    """Raised when prompt file loading fails."""

    def __init__(self, file_path: str, details: str):
        """
        Initialize PromptLoadError.

        Args:
            file_path: Path to the prompt file
            details: Details about the loading failure
        """
        self.file_path = file_path
        super().__init__(f"Failed to load prompt file '{file_path}': {details}")


class MessageProcessingError(AidaBaseException):
    """Raised when message processing fails."""

    def __init__(
        self,
        message: str = "Message processing failed",
        user_id: str | None = None,
        agent_key: str | None = None,
    ):
        """
        Initialize MessageProcessingError.

        Args:
            message: Error message
            user_id: User identifier
            agent_key: Agent identifier
        """
        self.user_id = user_id
        self.agent_key = agent_key
        super().__init__(message)
