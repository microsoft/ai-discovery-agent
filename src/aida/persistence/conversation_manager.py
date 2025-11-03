# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Conversation management service.

This module provides high-level conversation management capabilities including
automatic conversation titling, conversation lifecycle management, and integration
with the persistence layer.
"""

from datetime import UTC, datetime
from typing import Any

from langchain.chat_models.base import BaseChatModel
from langchain_core.messages import HumanMessage, SystemMessage

from aida.interfaces.interfaces import ConversationManager
from aida.utils.logging_setup import get_logger

from .azure_storage import AzureStorageManager

logger = get_logger(__name__)


class AzureStorageConversationManager(ConversationManager):
    """
    Manages conversation lifecycle including creation, titling, and persistence.

    Features:
    - Automatic conversation creation and unique ID generation
    - AI-powered conversation titling based on initial messages
    - Integration with Azure Storage for persistence
    - Conversation metadata management
    """

    def __init__(
        self,
        storage_manager: AzureStorageManager,
        openai_client: BaseChatModel | None = None,
    ):
        """
        Initialize conversation manager.

        Args:
            storage_manager: Azure Storage manager instance.
            openai_client: Azure OpenAI client configured with endpoint and key.
        """
        self.storage_manager = storage_manager
        self.openai_client = openai_client

    async def generate_conversation_title(self, messages: list[dict[str, str]]) -> str:
        """
        Generate a conversation title based on initial messages using Azure OpenAI.

        Args:
            messages: List of conversation messages.

        Returns:
            Generated conversation title (falls back to timestamp if model/client unavailable).
        """
        if not self.openai_client or not messages:
            return f"Conversation {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"
        try:
            # Take first few user messages for context
            user_messages = [msg for msg in messages[:5] if msg.get("role") == "user"]
            if not user_messages:
                return f"Conversation {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"

            # Combine first user messages
            context = " ".join([msg["content"][:200] for msg in user_messages])

            prompt = f"""Based on the following conversation start, generate a concise, descriptive title (maximum 50 characters):

Context: {context}

