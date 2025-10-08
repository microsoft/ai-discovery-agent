"""
Interfaces for testable abstractions.

This module defines abstract interfaces to decouple Chainlit and LangChain
interactions from the core business logic, making isolated testing easier.
"""

import uuid
from abc import ABC, abstractmethod
from typing import Any

import chainlit as cl


class IAgentManager(ABC):
    """Abstract interface for agent management."""

    @abstractmethod
    def load_configurations(self) -> None:
        """Load configuration from YAML files."""
        pass

    @abstractmethod
    def get_available_agents(
        self, user_roles: list[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Get available agents based on user roles."""
        pass

    @abstractmethod
    def get_agent_info(self, agent_key: str) -> dict[str, Any] | None:
        """Get information about a specific agent."""
        pass

    @abstractmethod
    def set_current_agent(self, agent_key: str) -> bool:
        """Set the current active agent."""
        pass


class IAuthenticator(ABC):
    """Abstract interface for authentication operations."""

    @abstractmethod
    async def password_auth_callback(
        self, username: str, password: str
    ) -> cl.User | None:
        """Authenticate user using password."""
        pass

    @abstractmethod
    async def oauth_callback(
        self,
        provider_id: str,
        token: str,
        raw_user_data: dict[str, str],
        default_user: cl.User,
        id_token: str | None = None,
    ) -> cl.User | None:
        """Authenticate user using OAuth."""
        pass

    @abstractmethod
    def is_oauth_enabled(self) -> bool:
        """Check if OAuth is enabled."""
        pass


class IFileLoader(ABC):
    """Abstract interface for file operations."""

    @abstractmethod
    def load_yaml_file(self, file_path: str) -> dict[str, Any]:
        """Load YAML file and return parsed content."""
        pass

    @abstractmethod
    def file_exists(self, file_path: str) -> bool:
        """Check if file exists."""
        pass


class IChainlitSession(ABC):
    """Abstract interface for Chainlit session operations."""

    @abstractmethod
    async def send_message(self, content: str) -> None:
        """Send a message to the user."""
        pass

    @abstractmethod
    def get_session_value(self, key: str) -> Any:
        """Get a value from the user session."""
        pass

    @abstractmethod
    def set_session_value(self, key: str, value: Any) -> None:
        """Set a value in the user session."""
        pass

    @abstractmethod
    def get_user(self) -> cl.User | None:
        """Get the current authenticated user."""
        pass


class ConversationManager(ABC):
    """
    Abstract base class for conversation management.

    Defines the interface for managing conversations including creation, titling,
    saving, loading, listing, and deletion.
    """

    def generate_conversation_id(self) -> str:
        """
        Generate a unique conversation ID.

        Returns:
            Unique conversation identifier
        """
        return str(uuid.uuid4())

    @abstractmethod
    async def generate_conversation_title(self, messages: list[dict[str, str]]) -> str:
        """
        Generate a conversation title based on initial messages using Azure OpenAI.

        Args:
            messages: List of conversation messages.

        Returns:
            Generated conversation title (falls back to timestamp if model/client unavailable).
        """
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
        pass

    @abstractmethod
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
