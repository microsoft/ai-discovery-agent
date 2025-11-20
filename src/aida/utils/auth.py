# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Authentication module for AI Discovery Workshop Agent.

Handles both password-based and OAuth authentication for Chainlit application.
"""

import base64
import hashlib
import os
import secrets
from pathlib import Path
from typing import Final

import chainlit as cl
import yaml
from yaml.loader import SafeLoader

from aida.exceptions import AuthenticationError, ConfigurationError
from aida.utils.logging_setup import get_logger, get_structured_logger

AUTH_CONFIG_FILE = Path.cwd() / "config/auth-config.yaml"

logger = get_logger(__name__)

SALT_SIZE: Final[int] = 32  # 32 bytes = 256 bits
PBKDF2_ITERATIONS: Final[int] = 100000


def _hash_password(password: str) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.

    Parameters:
    -----------
    password : str
        The plain text password to hash

    Returns:
    --------
    str
        Base64 encoded string containing salt and hash, separated by '$'
    """
    salt = os.urandom(SALT_SIZE)  # 32 bytes = 256 bits of salt

    # Use PBKDF2 with SHA-256, 100,000 iterations (recommended by OWASP)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )

    # Encode salt and hash as base64 and combine with separator
    b64 = base64.b64encode(salt + password_hash).decode("ascii")

    return f"pbkdf2_sha256${b64}"


