# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Unit tests for utils modules.

Tests configuration loading, logging setup, and other utility functions.
"""

import os
from unittest.mock import mock_open, patch

import pytest

from aida.utils.config import load_program_info, setup_auth_secret
from aida.utils.logging_setup import _MAIN_LOGGER_NAME, get_logger, setup_logging
from aida.utils.mermaid import extract_mermaid


class TestConfigModule:
    """Test configuration module functionality."""

    def test_setup_auth_secret_already_set(self):
        """Test setup_auth_secret when secret is already configured."""
        with patch.dict(os.environ, {"CHAINLIT_AUTH_SECRET": "existing_secret"}):
            with patch("aida.utils.config.dotenv.set_key") as mock_set_key:
                setup_auth_secret()

                # Should not call set_key if secret already exists
                mock_set_key.assert_not_called()

    @patch("aida.utils.config.random_secret")
    @patch("aida.utils.config.dotenv.set_key")
    def test_setup_auth_secret_not_set(self, mock_set_key, mock_random_secret):
        """Test setup_auth_secret when no secret is configured."""
        # Arrange
        mock_random_secret.return_value = "generated_secret"

        # Clear the environment variable
        with patch.dict(os.environ, {}, clear=True):
            # Act
            setup_auth_secret()

            # Assert
            assert os.environ["CHAINLIT_AUTH_SECRET"] == "generated_secret"
            mock_set_key.assert_called_once_with(
                ".env", "CHAINLIT_AUTH_SECRET", "generated_secret"
            )

    @patch("builtins.open", new_callable=mock_open)
    @patch("aida.utils.config.tomllib.load")
    def test_load_program_info_success(self, mock_tomllib_load, mock_file):
        """Test successful program info loading."""
        # Arrange
        expected_project_info = {
            "name": "ai-discovery-agent",
            "version": "0.5.0",
            "description": "AI Discovery Agent",
            "authors": [{"name": "jmservera"}],
            "urls": {
                "homepage": "https://github.com/jmservera/ai-discovery-agent",
                "repository": "https://github.com/jmservera/ai-discovery-agent",
                "documentation": "https://github.com/jmservera/ai-discovery-agent/blob/main/README.md",
            },
        }
        mock_tomllib_load.return_value = {"project": expected_project_info}

        # Act
        result = load_program_info()

        # Assert
        # The function returns a formatted string, not the dict
        assert "ai-discovery-agent version 0.5.0" in result
        assert "AI Discovery Agent" in result
        assert "jmservera" in result
        mock_tomllib_load.assert_called_once()

    @patch("builtins.open", side_effect=FileNotFoundError)
    def test_load_program_info_file_not_found(self, mock_file):
        """Test program info loading when file is missing."""
        # Act
        result = load_program_info()

        # Assert
        assert result == "Error retrieving program information."

    @patch("builtins.open", new_callable=mock_open)
    @patch("aida.utils.config.tomllib.load", side_effect=Exception("Parse error"))
    def test_load_program_info_parse_error(self, mock_tomllib_load, mock_file):
        """Test program info loading with parsing error."""
        # Act
        result = load_program_info()

        # Assert
        assert result == "Error retrieving program information."


class TestLoggingModule:
    """Test logging setup module functionality."""

    def test_get_logger_returns_logger(self):
        """Test that get_logger returns a Logger instance."""
        # Act
        logger = get_logger("test_module")

        # Assert
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")

    def test_get_logger_uses_correct_name(self):
        """Test that get_logger uses the provided name."""
        # Act
        logger = get_logger("test_module")

        # Assert
        assert logger.name == f"{_MAIN_LOGGER_NAME}.test_module"

    def test_get_logger_respects_env_log_level(self):
        """Test that get_logger respects LOGLEVEL environment variable."""
        # Since _LOG_LEVEL is set at import time, we need to test differently
        # We'll patch the _LOG_LEVEL directly
        with patch("aida.utils.logging_setup._LOG_LEVEL", "DEBUG"):
            # Act
            logger = get_logger("test_module")

            # Assert
            # In DEBUG level, the logger should be set to 10 (DEBUG level)
            assert logger.level == 10

    @patch.dict(os.environ, {}, clear=True)
    def test_get_logger_default_log_level(self):
        """Test that get_logger uses INFO as default log level."""
        # Act
        logger = get_logger("test_module")

        # Assert
        # INFO level is 20
        assert logger.level == 20

    def test_setup_logging_returns_logger(self):
        """Test that setup_logging returns a Logger instance."""
        # Act
        logger = setup_logging("test_module")

        # Assert
        assert hasattr(logger, "info")
        assert hasattr(logger, "error")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")

    def test_setup_logging_uses_correct_name(self):
        """Test that setup_logging uses the provided name."""
        # Act
        logger = setup_logging("test_module")

        # Assert
        assert logger.name == f"{_MAIN_LOGGER_NAME}.test_module"

    def test_setup_logging_respects_env_log_level(self):
        """Test that setup_logging respects LOGLEVEL environment variable."""
        # Since _LOG_LEVEL is set at import time, we need to test differently
        # We'll patch the _LOG_LEVEL directly
        with patch("aida.utils.logging_setup._LOG_LEVEL", "WARNING"):
            # Act
            logger = setup_logging("test_module")

            # Assert
            # WARNING level is 30
            assert logger.level == 30


class TestMermaidModule:
    """Test mermaid diagram extraction functionality."""

    def test_extract_mermaid_with_valid_diagram(self):
        """Test extracting valid mermaid diagram from text."""
        text = """
        Here is some explanation.

        ```mermaid
        graph TD
            A-->B
        ```
        More details follow.
        """
        diagrams = extract_mermaid(text)
        assert isinstance(diagrams, list)
        assert len(diagrams) == 1
        assert "graph TD" in diagrams[0]

    def test_extract_mermaid_no_diagram(self):
        """Test extracting mermaid diagram when none exists."""
        text = "There is no diagram in this text."
        diagrams = extract_mermaid(text)
        assert isinstance(diagrams, list)
        assert len(diagrams) == 0

    def test_extract_mermaid_malformed_diagram(self):
        """Test extracting malformed mermaid diagram."""
        text = """
        ```mermaid
        graph TD
            A--B
        """
        diagrams = extract_mermaid(text)
        assert isinstance(diagrams, list)
        # Should still detect one diagram block even if malformed
        assert len(diagrams) == 1
        assert "graph TD" in diagrams[0]


# Note: Tests for cached_llm.py would require mocking LangChain components
# and would be more complex due to the Azure OpenAI integration.
# We can add those tests in a separate file or extend this one later.


# Placeholder for tests for cached_llm.py
@pytest.mark.skip(
    reason="Tests for cached_llm.py require mocking LangChain components and Azure OpenAI, which is not set up yet."
)
class TestCachedLLMModule:
    def test_stub(self):
        """Placeholder stub test for cached_llm.py."""
        pass
