"""
Unit tests for the auth module.

Tests authentication functionality including password and OAuth authentication.
"""

import os
from unittest.mock import Mock, mock_open, patch

import pytest
import yaml

from auth import is_oauth_enabled, oauth_callback, password_auth_callback
from tests.fixtures.data import SAMPLE_AUTH_CONFIG


class TestPasswordAuthentication:
    """Test password authentication functionality."""

    @pytest.fixture
    def mock_auth_config_file(self):
        """Mock the auth config file."""
        return yaml.dump(SAMPLE_AUTH_CONFIG)

    @patch("builtins.open", new_callable=mock_open)
    @patch("auth.yaml.load")
    async def test_password_auth_callback_success(self, mock_yaml_load, mock_file):
        """Test successful password authentication."""
        # Arrange
        mock_yaml_load.return_value = SAMPLE_AUTH_CONFIG
        username = "testuser"
        password = "testpass"  # nosec B105

        # Mock bcrypt.checkpw properly - need to mock bcrypt.hashpw instead since that's what's used
        with patch("auth.bcrypt.hashpw") as mock_hashpw:
            # The actual implementation uses hashpw and compares the result
            stored_hash = "$2b$12$sample.hashed.password.for.testing"
            mock_hashpw.return_value = stored_hash.encode("utf-8")

            # Act
            result = await password_auth_callback(username, password)

            # Assert
            assert result is not None
            assert result.identifier == username
            assert result.metadata["email"] == "test@example.com"
            assert result.metadata["first_name"] == "Test"
            assert result.metadata["roles"] == ["user"]

    @patch("builtins.open", new_callable=mock_open)
    @patch("auth.yaml.load")
    async def test_password_auth_callback_invalid_user(self, mock_yaml_load, mock_file):
        """Test authentication with non-existent user."""
        # Arrange
        mock_yaml_load.return_value = SAMPLE_AUTH_CONFIG
        username = "nonexistentuser"
        password = "testpass"  # nosec B105

        # Act
        result = await password_auth_callback(username, password)

        # Assert
        assert result is None

    @patch("builtins.open", new_callable=mock_open)
    @patch("auth.yaml.load")
    async def test_password_auth_callback_wrong_password(
        self, mock_yaml_load, mock_file
    ):
        """Test authentication with wrong password."""
        # Arrange
        mock_yaml_load.return_value = SAMPLE_AUTH_CONFIG
        username = "testuser"
        password = "wrongpass"  # nosec B105

        # Mock bcrypt to simulate password verification failure
        with patch("auth.bcrypt.hashpw") as mock_hashpw:
            # Different hash result means wrong password
            mock_hashpw.return_value = b"different_hash_result"

            # Act
            result = await password_auth_callback(username, password)

            # Assert
            assert result is None

    @patch("builtins.open", side_effect=FileNotFoundError)
    async def test_password_auth_callback_config_not_found(self, mock_file):
        """Test authentication when config file is missing."""
        # Arrange
        username = "testuser"
        password = "testpass"  # nosec B105

        # Act
        result = await password_auth_callback(username, password)

        # Assert
        assert result is None

    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content")
    @patch("auth.yaml.load", side_effect=yaml.YAMLError("Invalid YAML"))
    async def test_password_auth_callback_invalid_yaml(self, mock_yaml_load, mock_file):
        """Test authentication with invalid YAML config."""
        # Arrange
        username = "testuser"
        password = "testpass"  # nosec B105

        # Act
        result = await password_auth_callback(username, password)

        # Assert
        assert result is None


class TestOAuthAuthentication:
    """Test OAuth authentication functionality."""

    async def test_oauth_callback_success(self):
        """Test successful OAuth authentication."""
        # Arrange
        provider_id = "github"
        token = "oauth_token"  # nosec B105
        raw_user_data = {
            "login": "testuser",
            "email": "test@example.com",
            "name": "Test User",
        }
        default_user = Mock()
        default_user.identifier = "testuser"
        default_user.metadata = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "roles": ["user"],
        }

        # Act
        result = await oauth_callback(provider_id, token, raw_user_data, default_user)

        # Assert
        assert result is not None
        assert result.identifier == "testuser"
        assert result.metadata["roles"] == ["user"]

    async def test_oauth_callback_with_none_default_user(self):
        """Test OAuth authentication with None default user."""
        # Arrange
        provider_id = "github"
        token = "oauth_token"  # nosec B105
        raw_user_data = {"login": "testuser"}

        # Create a minimal Mock user to satisfy the type requirement
        default_user = Mock()
        default_user.identifier = None  # Simulate a user with no identifier

        # The implementation tries to log default_user.identifier
        # Act
        result = await oauth_callback(provider_id, token, raw_user_data, default_user)

        # Assert - since identifier is None, we expect the callback to handle it gracefully
        assert result is not None


class TestOAuthEnabled:
    """Test OAuth enabled detection."""

    def test_is_oauth_enabled_github(self):
        """Test OAuth enabled with GitHub client ID."""
        with patch.dict(os.environ, {"OAUTH_GITHUB_CLIENT_ID": "test_client_id"}):
            result = is_oauth_enabled()
            assert result is True

    def test_is_oauth_enabled_google(self):
        """Test OAuth enabled with Google client ID."""
        with patch.dict(os.environ, {"OAUTH_GOOGLE_CLIENT_ID": "test_client_id"}):
            result = is_oauth_enabled()
            assert result is True

    def test_is_oauth_enabled_azure(self):
        """Test OAuth enabled with Azure AD client ID."""
        with patch.dict(os.environ, {"OAUTH_AZURE_AD_CLIENT_ID": "test_client_id"}):
            result = is_oauth_enabled()
            assert result is True

    def test_is_oauth_disabled(self):
        """Test OAuth disabled when no client IDs are set."""
        # Clear all OAuth environment variables
        oauth_vars = [
            "OAUTH_GITHUB_CLIENT_ID",
            "OAUTH_GOOGLE_CLIENT_ID",
            "OAUTH_AZURE_AD_CLIENT_ID",
            "OAUTH_AUTH0_CLIENT_ID",
            "OAUTH_OKTA_CLIENT_ID",
            "OAUTH_KEYCLOAK_CLIENT_ID",
            "OAUTH_COGNITO_CLIENT_ID",
            "OAUTH_DESCOPE_CLIENT_ID",
        ]
        with patch.dict(os.environ, {var: "" for var in oauth_vars}, clear=True):
            result = is_oauth_enabled()
            assert result is False

    def test_is_oauth_enabled_multiple_providers(self):
        """Test OAuth enabled with multiple providers configured."""
        with patch.dict(
            os.environ,
            {
                "OAUTH_GITHUB_CLIENT_ID": "github_client_id",
                "OAUTH_GOOGLE_CLIENT_ID": "google_client_id",
            },
        ):
            result = is_oauth_enabled()
            assert result is True
