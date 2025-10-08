"""
Main entry point for AI Discovery Workshop Agent.

This module initializes the application, sets up authentication,
and registers Chainlit event handlers.
"""

import os

import chainlit as cl
from dotenv import load_dotenv

from interfaces import ConversationManager
from persistence.conversation_manager import (
    AzureStorageConversationManager,
    DummyConversationManager,
)

# Load env values from file before importing other modules
load_dotenv(".azure.env", override=False)
load_dotenv(".env", override=False)

from agents import ChainlitAgentManager  # noqa E402
from auth import is_oauth_enabled, oauth_callback, password_auth_callback  # noqa E402
from chat_handlers import (  # noqa E402
    on_chat_resume,
    on_chat_start,
    on_message,
    set_chat_profiles,
)
from persistence import AzureStorageManager  # noqa E402
from utils.cached_llm import create_llm  # noqa E402
from utils.config import setup_auth_secret  # noqa E402
from utils.logging_setup import get_logger  # noqa E402

logger = get_logger(__name__)

# Setup authentication secret
setup_auth_secret()

# Global instances - these will be available to chat_handlers via getter functions
_agent_manager: ChainlitAgentManager = ChainlitAgentManager()
_storage_manager: AzureStorageManager | None = None
_conversation_manager: ConversationManager

# Initialize persistence layer
try:
    if os.getenv("AZURE_STORAGE_CONNECTION_STRING") or os.getenv(
        "AZURE_STORAGE_ACCOUNT_URL"
    ):
        _storage_manager = AzureStorageManager()
        openai_client = None
        AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
        AZURE_OPENAI_API_VERSION = os.getenv(
            "AZURE_OPENAI_API_VERSION", "2025-04-01-preview"
        )
        CONVERSATION_TITLE_MODEL_DEPLOYMENT = os.getenv(
            "CONVERSATION_TITLE_MODEL_DEPLOYMENT", "gpt-4"
        )

        client = create_llm(
            endpoint=AZURE_OPENAI_ENDPOINT,
            api_version=AZURE_OPENAI_API_VERSION,
            deployment=CONVERSATION_TITLE_MODEL_DEPLOYMENT,
            temperature=0.3,
            tag="conversation_manager_init",
        )

        _conversation_manager = AzureStorageConversationManager(
            _storage_manager, client
        )
        logger.info("Azure Storage persistence enabled")
    else:
        logger.warning(
            "Azure Storage not configured - conversations will not be persisted"
        )
        _conversation_manager = DummyConversationManager()
except Exception as e:
    logger.error(f"Failed to initialize persistence layer: {e}")
    _storage_manager = None
    _conversation_manager = DummyConversationManager()


def get_agent_manager() -> ChainlitAgentManager:
    """Get the global agent manager instance."""
    return _agent_manager


def get_storage_manager() -> AzureStorageManager | None:
    """Get the global storage manager instance."""
    return _storage_manager


def get_conversation_manager() -> ConversationManager:
    """Get the global conversation manager instance."""
    return _conversation_manager


# Register authentication callbacks
@cl.password_auth_callback
async def auth_callback(username: str, password: str) -> cl.User | None:
    """Handle password authentication."""
    return await password_auth_callback(username, password)


# Register OAuth callback if OAuth is enabled
oauth_enabled = is_oauth_enabled()

if oauth_enabled:
    logger.info("OAuth authentication is enabled")

    @cl.oauth_callback
    async def oauth_auth_callback(
        provider_id: str,
        token: str,
        raw_user_data: dict,
        default_user: cl.User,
        id_token: str | None = None,
    ) -> cl.User | None:
        """Handle OAuth authentication."""
        return await oauth_callback(
            provider_id, token, raw_user_data, default_user, id_token
        )

else:
    logger.info(
        "OAuth authentication is disabled - only password authentication is available"
    )


# Register chat event handlers
@cl.set_chat_profiles
async def chat_profile(user: cl.User | None = None):
    """Set available chat profiles."""
    return await set_chat_profiles(get_agent_manager(), user)


@cl.on_chat_start
async def start():
    """Handle chat start event."""
    await on_chat_start(get_agent_manager(), get_conversation_manager())


@cl.on_message
async def main(message: cl.Message):
    """Handle incoming messages."""
    await on_message(get_conversation_manager(), message)


@cl.on_chat_resume
async def resume(thread):
    """Handle chat resume event."""
    await on_chat_resume(get_agent_manager(), get_conversation_manager(), thread)


if __name__ == "__main__":
    cl.run()
