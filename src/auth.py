"""
Authentication module for AI Discovery Workshop Agent.

Handles both password-based and OAuth authentication for Chainlit application.
"""

import os
from pathlib import Path

import bcrypt
import chainlit as cl
import yaml
from yaml.loader import SafeLoader

from utils.logging_setup import get_logger

AUTH_CONFIG_FILE = Path(__file__).parent / "config/auth-config.yaml"

logger = get_logger(__name__)


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

            # Handle both bcrypt hashed passwords and plain text for demo
            if stored_password.startswith("$2b$"):
                # Bcrypt hashed password
                if bcrypt.hashpw(
                    password.encode("utf-8"), stored_password.encode("utf-8")
                ) == stored_password.encode("utf-8"):
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
            else:
                # For demo purposes, allow simple password check
                # In production, use only bcrypt

                # review all passwords in the config file and hash them
                modified = False
                for user, user_data in credentials.items():
                    stored_password = user_data.get("password", "")
                    if not stored_password.startswith("$2b$"):
                        # If the password is not hashed, hash it
                        logger.warning(
                            f"Password for user '{user}' is not hashed. Hashing now."
                        )
                        # Hash the password if it's not already hashed
                        hashed_password = bcrypt.hashpw(
                            stored_password.encode("utf-8"),
                            bcrypt.gensalt(),
                        ).decode("utf-8")
                        user_data["password"] = hashed_password
                        config["credentials"]["usernames"][user] = user_data
                        modified = True
                    else:
                        logger.info(
                            f"Password for user '{user}' is already hashed. Skipping."
                        )
                if modified:
                    with open(AUTH_CONFIG_FILE, "w", encoding="utf-8") as file:
                        yaml.dump(config, file)

                if password == stored_password:
                    return cl.User(
                        identifier=username,
                        metadata={
                            "first_name": user_data.get("first_name", ""),
                            "last_name": user_data.get("last_name", ""),
                            "email": user_data.get("email", ""),
                            "roles": user_data.get("roles", ["user"]),
                        },
                    )
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
