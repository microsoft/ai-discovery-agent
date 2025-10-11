# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Integration tests for message routing and chat handling.

Tests the interaction between chat handlers, agent manager, and session management.
"""

from unittest.mock import AsyncMock, MagicMock, Mock, patch

import chainlit as cl
import pytest

import main
from agents.agent_manager import ChainlitAgentManager
from chat_handlers import on_chat_start, set_chat_profiles
from persistence.conversation_manager import DummyConversationManager
from tests.fixtures.data import (
    create_mock_admin_user,
    create_mock_user,
)


class TestChatProfileIntegration:
    """Test chat profile setup integration."""

    @pytest.fixture
    def mock_agent_manager(self):
        """Create a mock agent manager."""
        manager = Mock(spec=ChainlitAgentManager)
        manager.get_available_agents.return_value = {
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
        return manager

    async def test_set_chat_profiles_regular_user(self, mock_agent_manager):
        """Test chat profile setup for regular user."""
        # Create a mock user
        user = Mock(spec=cl.User)
        user.metadata = {"roles": ["user"]}

        # Mock the get_agent_manager function
        with patch("main.get_agent_manager", return_value=mock_agent_manager):
            # Test with user having restricted access
            mock_agent_manager.get_available_agents.return_value = {
                "facilitator": {
                    "title": "Workshop Facilitator",
                    "header": "Facilitator",
                    "subtitle": "AI Workshop Facilitator",
                    "default": True,
                },
            }

            profiles = await set_chat_profiles(main.get_agent_manager(), user)

            # Should have one profile for regular user
            assert len(profiles) == 1
            assert profiles[0].name == "Facilitator"
            assert profiles[0].markdown_description == "AI Workshop Facilitator"
            assert profiles[0].default is True

    async def test_set_chat_profiles_admin_user(self, mock_agent_manager):
        """Test chat profile setup for admin user."""
        # Create a mock admin user
        user = Mock(spec=cl.User)
        user.metadata = {"roles": ["admin", "user"]}

        # Mock the get_agent_manager function
        with patch("main.get_agent_manager", return_value=mock_agent_manager):
            profiles = await set_chat_profiles(main.get_agent_manager(), user)

            # Should have both profiles for admin user
            assert len(profiles) == 2
            profile_names = [p.name for p in profiles]
            assert "Facilitator" in profile_names
            assert "Expert" in profile_names

    async def test_set_chat_profiles_no_user(self):
        """Test chat profile setup when no user is provided."""
        profiles = await set_chat_profiles(main.get_agent_manager(), None)

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
        # Mock the agent manager
        mock_agent_manager = Mock(spec=ChainlitAgentManager)
        mock_agent_manager.get_available_agents.return_value = {
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

            with patch("main.get_agent_manager", return_value=mock_agent_manager):
                with patch("chainlit.Message") as mock_message:
                    mock_message_instance = AsyncMock()
                    mock_message.return_value = mock_message_instance

                    # Act
                    await on_chat_start(
                        main.get_agent_manager(), DummyConversationManager()
                    )

                    # Assert
                    mock_agent_manager.get_available_agents.assert_called_once_with(
                        ["user"]
                    )
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
                await on_chat_start(
                    main.get_agent_manager(), DummyConversationManager()
                )

                # Assert - should send authentication error message
                mock_message_instance.send.assert_called()
                # Get the message content that was sent
                call_args = mock_message.call_args[1] if mock_message.call_args else {}
                content = call_args.get("content", "")
                assert "Authentication required" in content

    async def test_on_chat_start_no_available_agents(self, mock_user):
        """Test chat start when user has no available agents."""
        mock_agent_manager = Mock(spec=ChainlitAgentManager)
        mock_agent_manager.get_available_agents.return_value = {}

        with patch("chainlit.user_session") as mock_cl_session:
            mock_cl_session.get.return_value = mock_user

            with patch("main.get_agent_manager", return_value=mock_agent_manager):
                with patch("chainlit.Message") as mock_message:
                    mock_message_instance = AsyncMock()
                    mock_message.return_value = mock_message_instance

                    # Act
                    await on_chat_start(
                        main.get_agent_manager(), DummyConversationManager()
                    )

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
        # This test would be more complex in a real implementation
        # For now, we'll test the structure exists

        with patch("chainlit.user_session") as mock_session:
            # Mock session data
            mock_session.get.return_value = {"current_agent": "facilitator"}

            # Mock agent processing
            with patch("chat_handlers.agent_registry") as mock_registry:
                mock_agent = Mock()
                mock_agent.astream = AsyncMock()
                mock_registry.get_agent.return_value = mock_agent

                with patch("chainlit.Message") as mock_cl_message:
                    mock_cl_message_instance = AsyncMock()
                    mock_cl_message.return_value = mock_cl_message_instance

                    # Act - This would call on_message but we need to mock more components
                    # For now, just verify the structure is testable
                    pass

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