Generate a title that captures the main topic or intent. Be specific and informative."""

            response = await self.openai_client.agenerate(
                messages=[
                    [
                        SystemMessage(
                            content="You are a helpful assistant that generates concise, descriptive conversation titles."
                        ),
                        HumanMessage(content=prompt),
                    ]
                ]
            )

            if (
                not response
                or not hasattr(response, "generations")
                or not response.generations
                or not response.generations[0]
                or not response.generations[0][0]
                or not hasattr(response.generations[0][0], "text")
                or not response.generations[0][0].text
            ):
                return f"Conversation {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"

            title = response.generations[0][0].text.strip()
            # Clean up the title
            title = title.replace('"', "").replace("'", "")[:50]
            return title

        except Exception as e:
            logger.error(
                f"Error generating conversation title via Azure OpenAI deployment "
                f"'{self.openai_client.model_name}': {e}"
            )
            return f"Conversation {datetime.now(UTC).strftime('%Y-%m-%d %H:%M')}"

    async def create_conversation(
        self,
        user_id: str,
        agent_key: str,
        initial_messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Create a new conversation.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            initial_messages: Optional initial messages

        Returns:
            Conversation ID
        """
        conversation_id = self.generate_conversation_id()

        # Generate title if we have initial messages
        title = "New Conversation"
        if initial_messages:
            title = await self.generate_conversation_title(initial_messages)

        conversation_data = {
            "title": title,
            "messages": initial_messages or [],
            "created_at": datetime.now(UTC).isoformat(),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        success = await self.storage_manager.save_conversation(
            user_id, agent_key, conversation_id, conversation_data
        )

        if success:
            logger.info(
                f"Created new conversation {conversation_id} for user {user_id}"
            )
        else:
            logger.error(
                f"Failed to create conversation {conversation_id} for user {user_id}"
            )

        return conversation_id

    async def save_conversation(
        self,
        user_id: str,
        agent_key: str,
        conversation_id: str,
        messages: list[dict[str, str]],
        title: str | None = None,
    ) -> bool:
        """
        Save conversation with updated messages.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier
            messages: Updated message list
            title: Optional conversation title

        Returns:
            True if successful, False otherwise
        """
        # Load existing conversation to preserve metadata
        existing_data = await self.storage_manager.load_conversation(
            user_id, agent_key, conversation_id
        )

        conversation_data = {
            "title": title
            or (
                existing_data.get("title") if existing_data else "Untitled Conversation"
            ),
            "messages": messages,
            "created_at": (
                existing_data.get("created_at")
                if existing_data
                else datetime.now(UTC).isoformat()
            ),
            "updated_at": datetime.now(UTC).isoformat(),
        }

        # Update title if not set and we have enough messages
        if not title and len(messages) >= 2:
            conversation_data["title"] = await self.generate_conversation_title(
                messages
            )

        return await self.storage_manager.save_conversation(
            user_id, agent_key, conversation_id, conversation_data
        )

    async def load_conversation(
        self, user_id: str, agent_key: str, conversation_id: str
    ) -> dict[str, Any] | None:
        """
        Load conversation data.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            Conversation data if found, None otherwise
        """
        return await self.storage_manager.load_conversation(
            user_id, agent_key, conversation_id
        )

    async def list_conversations(
        self, user_id: str, agent_key: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List conversations for a user with enhanced metadata.

        Args:
            user_id: User identifier
            agent_key: Optional agent filter

        Returns:
            List of conversation metadata with titles
        """
        conversations = await self.storage_manager.list_conversations(
            user_id, agent_key
        )

        # Enhance with titles by loading conversation data
        enhanced_conversations = []
        for conv in conversations:
            conv_data = await self.storage_manager.load_conversation(
                user_id, conv["agent_key"], conv["conversation_id"]
            )
            if conv_data:
                enhanced_conversations.append(
                    {
                        **conv,
                        "title": conv_data.get("title", "Untitled"),
                        "message_count": len(conv_data.get("messages", [])),
                        "created_at": conv_data.get("created_at"),
                        "updated_at": conv_data.get("updated_at"),
                    }
                )

        return enhanced_conversations

    async def delete_conversation(
        self, user_id: str, agent_key: str, conversation_id: str
    ) -> bool:
        """
        Delete a conversation.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            True if successful, False otherwise
        """
        return await self.storage_manager.delete_conversation(
            user_id, agent_key, conversation_id
        )


class DummyConversationManager(ConversationManager):
    """
    Dummy conversation manager that performs no operations.

    This can be used when conversation persistence is not required.
    """

    def generate_conversation_id(self) -> str:
        """
        Generate a unique conversation ID.

        Returns:
            Unique conversation identifier
        """
        return "dummy-conversation-id"

    async def generate_conversation_title(self, messages: list[dict[str, str]]) -> str:
        """
        Generate a conversation title (dummy implementation).

        Args:
            messages: List of conversation messages.

        Returns:
            Default conversation title
        """
        return "New Conversation"

    async def create_conversation(
        self,
        user_id: str,
        agent_key: str,
        initial_messages: list[dict[str, str]] | None = None,
    ) -> str:
        """
        Create a new conversation (dummy implementation).

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            initial_messages: Optional initial messages

        Returns:
            Dummy Conversation ID
        """
        return self.generate_conversation_id()

    async def save_conversation(
        self,
        user_id: str,
        agent_key: str,
        conversation_id: str,
        messages: list[dict[str, str]],
        title: str | None = None,
    ) -> bool:
        """
        Save conversation (dummy implementation).

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier
            messages: Updated message list
            title: Optional conversation title

        Returns:
            Always returns True
        """
        return True

    async def load_conversation(
        self, user_id: str, agent_key: str, conversation_id: str
    ) -> dict[str, Any] | None:
        """
        Load conversation data (dummy implementation).

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            Always returns None
        """
        return None

    async def list_conversations(
        self, user_id: str, agent_key: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List conversations (dummy implementation).

        Args:
            user_id: User identifier
            agent_key: Optional agent filter

        Returns:
            Always returns an empty list
        """
        return []

    async def delete_conversation(
        self, user_id: str, agent_key: str, conversation_id: str
    ) -> bool:
        """
        Delete a conversation (dummy implementation).

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            Always returns True
        """
        return True
