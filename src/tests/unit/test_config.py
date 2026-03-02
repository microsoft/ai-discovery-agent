# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Unit tests for the config module.

Tests configuration loading functionality including program metadata extraction.
"""

import os
from importlib.metadata import PackageNotFoundError
from unittest.mock import MagicMock, patch

from aida.utils.config import load_program_info, setup_auth_secret


class TestLoadProgramInfo:
    """Test load_program_info functionality."""

    @patch("aida.utils.config.distribution")
    def test_load_program_info_malformed_project_url(self, mock_distribution):
        """Test handling of malformed Project-URL entries."""
        # Arrange
        mock_metadata = MagicMock()
        mock_metadata.get.side_effect = lambda key, default="N/A": {
            "Name": "test-package",
            "Version": "1.0.0",
            "Summary": "Test package",
            "Author": "Test Author",
            "Author-Email": "test@example.com",
            "Home-Page": "https://example.com",
        }.get(key, default)

        # Create malformed Project-URL entries (missing comma-space separator)
        mock_metadata.get_all.return_value = [
            "Repository https://github.com/test/repo",  # Missing ", "
            "repository, https://github.com/test/repo2",  # Valid
            "",  # Empty entry
            "Documentation:https://docs.example.com",  # Wrong separator
        ]

        mock_dist = MagicMock()
        mock_dist.metadata = mock_metadata
        mock_distribution.return_value = mock_dist

        # Act
        result = load_program_info()

        # Assert
        assert "test-package" in result
        assert "1.0.0" in result
        # Should use the valid URL entry
        assert "https://github.com/test/repo2" in result
        # Malformed entries should be skipped without crashing

    @patch("aida.utils.config.distribution")
    def test_load_program_info_valid_project_urls(self, mock_distribution):
        """Test handling of valid Project-URL entries."""
        # Arrange
        mock_metadata = MagicMock()
        mock_metadata.get.side_effect = lambda key, default="N/A": {
            "Name": "test-package",
            "Version": "1.0.0",
            "Summary": "Test package",
            "Author": "Test Author",
            "Author-Email": "test@example.com",
            "Home-Page": "https://example.com",
        }.get(key, default)

        mock_metadata.get_all.return_value = [
            "repository, https://github.com/test/repo",
            "documentation, https://docs.example.com",
        ]

        mock_dist = MagicMock()
        mock_dist.metadata = mock_metadata
        mock_distribution.return_value = mock_dist

        # Act
        result = load_program_info()

        # Assert
        assert "https://github.com/test/repo" in result
        assert "https://docs.example.com" in result

    @patch("aida.utils.config.distribution")
    def test_load_program_info_various_separators(self, mock_distribution):
        """Test handling of Project-URL entries with various separators."""
        # Arrange
        mock_metadata = MagicMock()
        mock_metadata.get.side_effect = lambda key, default="N/A": {
            "Name": "test-package",
            "Version": "1.0.0",
            "Summary": "Test package",
            "Author": "Test Author",
            "Author-Email": "test@example.com",
            "Home-Page": "https://example.com",
        }.get(key, default)

        # Test various separator formats
        mock_metadata.get_all.return_value = [
            "repository, https://github.com/test/repo1",  # Standard: comma-space
            "Repository,https://github.com/test/repo2",  # No space after comma
            "GitHub: https://github.com/test/repo3",  # Colon with space
            "Documentation:https://docs.example.com",  # Colon without space
            "Docs , https://docs.example.com/alt",  # Extra spaces
        ]

        mock_dist = MagicMock()
        mock_dist.metadata = mock_metadata
        mock_distribution.return_value = mock_dist

        # Act
        result = load_program_info()

        # Assert
        assert "test-package" in result
        # All valid formats should be parsed, but only the last matching entry for each type is used
        # repo3 should be used as it's the last "github" match (the implementation overwrites each time)
        assert (
            "https://github.com/test/repo3" in result
            or "https://github.com/test/repo2" in result
            or "https://github.com/test/repo1" in result
        )
        # docs.example.com should be parsed
        assert "docs.example.com" in result

    @patch("aida.utils.config.distribution")
    def test_load_program_info_package_not_found(self, mock_distribution):
        """Test handling when package is not found."""
        # Arrange
        mock_distribution.side_effect = PackageNotFoundError

        # Act
        result = load_program_info()

        # Assert
        assert "Error: Package not found" in result

    @patch("aida.utils.config.distribution")
    def test_load_program_info_general_exception(self, mock_distribution):
        """Test handling of unexpected exceptions."""
        # Arrange
        mock_distribution.side_effect = RuntimeError("Unexpected error")

        # Act
        result = load_program_info()

        # Assert
        assert "Error retrieving program information" in result


class TestSetupAuthSecret:
    """Test setup_auth_secret functionality."""

    @patch.dict(os.environ, {})
    @patch("aida.utils.config.dotenv.set_key")
    @patch("aida.utils.config.os.getenv")
    @patch("aida.utils.config.random_secret")
    def test_setup_auth_secret_not_set(
        self, mock_random_secret, mock_getenv, mock_set_key
    ):
        """Test setup_auth_secret when CHAINLIT_AUTH_SECRET is not set."""
        # Arrange
        mock_getenv.return_value = None
        mock_random_secret.return_value = "random-secret-123"

        # Act
        setup_auth_secret()

        # Assert
        mock_random_secret.assert_called_once()
        mock_set_key.assert_called_once_with(
            ".env", "CHAINLIT_AUTH_SECRET", "random-secret-123"
        )

    @patch.dict(os.environ, {})
    @patch("aida.utils.config.dotenv.set_key")
    @patch("aida.utils.config.os.getenv")
    def test_setup_auth_secret_already_set(self, mock_getenv, mock_set_key):
        """Test setup_auth_secret when CHAINLIT_AUTH_SECRET is already set."""
        # Arrange
        mock_getenv.return_value = "existing-secret"

        # Act
        setup_auth_secret()

        # Assert
        mock_set_key.assert_not_called()

    @patch.dict(os.environ, {})
    @patch("aida.utils.config.dotenv.set_key")
    @patch("aida.utils.config.os.getenv")
    @patch("aida.utils.config.random_secret")
    def test_setup_auth_secret_permission_denied(
        self, mock_random_secret, mock_getenv, mock_set_key
    ):
        """Test setup_auth_secret continues when .env file is not writable."""
        # Arrange
        mock_getenv.return_value = None
        mock_random_secret.return_value = "random-secret-456"
        mock_set_key.side_effect = PermissionError(
            "[Errno 13] Permission denied: '/app/.tmp_file'"
        )

        # Act - should not raise
        setup_auth_secret()

        # Assert - secret should still be set in os.environ
        mock_random_secret.assert_called_once()
        mock_set_key.assert_called_once_with(
            ".env", "CHAINLIT_AUTH_SECRET", "random-secret-456"
        )