def _verify_password(password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Parameters:
    -----------
    password : str
        The plain text password to verify
    hashed_password : str
        The stored hash to verify against

    Returns:
    --------
    bool
        True if password matches, False otherwise
    """
    try:
        # Handle both new PBKDF2 format and legacy bcrypt format
        if hashed_password.startswith("pbkdf2_sha256$"):
            # New PBKDF2 format: pbkdf2_sha256$salt+hash_b64
            parts = hashed_password.split("$")
            if len(parts) != 2:
                logger.warning("Invalid PBKDF2 hash format: incorrect number of parts")
                return False

            try:
                salt_and_pass = base64.b64decode(parts[1])
            except (ValueError, TypeError) as e:
                logger.error(f"Failed to decode PBKDF2 hash: {e}")
                return False

            salt = salt_and_pass[:SALT_SIZE]
            expected_hash = salt_and_pass[SALT_SIZE:]

            # Hash the provided password with the same salt
            password_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
            )

            # Use secrets.compare_digest for timing attack resistance
            return secrets.compare_digest(password_hash, expected_hash)

        elif hashed_password.startswith("$2b$"):
            # Legacy bcrypt format - for backward compatibility
            # In production, you should migrate all passwords to the new format
            logger.warning(
                "Legacy bcrypt password detected. Consider migrating to PBKDF2."
            )
            return False
        else:
            # Plain text password (legacy, insecure)
            logger.warning("Plain text password comparison detected - insecure!")
            return secrets.compare_digest(password, hashed_password)

    except (ValueError, TypeError) as e:
        logger.error(f"Password verification error: {e}", exc_info=True)
        return False
    except Exception as e:
        logger.error(
            f"Unexpected error during password verification: {e}", exc_info=True
        )
        return False


async def password_auth_callback(username: str, password: str) -> cl.User | None:
    """
    Authenticate user using credentials from auth-config.yaml.

    Parameters:
    -----------
    username : str
        The username provided by the user
    password : str
        The password provided by the user

    Returns:
    --------
    Optional[cl.User]
        Authenticated user object if successful, None otherwise
    """
    # Create structured logger with username context
    auth_logger = get_structured_logger(__name__, user_id=username)

    try:
        if not AUTH_CONFIG_FILE.exists():
            logger.error(
                f"Authentication configuration file not found: {AUTH_CONFIG_FILE}"
            )
            raise ConfigurationError(
                "Authentication configuration missing", str(AUTH_CONFIG_FILE)
            )

        try:
            with open(AUTH_CONFIG_FILE, encoding="utf-8") as file:
                config = yaml.load(file, Loader=SafeLoader)
        except yaml.YAMLError as e:
            logger.error(
                f"Invalid YAML in authentication config file: {e}", exc_info=True
            )
            raise ConfigurationError(
                f"Invalid authentication configuration: {e}", str(AUTH_CONFIG_FILE)
            ) from e
        except OSError as e:
            logger.error(
                f"Failed to read authentication config file: {e}", exc_info=True
            )
            raise ConfigurationError(
                f"Cannot read authentication configuration: {e}", str(AUTH_CONFIG_FILE)
            ) from e

        credentials = config.get("credentials", {}).get("usernames", {})

        if username not in credentials:
            auth_logger.warning("Authentication failed: user not found")
            raise AuthenticationError(
                "Invalid username or password", username
            ) from None

        user_data = credentials[username]
        stored_password = user_data.get("password", "")

        # Use the new password verification function
        if not _verify_password(password, stored_password):
            auth_logger.warning("Authentication failed: incorrect password")
            raise AuthenticationError(
                "Invalid username or password", username
            ) from None

        # If this was a plain text password, upgrade it to hashed
        if not stored_password.startswith(("pbkdf2_sha256$", "$2b$")):
            auth_logger.warning(
                "Upgrading plain text password to PBKDF2 hash for security"
            )
            try:
                hashed_password = _hash_password(password)
                user_data["password"] = hashed_password
                config["credentials"]["usernames"][username] = user_data

                with open(AUTH_CONFIG_FILE, "w", encoding="utf-8") as file:
                    yaml.dump(config, file)
                auth_logger.info("Password successfully upgraded to PBKDF2 hash")
            except OSError as e:
                auth_logger.error(f"Failed to upgrade password to hash: {e}")
                # Continue with authentication despite upgrade failure
            except Exception as e:
                auth_logger.error(
                    f"Unexpected error during password upgrade: {e}", exc_info=True
                )
                # Continue with authentication despite upgrade failure

        auth_logger.info("Authentication successful")
        return cl.User(
            identifier=username,
            metadata={
                "first_name": user_data.get("first_name", ""),
                "last_name": user_data.get("last_name", ""),
                "email": user_data.get("email", ""),
                "roles": user_data.get("roles", ["user"]),
            },
        )

    except (AuthenticationError, ConfigurationError):
        # Re-raise our custom exceptions
        raise
    except Exception as e:
        logger.error(
            f"Unexpected authentication error for user '{username}': {e}",
            exc_info=True,
        )
        raise AuthenticationError(f"Authentication system error: {e}", username) from e



async def oauth_callback(
    provider_id: str,
    token: str,
    raw_user_data: dict[str, str],
    default_user: cl.User,
    id_token: str | None = None,
) -> cl.User | None:
    """
    Handle OAuth callback after successful authentication.

    This callback is invoked when a user successfully authenticates via an OAuth provider.
    It allows for custom logic to be implemented based on the provider used.

    Args:
        provider_id (str): The identifier of the OAuth provider (e.g., 'google', 'github').
        token (str): The access token returned by the OAuth provider.
        raw_user_data (Dict[str, str]): Raw user data returned by the OAuth provider.
        default_user (cl.User): The default Chainlit user object created from OAuth data.
        id_token (Optional[str]): The ID token if provided by the OAuth provider. Defaults to None.

    Returns:
        Optional[cl.User]: The Chainlit user object to use for the session, or None to reject the login.
            Returning the default_user allows the login, while None denies access.

    Note:
        This method can be extended to implement custom authorization logic such as:
        - Domain restrictions based on email
        - Role mapping from OAuth provider claims
        - Additional user data enrichment
    """
    # Create structured logger with OAuth context
    oauth_logger = get_structured_logger(__name__, user_id=default_user.identifier)

    try:
        oauth_logger.info(
            f"OAuth authentication successful via provider: {provider_id}"
        )
        # You can add custom logic here based on provider_id
        # For example, domain restrictions or role mapping
        return default_user
    except Exception as e:
        logger.error(
            f"Error in OAuth callback for user {default_user.identifier} via {provider_id}: {e}",
            exc_info=True,
        )
        raise AuthenticationError(
            f"OAuth authentication failed: {e}", default_user.identifier
        ) from e


def is_oauth_enabled() -> bool:
    """
    Check if OAuth authentication is enabled based on environment variables.

    Returns:
    --------
    bool
        True if any OAuth provider is configured, False otherwise
    """
    return any(
        [
            os.getenv("OAUTH_GITHUB_CLIENT_ID"),
            os.getenv("OAUTH_GOOGLE_CLIENT_ID"),
            os.getenv("OAUTH_AZURE_AD_CLIENT_ID"),
            os.getenv("OAUTH_AUTH0_CLIENT_ID"),
            os.getenv("OAUTH_OKTA_CLIENT_ID"),
            os.getenv("OAUTH_KEYCLOAK_CLIENT_ID"),
            os.getenv("OAUTH_COGNITO_CLIENT_ID"),
            os.getenv("OAUTH_DESCOPE_CLIENT_ID"),
            # To extend OAuth provider support, add the corresponding environment variable for the provider's client ID.
            # For a complete list of supported providers and configuration instructions, see:
            # https://docs.chainlit.io/docs/authentication/oauth
        ]
    )
