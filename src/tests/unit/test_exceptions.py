# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Unit tests for the exceptions module.

Tests custom exception classes and their attributes.
"""

import pytest

from aida.exceptions import (
    AgentConfigurationError,
    AgentError,
    AgentNotFoundError,
    AidaBaseException,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    ConversationNotFoundError,
    MessageProcessingError,
    PromptLoadError,
    StorageAccessError,
    StorageError,
)


class TestBaseExceptions:
    """Test base exception classes."""

    def test_aida_base_exception(self):
        """Test AidaBaseException creation and inheritance."""
        exc = AidaBaseException("Test error")
        assert str(exc) == "Test error"
        assert isinstance(exc, Exception)

    def test_agent_error(self):
        """Test AgentError base class."""
        exc = AgentError("Test agent error", "test_agent")
        assert str(exc) == "Test agent error"
        assert exc.agent_key == "test_agent"
        assert isinstance(exc, AidaBaseException)

    def test_storage_error(self):
        """Test StorageError base class."""
        exc = StorageError("Test storage error", "user123", "conv456")
        assert str(exc) == "Test storage error"
        assert exc.user_id == "user123"
        assert exc.conversation_id == "conv456"
        assert isinstance(exc, AidaBaseException)


class TestAuthenticationExceptions:
    """Test authentication-related exceptions."""

    def test_authentication_error_with_username(self):
        """Test AuthenticationError with username."""
        exc = AuthenticationError("Login failed", "testuser")
        assert str(exc) == "Login failed"
        assert exc.username == "testuser"

    def test_authentication_error_without_username(self):
        """Test AuthenticationError without username."""
        exc = AuthenticationError("Authentication required")
        assert str(exc) == "Authentication required"
        assert exc.username is None

    def test_authentication_error_default_message(self):
        """Test AuthenticationError with default message."""
        exc = AuthenticationError()
        assert str(exc) == "Authentication failed"
        assert exc.username is None

    def test_authorization_error_with_context(self):
        """Test AuthorizationError with full context."""
        exc = AuthorizationError("Access denied", "user123", "admin")
        assert str(exc) == "Access denied"
        assert exc.user_id == "user123"
        assert exc.required_role == "admin"

    def test_authorization_error_default(self):
        """Test AuthorizationError with defaults."""
        exc = AuthorizationError()
        assert str(exc) == "User not authorized"
        assert exc.user_id is None
        assert exc.required_role is None


class TestConfigurationExceptions:
    """Test configuration-related exceptions."""

    def test_configuration_error_with_file(self):
        """Test ConfigurationError with config file."""
        exc = ConfigurationError("Invalid YAML", "/path/to/config.yaml")
        assert str(exc) == "Invalid YAML"
        assert exc.config_file == "/path/to/config.yaml"

    def test_configuration_error_without_file(self):
        """Test ConfigurationError without config file."""
        exc = ConfigurationError("Missing configuration")
        assert str(exc) == "Missing configuration"
        assert exc.config_file is None

    def test_configuration_error_default(self):
        """Test ConfigurationError with default message."""
        exc = ConfigurationError()
        assert str(exc) == "Configuration error"


class TestAgentExceptions:
    """Test agent-related exceptions."""

    def test_agent_not_found_error(self):
        """Test AgentNotFoundError."""
        exc = AgentNotFoundError("my_agent")
        assert "my_agent" in str(exc)
        assert "not found" in str(exc)
        assert exc.agent_key == "my_agent"
        assert isinstance(exc, AgentError)

    def test_agent_configuration_error(self):
        """Test AgentConfigurationError."""
        exc = AgentConfigurationError("my_agent", "missing persona field")
        assert "my_agent" in str(exc)
        assert "missing persona field" in str(exc)
        assert exc.agent_key == "my_agent"
        assert isinstance(exc, AgentError)


class TestStorageExceptions:
    """Test storage-related exceptions."""

    def test_conversation_not_found_error(self):
        """Test ConversationNotFoundError."""
        exc = ConversationNotFoundError("user123", "conv456")
        assert "conv456" in str(exc)
        assert "user123" in str(exc)
        assert "not found" in str(exc)
        assert exc.user_id == "user123"
        assert exc.conversation_id == "conv456"
        assert isinstance(exc, StorageError)

    def test_storage_access_error_with_context(self):
        """Test StorageAccessError with full context."""
        exc = StorageAccessError(
            "Permission denied", user_id="user123", conversation_id="conv456"
        )
        assert str(exc) == "Permission denied"
        assert exc.user_id == "user123"
        assert exc.conversation_id == "conv456"
        assert isinstance(exc, StorageError)

    def test_storage_access_error_minimal(self):
        """Test StorageAccessError with minimal context."""
        exc = StorageAccessError("Network error")
        assert str(exc) == "Network error"
        assert exc.user_id is None
        assert exc.conversation_id is None


class TestPromptExceptions:
    """Test prompt-related exceptions."""

    def test_prompt_load_error(self):
        """Test PromptLoadError."""
        exc = PromptLoadError("prompts/persona.md", "file not found")
        assert "prompts/persona.md" in str(exc)
        assert "file not found" in str(exc)
        assert exc.file_path == "prompts/persona.md"


class TestMessageExceptions:
    """Test message processing exceptions."""

    def test_message_processing_error_with_context(self):
        """Test MessageProcessingError with full context."""
        exc = MessageProcessingError(
            "Processing failed", user_id="user123", agent_key="facilitator"
        )
        assert str(exc) == "Processing failed"
        assert exc.user_id == "user123"
        assert exc.agent_key == "facilitator"

    def test_message_processing_error_default(self):
        """Test MessageProcessingError with defaults."""
        exc = MessageProcessingError()
        assert str(exc) == "Message processing failed"
        assert exc.user_id is None
        assert exc.agent_key is None


class TestExceptionInheritance:
    """Test exception inheritance hierarchy."""

    def test_all_inherit_from_aida_base(self):
        """Test that all custom exceptions inherit from AidaBaseException."""
        exceptions_to_test = [
            AuthenticationError(),
            AuthorizationError(),
            ConfigurationError(),
            AgentError(),
            AgentNotFoundError("test"),
            AgentConfigurationError("test", "details"),
            StorageError(),
            ConversationNotFoundError("user", "conv"),
            StorageAccessError("error"),
            PromptLoadError("file", "details"),
            MessageProcessingError(),
        ]

        for exc in exceptions_to_test:
            assert isinstance(exc, AidaBaseException)
            assert isinstance(exc, Exception)

    def test_agent_exceptions_inherit_from_agent_error(self):
        """Test that agent exceptions inherit from AgentError."""
        assert isinstance(AgentNotFoundError("test"), AgentError)
        assert isinstance(AgentConfigurationError("test", "details"), AgentError)

    def test_storage_exceptions_inherit_from_storage_error(self):
        """Test that storage exceptions inherit from StorageError."""
        assert isinstance(ConversationNotFoundError("user", "conv"), StorageError)
        assert isinstance(StorageAccessError("error"), StorageError)


class TestExceptionRaising:
    """Test that exceptions can be raised and caught properly."""

    def test_raise_and_catch_authentication_error(self):
        """Test raising and catching AuthenticationError."""
        with pytest.raises(AuthenticationError) as exc_info:
            raise AuthenticationError("Test auth error", "testuser")

        assert exc_info.value.username == "testuser"
        assert "Test auth error" in str(exc_info.value)

    def test_raise_and_catch_agent_not_found(self):
        """Test raising and catching AgentNotFoundError."""
        with pytest.raises(AgentNotFoundError) as exc_info:
            raise AgentNotFoundError("missing_agent")

        assert exc_info.value.agent_key == "missing_agent"

    def test_raise_and_catch_storage_error(self):
        """Test raising and catching ConversationNotFoundError."""
        with pytest.raises(ConversationNotFoundError) as exc_info:
            raise ConversationNotFoundError("user123", "conv456")

        assert exc_info.value.user_id == "user123"
        assert exc_info.value.conversation_id == "conv456"

    def test_catch_by_base_class(self):
        """Test that derived exceptions can be caught by base class."""
        # Test AgentNotFoundError can be caught as AgentError
        with pytest.raises(AgentError):
            raise AgentNotFoundError("test")

        # Test ConversationNotFoundError can be caught as StorageError
        with pytest.raises(StorageError):
            raise ConversationNotFoundError("user", "conv")

        # Test all can be caught as AidaBaseException
        with pytest.raises(AidaBaseException):
            raise AuthenticationError("test")
