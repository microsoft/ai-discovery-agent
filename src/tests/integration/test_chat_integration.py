# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Integration tests for message routing and chat handling.

Tests the interaction between chat handlers, agent manager, and session management.
"""

from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, Mock, patch

import chainlit as cl
import pytest

from aida.persistence.conversation_manager import DummyConversationManager
from aida.utils.chat_handlers import on_chat_start, on_message, set_chat_profiles
from tests.fixtures.data import (
    create_mock_admin_user,
    create_mock_user,
)


class TestChatProfileIntegration:
    """Test chat profile setup integration."""

    @pytest.fixture
    def mock_available_agents(self):
        """Mock available agents for testing."""
        return {
            "facilitator": {
                "title": "Workshop Facilitator",
                "header": "Facilitator",
                "subtitle": "AI Workshop Facilitator",
                "default": True,
            },
            "expert": {
                "title": "Expert Advisor",
                "header": "Expert",
                "subtitle": "Domain Expert",
                "default": False,
            },
        }

    async def test_set_chat_profiles_regular_user(self, mock_available_agents):
        """Test chat profile setup for regular user."""
        # Create a mock user
        user = Mock(spec=cl.User)
        user.metadata = {"roles": ["user"]}

        # Mock the agent_manager module functions
        with patch("aida.agents.agent_manager.get_available_agents") as mock_get_agents:
            # Test with user having restricted access
            mock_get_agents.return_value = {
                "facilitator": mock_available_agents["facilitator"]
            }

            profiles = await set_chat_profiles(user)

            # Should have one profile for regular user
            assert len(profiles) == 1
            assert profiles[0].name == "Facilitator"
            assert profiles[0].markdown_description == "AI Workshop Facilitator"
            assert profiles[0].default is True

    async def test_set_chat_profiles_admin_user(self, mock_available_agents):
        """Test chat profile setup for admin user."""
        # Create a mock admin user
        user = Mock(spec=cl.User)
        user.metadata = {"roles": ["admin", "user"]}

        # Mock the agent_manager module functions
        with patch("aida.agents.agent_manager.get_available_agents") as mock_get_agents:
            mock_get_agents.return_value = mock_available_agents

            profiles = await set_chat_profiles(user)

            # Should have both profiles for admin user
            assert len(profiles) == 2
            profile_names = [p.name for p in profiles]
            assert "Facilitator" in profile_names
            assert "Expert" in profile_names

    async def test_set_chat_profiles_no_user(self):
        """Test chat profile setup when no user is provided."""
        profiles = await set_chat_profiles(None)

        # Should return empty list when no user
        assert profiles == []


class TestChatStartIntegration:
    """Test chat session initialization integration."""

    @pytest.fixture
    def mock_session(self):
        """Create mock user session."""
        session = MagicMock()
        return session

    @pytest.fixture
    def mock_user(self):
        """Create a mock user."""
        user = Mock(spec=cl.User)
        user.identifier = "testuser"
        user.metadata = {
            "first_name": "Test",
            "roles": ["user"],
        }
        return user

    async def test_on_chat_start_with_user(self, mock_session, mock_user):
        """Test chat start with authenticated user."""
        # Mock the agent manager functions
        with patch("aida.agents.agent_manager.get_available_agents") as mock_get_agents:
            mock_get_agents.return_value = {
                "facilitator": {
                    "title": "Workshop Facilitator",
                    "header": "Facilitator",
                    "subtitle": "AI Workshop Facilitator",
                    "default": True,
                }
            }

            with patch("chainlit.user_session") as mock_cl_session:
                mock_cl_session.get.return_value = mock_user
                mock_cl_session.set = Mock()

                with patch("chainlit.Message") as mock_message:
                    mock_message_instance = AsyncMock()
                    mock_message.return_value = mock_message_instance

                    # Act
                    await on_chat_start(DummyConversationManager())

                    # Assert
                    mock_get_agents.assert_called_once_with(["user"])
                    # Check that session was set with available agents
                    mock_cl_session.set.assert_any_call(
                        "available_agents",
                        {
                            "facilitator": {
                                "title": "Workshop Facilitator",
                                "header": "Facilitator",
                                "subtitle": "AI Workshop Facilitator",
                                "default": True,
                            }
                        },
                    )
                    mock_message_instance.send.assert_called()

    async def test_on_chat_start_no_user(self):
        """Test chat start without authenticated user."""
        with patch("chainlit.user_session") as mock_cl_session:
            mock_cl_session.get.return_value = None

            with patch("chainlit.Message") as mock_message:
                mock_message_instance = AsyncMock()
                mock_message.return_value = mock_message_instance

                # Act
                await on_chat_start(DummyConversationManager())

                # Assert - should send authentication error message
                mock_message_instance.send.assert_called()
                # Get the message content that was sent
                call_args = mock_message.call_args[1] if mock_message.call_args else {}
                content = call_args.get("content", "")
                assert "Authentication required" in content

    async def test_on_chat_start_no_available_agents(self, mock_user):
        """Test chat start when user has no available agents."""
        with patch("aida.agents.agent_manager.get_available_agents") as mock_get_agents:
            mock_get_agents.return_value = {}

            with patch("chainlit.user_session") as mock_cl_session:
                mock_cl_session.get.return_value = mock_user

                with patch("chainlit.Message") as mock_message:
                    mock_message_instance = AsyncMock()
                    mock_message.return_value = mock_message_instance

                    # Act
                    await on_chat_start(DummyConversationManager())

                    # Assert - should send no agents available message
                    mock_message_instance.send.assert_called()


class TestMessageRoutingIntegration:
    """Test message routing and processing integration."""

    @pytest.fixture
    def mock_message(self):
        """Create a mock Chainlit message."""
        message = Mock(spec=cl.Message)
        message.content = "Hello, how can I help?"
        return message

    async def test_message_routing_basic_flow(self, mock_message):
        """Test basic message routing flow."""
        # This test exercises the real on_message -> process_with_agent flow using
        # patched Chainlit primitives and a dummy streaming agent.

        # Prepare a dummy user object
        user = Mock(spec=cl.User)
        user.identifier = "test-user"
        user.metadata = {"roles": ["user"], "first_name": "Test"}

        # Store simulating chainlit.user_session internal key/value storage
        session_store: dict[str, object] = {
            "user": user,
            "current_agent_key": "facilitator",
            # start with empty conversation history
            "conversation_history": [],
            # dummy conversation id so saving logic can run without error
            "current_conversation_id": "conv-1",
        }

        # Side effect handlers replicating Chainlit's session get/set
        def session_get(key: str, default: object | None = None):
            return session_store.get(key, default)

        def session_set(key: str, value: object):
            session_store[key] = value

        # Dummy Step context manager used by process_with_agent
        class DummyStep:  # pragma: no cover - trivial helper
            def __init__(self, name: str):
                self.name = name
                self.input = None
                self.output = None

            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, tb):
                return False

            async def send(self):  # mimic Chainlit Step .send()
                return None

        # Dummy streaming agent that yields two chunks
        class DummyAgent:  # pragma: no cover - simple test double
            async def astream(
                self, history: list[dict[str, str]], config: object
            ) -> AsyncIterator[Any]:
                # Simulate token streaming
                for token in ["Hello", " world"]:
                    # Yield an object with a .content attribute like LangChain messages
                    yield type("Chunk", (), {"content": token})()

        dummy_agent = DummyAgent()

        # Patch Chainlit components and agent registry
        class DummyLCB:
            pass

        with (
            patch("chainlit.user_session") as mock_session,
            patch(
                "aida.utils.chat_handlers.agent_registry.get_agent",
                return_value=dummy_agent,
            ) as mock_get_agent,
            patch("chainlit.Step", DummyStep),
            patch("chainlit.LangchainCallbackHandler", DummyLCB),
            patch("chainlit.Message") as mock_cl_message,
        ):
            # Configure session get/set behaviour
            mock_session.get.side_effect = session_get
            mock_session.set.side_effect = session_set

            # Build a realistic Message mock that accumulates streamed tokens
            class DummyCLMessage(AsyncMock):  # pragma: no cover
                def __init__(self, *args, **kwargs):
                    """
                    Initialize dummy Chainlit message for testing.

                    Args:
                        *args: Positional arguments.
                        **kwargs: Keyword arguments, may include 'content'.
                    """
                    super().__init__()
                    self.content = kwargs.get("content", "")
                    self.elements = []

                async def send(self):
                    """Send the message (no-op in tests)."""
                    return None

                async def stream_token(self, token: str):
                    """Accumulate streamed token into message content."""
                    self.content += token
                    return None

                async def remove(self):
                    """Simulate removing the message (no-op implementation for testing)."""
                    return None

            mock_cl_message.side_effect = lambda *a, **kw: DummyCLMessage(*a, **kw)

            # Incoming user message fixture adaptation
            mock_message.content = "Hi there"

            # Act
            await on_message(DummyConversationManager(), mock_message)

            # Assert agent lookup occurred with current agent key
            mock_get_agent.assert_called_once_with("facilitator")

            # Conversation history should now contain user + assistant messages
            history = session_store.get("conversation_history")
            assert isinstance(history, list), "conversation_history should be a list"
            assert len(history) == 2, (
                "Expected two messages in history (user & assistant)"
            )
            assert history[0]["role"] == "user"
            assert history[0]["content"] == "Hi there"
            assert history[1]["role"] == "assistant"
            # The assistant concatenated streamed tokens
            assert history[1]["content"] == "Hello world"

    def test_message_content_extraction(self, mock_message):
        """Test message content extraction."""
        # Test that we can extract content from messages
        assert mock_message.content == "Hello, how can I help?"

        # Test with different content types
        mock_message.content = "!facilitator"
        assert mock_message.content.startswith("!")

        mock_message.content = "What is AI?"
        assert not mock_message.content.startswith("!")


class TestWorkshopFlowIntegration:
    """Test complete workshop facilitation flow integration."""

    def test_agent_switching_commands(self):
        """Test agent switching command parsing."""
        # Test command detection
        commands = ["!facilitator", "!expert", "!help"]

        for cmd in commands:
            assert cmd.startswith("!")
            agent_name = cmd[1:]  # Remove ! prefix
            assert agent_name in ["facilitator", "expert", "help"]

    def test_user_role_workflow(self):
        """Test complete user role-based workflow."""
        # Test user role mapping
        regular_user = create_mock_user()
        admin_user = create_mock_admin_user()

        assert "user" in regular_user["metadata"]["roles"]
        assert "admin" in admin_user["metadata"]["roles"]
        assert "user" in admin_user["metadata"]["roles"]

        # Test role-based agent access
        user_roles = regular_user["metadata"]["roles"]
        admin_roles = admin_user["metadata"]["roles"]

        # Regular user should not have admin access
        is_user_admin = "admin" in user_roles
        assert is_user_admin is False

        # Admin user should have admin access
        is_admin_admin = "admin" in admin_roles
        assert is_admin_admin is True
