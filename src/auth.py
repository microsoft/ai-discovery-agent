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

import chainlit as cl
import yaml
from yaml.loader import SafeLoader

from utils.logging_setup import get_logger

AUTH_CONFIG_FILE = Path(__file__).parent / "config/auth-config.yaml"

logger = get_logger(__name__)


def _hash_password(password: str, salt: bytes | None = None) -> str:
    """
    Hash a password using PBKDF2 with SHA-256.

    Parameters:
    -----------
    password : str
        The plain text password to hash
    salt : bytes | None
        Optional salt bytes. If None, a new random salt is generated

    Returns:
    --------
    str
        Base64 encoded string containing salt and hash, separated by '$'
    """
    if salt is None:
        salt = secrets.token_bytes(32)  # 32 bytes = 256 bits of salt

    # Use PBKDF2 with SHA-256, 100,000 iterations (recommended by OWASP)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, 100000
    )

    # Encode salt and hash as base64 and combine with separator
    salt_b64 = base64.b64encode(salt).decode("ascii")
    hash_b64 = base64.b64encode(password_hash).decode("ascii")

    return f"pbkdf2_sha256${salt_b64}${hash_b64}"


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
            # New PBKDF2 format: pbkdf2_sha256$salt_b64$hash_b64
            parts = hashed_password.split("$")
            if len(parts) != 3:
                return False

            salt = base64.b64decode(parts[1])
            expected_hash = base64.b64decode(parts[2])

            # Hash the provided password with the same salt
            password_hash = hashlib.pbkdf2_hmac(
                "sha256", password.encode("utf-8"), salt, 100000
            )

            # Use secrets.compare_digest for timing attack resistance
            return secrets.compare_digest(password_hash, expected_hash)

        elif hashed_password.startswith("$2b$"):
            # Legacy bcrypt format - for backward compatibility
            # In production, you should migrate all passwords to the new format
            logger.warning(
                "Legacy bcrypt password detected. Consider migrating to PBKDF2."
            )
            # For now, fall back to plain text comparison (not secure, but maintains compatibility)
            return False

        else:
            # Plain text password (legacy, insecure)
            return secrets.compare_digest(password, hashed_password)

    except Exception as e:
        logger.error(f"Password verification error: {e}")
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
    try:
        with open(AUTH_CONFIG_FILE, encoding="utf-8") as file:
            config = yaml.load(file, Loader=SafeLoader)

        credentials = config.get("credentials", {}).get("usernames", {})

        if username in credentials:
            user_data = credentials[username]
            stored_password = user_data.get("password", "")

            # Use the new password verification function
            if _verify_password(password, stored_password):
                # If this was a plain text password, upgrade it to hashed
                if not stored_password.startswith(("pbkdf2_sha256$", "$2b$")):
                    logger.warning(
                        f"Upgrading plain text password for user '{username}' to PBKDF2 hash."
                    )
                    try:
                        hashed_password = _hash_password(password)
                        user_data["password"] = hashed_password
                        config["credentials"]["usernames"][username] = user_data

                        with open(AUTH_CONFIG_FILE, "w", encoding="utf-8") as file:
                            yaml.dump(config, file)
                        logger.info(
                            f"Password for user '{username}' successfully upgraded to PBKDF2 hash."
                        )
                    except Exception as e:
                        logger.error(
                            f"Failed to upgrade password for user '{username}': {e}"
                        )

                return cl.User(
                    identifier=username,
                    metadata={
                        "first_name": user_data.get("first_name", ""),
                        "last_name": user_data.get("last_name", ""),
                        "email": user_data.get("email", ""),
                        "roles": user_data.get("roles", ["user"]),
                    },
                )
            else:
                logger.warning(
                    f"Authentication failed for user '{username}': Incorrect password."
                )
                return None
    except Exception as e:
        logger.error(f"Authentication error: {e}", exc_info=e, stack_info=True)

    return None


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
    # You can add custom logic here based on provider_id
    # For example, domain restrictions or role mapping
    logger.info(
        f"OAuth login successful for user {default_user.identifier} via {provider_id}"
    )
    return default_user


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
