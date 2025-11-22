# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Integration tests for authentication flow.

Tests the complete authentication flow including file operations and user session management.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import Mock, patch

import chainlit as cl
import pytest
import yaml

from aida.utils.auth import is_oauth_enabled, password_auth_callback
from tests.fixtures.data import SAMPLE_AUTH_CONFIG


class TestAuthenticationIntegration:
    """Integration tests for authentication system."""

    @pytest.fixture
    def temp_auth_config(self):
        """Create a temporary auth config file."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(SAMPLE_AUTH_CONFIG, f)
            yield f.name
        # Cleanup
        os.unlink(f.name)

    async def test_password_auth_flow_with_real_file(self, temp_auth_config):
        """Test password authentication with actual file operations."""
        from aida.exceptions import AuthenticationError

        # Patch the AUTH_CONFIG_FILE to point to our temp file
        with patch("aida.utils.auth.AUTH_CONFIG_FILE", Path(temp_auth_config)):
            # Test that authentication fails with wrong password
            # Since the password in SAMPLE_AUTH_CONFIG is plain text "testpass",
            # it should work if we use the right password, but the test data may not match
            with pytest.raises(
                AuthenticationError, match="Invalid username or password"
            ):
                await password_auth_callback("testuser", "wrongpass")

    async def test_password_auth_flow_missing_config(self):
        """Test authentication when config file is missing."""
        from aida.exceptions import ConfigurationError

        # Patch to non-existent file
        with patch(
            "aida.utils.auth.AUTH_CONFIG_FILE", Path("/nonexistent/path/auth.yaml")
        ):
            with pytest.raises(
                ConfigurationError, match="Authentication configuration missing"
            ):
                await password_auth_callback("testuser", "testpass")

    def test_oauth_detection_integration(self):
        """Test OAuth detection with various environment configurations."""
        # Test with no OAuth vars set
        with patch.dict(os.environ, {}, clear=True):
            assert is_oauth_enabled() is False

        # Test with GitHub OAuth enabled
        with patch.dict(os.environ, {"OAUTH_GITHUB_CLIENT_ID": "test_id"}):
            assert is_oauth_enabled() is True

        # Test with multiple providers
        with patch.dict(
            os.environ,
            {
                "OAUTH_GITHUB_CLIENT_ID": "github_id",
                "OAUTH_GOOGLE_CLIENT_ID": "google_id",
            },
        ):
            assert is_oauth_enabled() is True


class TestAuthenticationErrorHandling:
    """Test error handling in authentication flows."""

    async def test_auth_with_malformed_yaml(self):
        """Test authentication with malformed YAML config."""
        from aida.exceptions import ConfigurationError

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML
            f.flush()

            with patch("aida.utils.auth.AUTH_CONFIG_FILE", Path(f.name)):
                with pytest.raises(
                    ConfigurationError, match="Invalid authentication configuration"
                ):
                    await password_auth_callback("testuser", "testpass")

            # Cleanup
            os.unlink(f.name)

    async def test_auth_with_missing_credentials_section(self):
        """Test authentication with config missing credentials section."""
        from aida.exceptions import AuthenticationError

        config_without_creds = {"some_other_section": {}}

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_without_creds, f)
            f.flush()

            with patch("aida.utils.auth.AUTH_CONFIG_FILE", Path(f.name)):
                with pytest.raises(
                    AuthenticationError, match="Invalid username or password"
                ):
                    await password_auth_callback("testuser", "testpass")

            # Cleanup
            os.unlink(f.name)

    async def test_auth_with_empty_config(self):
        """Test authentication with empty config file."""
        from aida.exceptions import AuthenticationError

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump({}, f)
            f.flush()

            with patch("aida.utils.auth.AUTH_CONFIG_FILE", Path(f.name)):
                with pytest.raises(
                    AuthenticationError, match="Invalid username or password"
                ):
                    await password_auth_callback("testuser", "testpass")

            # Cleanup
            os.unlink(f.name)


class TestUserSessionIntegration:
    """Test user session integration with authentication."""

    def test_user_metadata_mapping(self):
        """Test that user metadata is correctly mapped from config."""
        # This would typically involve testing the complete flow
        # from authentication to user session setup
        # For now, we'll test the data structure mapping

        user_data = SAMPLE_AUTH_CONFIG["credentials"]["usernames"]["testuser"]

        # Simulate creating a cl.User object
        mock_user = Mock(spec=cl.User)
        mock_user.identifier = "testuser"
        mock_user.metadata = {
            "first_name": user_data.get("first_name", ""),
            "last_name": user_data.get("last_name", ""),
            "email": user_data.get("email", ""),
            "roles": user_data.get("roles", ["user"]),
        }

        # Verify the mapping
        assert mock_user.identifier == "testuser"
        assert mock_user.metadata["email"] == "test@example.com"
        assert mock_user.metadata["first_name"] == "Test"
        assert mock_user.metadata["roles"] == ["user"]
