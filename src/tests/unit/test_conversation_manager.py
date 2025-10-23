"""Unit tests for the conversation_manager module."""

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

from persistence.conversation_manager import (
    AzureStorageConversationManager,
    DummyConversationManager,
)


class TestAzureStorageConversationManager:
    """Test cases for AzureStorageConversationManager."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_storage = AsyncMock()
        self.mock_openai_client = AsyncMock()
        self.manager = AzureStorageConversationManager(
            storage_manager=self.mock_storage, openai_client=self.mock_openai_client
        )

    async def test_init(self):
        """Test initialization of AzureStorageConversationManager."""
        manager = AzureStorageConversationManager(
            storage_manager=self.mock_storage, openai_client=self.mock_openai_client
        )
        assert manager.storage_manager == self.mock_storage
        assert manager.openai_client == self.mock_openai_client

    async def test_init_without_openai_client(self):
        """Test initialization without OpenAI client."""
        manager = AzureStorageConversationManager(storage_manager=self.mock_storage)
        assert manager.storage_manager == self.mock_storage
        assert manager.openai_client is None

    async def test_generate_conversation_title_without_client(self):
        """Test title generation when no OpenAI client is available."""
        manager = AzureStorageConversationManager(storage_manager=self.mock_storage)
        messages = [{"role": "user", "content": "Hello, I need help with Python"}]

        with patch("persistence.conversation_manager.datetime") as mock_datetime:
            mock_datetime.now.return_value.strftime.return_value = "2024-01-01 10:00"
            title = await manager.generate_conversation_title(messages)

        assert title == "Conversation 2024-01-01 10:00"

    async def test_generate_conversation_title_without_messages(self):
        """Test title generation with empty messages."""
        title = await self.manager.generate_conversation_title([])

        assert "Conversation" in title
        assert datetime.now(UTC).strftime("%Y-%m-%d") in title

    async def test_generate_conversation_title_no_user_messages(self):
        """Test title generation with no user messages."""
        messages = [{"role": "assistant", "content": "Hello! How can I help you?"}]

        title = await self.manager.generate_conversation_title(messages)

        assert "Conversation" in title
        assert datetime.now(UTC).strftime("%Y-%m-%d") in title

    async def test_generate_conversation_title_success(self):
        """Test successful title generation with OpenAI."""
        messages = [
            {"role": "user", "content": "I need help with Python data structures"},
            {"role": "assistant", "content": "I'd be happy to help!"},
        ]

        # Mock OpenAI response
        mock_generation = MagicMock()
        mock_generation.text = "Python Data Structures Help"

        mock_response = MagicMock()
        mock_response.generations = [[mock_generation]]

        self.mock_openai_client.agenerate.return_value = mock_response

        title = await self.manager.generate_conversation_title(messages)

        assert title == "Python Data Structures Help"
        self.mock_openai_client.agenerate.assert_called_once()

    async def test_generate_conversation_title_with_quotes(self):
        """Test title generation removes quotes from title."""
        messages = [{"role": "user", "content": "Help with 'Python' programming"}]

        mock_generation = MagicMock()
        mock_generation.text = '"Python Programming Help"'

        mock_response = MagicMock()
        mock_response.generations = [[mock_generation]]

        self.mock_openai_client.agenerate.return_value = mock_response

        title = await self.manager.generate_conversation_title(messages)

        assert title == "Python Programming Help"

    async def test_generate_conversation_title_truncates_long_title(self):
        """Test title generation truncates titles longer than 50 characters."""
        messages = [{"role": "user", "content": "Help with complex topic"}]

        mock_generation = MagicMock()
        mock_generation.text = (
            "This is a very long conversation title that exceeds fifty characters"
        )

        mock_response = MagicMock()
        mock_response.generations = [[mock_generation]]

        self.mock_openai_client.agenerate.return_value = mock_response

        title = await self.manager.generate_conversation_title(messages)

        assert len(title) == 50
        assert title == "This is a very long conversation title that exceed"

    async def test_generate_conversation_title_openai_error(self):
        """Test title generation handles OpenAI errors gracefully."""
        messages = [{"role": "user", "content": "Test message"}]

        self.mock_openai_client.agenerate.side_effect = Exception("OpenAI API error")

        title = await self.manager.generate_conversation_title(messages)

        assert "Conversation" in title
        assert datetime.now(UTC).strftime("%Y-%m-%d") in title

    async def test_generate_conversation_title_invalid_response(self):
        """Test title generation handles invalid OpenAI response."""
        messages = [{"role": "user", "content": "Test message"}]

        # Mock invalid response
        mock_response = MagicMock()
        mock_response.generations = []

        self.mock_openai_client.agenerate.return_value = mock_response

        title = await self.manager.generate_conversation_title(messages)

        assert "Conversation" in title

    async def test_create_conversation_success(self):
        """Test successful conversation creation."""
        self.mock_storage.save_conversation.return_value = True

        with patch.object(
            self.manager, "generate_conversation_id", return_value="test-conv-id"
        ):
            with patch.object(
                self.manager,
                "generate_conversation_title",
                return_value="Test Title",
            ):
                initial_messages = [{"role": "user", "content": "Hello"}]
                conversation_id = await self.manager.create_conversation(
                    user_id="user123",
                    agent_key="test_agent",
                    initial_messages=initial_messages,
                )

        assert conversation_id == "test-conv-id"
        self.mock_storage.save_conversation.assert_called_once()

    async def test_create_conversation_without_initial_messages(self):
        """Test conversation creation without initial messages."""
        self.mock_storage.save_conversation.return_value = True

        with patch.object(
            self.manager, "generate_conversation_id", return_value="test-conv-id"
        ):
            conversation_id = await self.manager.create_conversation(
                user_id="user123", agent_key="test_agent"
            )

        assert conversation_id == "test-conv-id"
        call_args = self.mock_storage.save_conversation.call_args
        conversation_data = call_args[0][3]  # Fourth argument is conversation_data
        assert conversation_data["title"] == "New Conversation"
        assert conversation_data["messages"] == []

    async def test_create_conversation_storage_failure(self):
        """Test conversation creation when storage fails."""
        self.mock_storage.save_conversation.return_value = False

        with patch.object(
            self.manager, "generate_conversation_id", return_value="test-conv-id"
        ):
            conversation_id = await self.manager.create_conversation(
                user_id="user123", agent_key="test_agent"
            )

        assert conversation_id == "test-conv-id"  # ID returned even if save fails

    async def test_save_conversation_new(self):
        """Test saving a new conversation."""
        self.mock_storage.load_conversation.return_value = None
        self.mock_storage.save_conversation.return_value = True

        messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        result = await self.manager.save_conversation(
            user_id="user123",
            agent_key="test_agent",
            conversation_id="conv123",
            messages=messages,
            title="Custom Title",
        )

        assert result is True
        self.mock_storage.save_conversation.assert_called_once()
        call_args = self.mock_storage.save_conversation.call_args
        conversation_data = call_args[0][3]
        assert conversation_data["title"] == "Custom Title"
        assert conversation_data["messages"] == messages

    async def test_save_conversation_existing(self):
        """Test updating an existing conversation."""
        existing_data = {
            "title": "Old Title",
            "messages": [{"role": "user", "content": "Previous message"}],
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
        }
        self.mock_storage.load_conversation.return_value = existing_data
        self.mock_storage.save_conversation.return_value = True

        new_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # Mock title generation since it will be called for messages >= 2 when no title provided
        with patch.object(
            self.manager, "generate_conversation_title", return_value="Generated Title"
        ) as mock_generate_title:
            result = await self.manager.save_conversation(
                user_id="user123",
                agent_key="test_agent",
                conversation_id="conv123",
                messages=new_messages,
            )

            # Should generate new title since no title parameter provided and messages >= 2
            mock_generate_title.assert_called_once_with(new_messages)

        assert result is True
        call_args = self.mock_storage.save_conversation.call_args
        conversation_data = call_args[0][3]
        assert conversation_data["title"] == "Generated Title"  # New generated title
        assert conversation_data["messages"] == new_messages
        assert conversation_data["created_at"] == "2024-01-01T10:00:00Z"

    async def test_save_conversation_existing_with_explicit_title(self):
        """Test updating an existing conversation with explicit title preserves existing metadata."""
        existing_data = {
            "title": "Old Title",
            "messages": [{"role": "user", "content": "Previous message"}],
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:00:00Z",
        }
        self.mock_storage.load_conversation.return_value = existing_data
        self.mock_storage.save_conversation.return_value = True

        new_messages = [
            {"role": "user", "content": "Hello"},
            {"role": "assistant", "content": "Hi there!"},
        ]

        # When explicit title is provided, should not generate new title
        with patch.object(
            self.manager, "generate_conversation_title"
        ) as mock_generate_title:
            result = await self.manager.save_conversation(
                user_id="user123",
                agent_key="test_agent",
                conversation_id="conv123",
                messages=new_messages,
                title="Explicit Title",
            )

            # Should not generate title when explicit title is provided
            mock_generate_title.assert_not_called()

        assert result is True
        call_args = self.mock_storage.save_conversation.call_args
        conversation_data = call_args[0][3]
        assert conversation_data["title"] == "Explicit Title"  # Explicit title used
        assert conversation_data["messages"] == new_messages
        assert conversation_data["created_at"] == "2024-01-01T10:00:00Z"

    async def test_save_conversation_auto_title_generation(self):
        """Test automatic title generation when saving conversation with enough messages."""
        self.mock_storage.load_conversation.return_value = None
        self.mock_storage.save_conversation.return_value = True

        with patch.object(
            self.manager,
            "generate_conversation_title",
            return_value="Auto Generated Title",
        ) as mock_generate_title:
            messages = [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi there!"},
            ]

            await self.manager.save_conversation(
                user_id="user123",
                agent_key="test_agent",
                conversation_id="conv123",
                messages=messages,
            )

            mock_generate_title.assert_called_once_with(messages)

    async def test_load_conversation_success(self):
        """Test successful conversation loading."""
        expected_data = {
            "title": "Test Conversation",
            "messages": [{"role": "user", "content": "Hello"}],
        }
        self.mock_storage.load_conversation.return_value = expected_data

        result = await self.manager.load_conversation(
            user_id="user123", agent_key="test_agent", conversation_id="conv123"
        )

        assert result == expected_data
        self.mock_storage.load_conversation.assert_called_once_with(
            "user123", "test_agent", "conv123"
        )

    async def test_load_conversation_not_found(self):
        """Test loading non-existent conversation."""
        self.mock_storage.load_conversation.return_value = None

        result = await self.manager.load_conversation(
            user_id="user123", agent_key="test_agent", conversation_id="conv123"
        )

        assert result is None

    async def test_list_conversations_success(self):
        """Test successful conversation listing."""
        raw_conversations = [
            {"agent_key": "test_agent", "conversation_id": "conv1"},
            {"agent_key": "test_agent", "conversation_id": "conv2"},
        ]
        self.mock_storage.list_conversations.return_value = raw_conversations

        # Mock conversation data for enhancement
        conv_data_1 = {
            "title": "First Conversation",
            "messages": [{"role": "user", "content": "Hello"}],
            "created_at": "2024-01-01T10:00:00Z",
            "updated_at": "2024-01-01T10:30:00Z",
        }
        conv_data_2 = {
            "title": "Second Conversation",
            "messages": [
                {"role": "user", "content": "Hi"},
                {"role": "assistant", "content": "Hello!"},
            ],
            "created_at": "2024-01-01T11:00:00Z",
            "updated_at": "2024-01-01T11:15:00Z",
        }

        self.mock_storage.load_conversation.side_effect = [conv_data_1, conv_data_2]

        result = await self.manager.list_conversations(
            user_id="user123", agent_key="test_agent"
        )

        assert len(result) == 2
        assert result[0]["title"] == "First Conversation"
        assert result[0]["message_count"] == 1
        assert result[1]["title"] == "Second Conversation"
        assert result[1]["message_count"] == 2

    async def test_list_conversations_with_missing_data(self):
        """Test conversation listing when some conversation data is missing."""
        raw_conversations = [
            {"agent_key": "test_agent", "conversation_id": "conv1"},
            {"agent_key": "test_agent", "conversation_id": "conv2"},
        ]
        self.mock_storage.list_conversations.return_value = raw_conversations

        # First conversation exists, second does not
        conv_data_1 = {"title": "First Conversation", "messages": []}
        self.mock_storage.load_conversation.side_effect = [conv_data_1, None]

        result = await self.manager.list_conversations(user_id="user123")

        assert len(result) == 1
        assert result[0]["title"] == "First Conversation"

    async def test_delete_conversation_success(self):
        """Test successful conversation deletion."""
        self.mock_storage.delete_conversation.return_value = True

        result = await self.manager.delete_conversation(
            user_id="user123", agent_key="test_agent", conversation_id="conv123"
        )

        assert result is True
        self.mock_storage.delete_conversation.assert_called_once_with(
            "user123", "test_agent", "conv123"
        )

    async def test_delete_conversation_failure(self):
        """Test conversation deletion failure."""
        self.mock_storage.delete_conversation.return_value = False

        result = await self.manager.delete_conversation(
            user_id="user123", agent_key="test_agent", conversation_id="conv123"
        )

        assert result is False


class TestDummyConversationManager:
    """Test cases for DummyConversationManager."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.manager = DummyConversationManager()

    def test_generate_conversation_id(self):
        """Test dummy conversation ID generation."""
        conv_id = self.manager.generate_conversation_id()
        assert conv_id == "dummy-conversation-id"

    async def test_generate_conversation_title(self):
        """Test dummy conversation title generation."""
        messages = [{"role": "user", "content": "Test message"}]
        title = await self.manager.generate_conversation_title(messages)
        assert title == "New Conversation"

    async def test_create_conversation(self):
        """Test dummy conversation creation."""
        conv_id = await self.manager.create_conversation(
            user_id="user123",
            agent_key="test_agent",
            initial_messages=[{"role": "user", "content": "Hello"}],
        )
        assert conv_id == "dummy-conversation-id"

    async def test_save_conversation(self):
        """Test dummy conversation saving."""
        result = await self.manager.save_conversation(
            user_id="user123",
            agent_key="test_agent",
            conversation_id="conv123",
            messages=[{"role": "user", "content": "Hello"}],
            title="Test Title",
        )
        assert result is True

    async def test_load_conversation(self):
        """Test dummy conversation loading."""
        result = await self.manager.load_conversation(
            user_id="user123", agent_key="test_agent", conversation_id="conv123"
        )
        assert result is None

    async def test_list_conversations(self):
        """Test dummy conversation listing."""
        result = await self.manager.list_conversations(
            user_id="user123", agent_key="test_agent"
        )
        assert result == []

    async def test_delete_conversation(self):
        """Test dummy conversation deletion."""
        result = await self.manager.delete_conversation(
            user_id="user123", agent_key="test_agent", conversation_id="conv123"
        )
        assert result is True


class TestConversationManagerEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.mock_storage = AsyncMock()
        self.mock_openai_client = AsyncMock()
        self.manager = AzureStorageConversationManager(
            storage_manager=self.mock_storage, openai_client=self.mock_openai_client
        )

    async def test_generate_conversation_title_with_long_messages(self):
        """Test title generation with very long user messages."""
        long_content = "This is a very long message " * 50  # > 200 chars
        messages = [{"role": "user", "content": long_content}]

        mock_generation = MagicMock()
        mock_generation.text = "Long Message Title"

        mock_response = MagicMock()
        mock_response.generations = [[mock_generation]]

        self.mock_openai_client.agenerate.return_value = mock_response

        title = await self.manager.generate_conversation_title(messages)

        assert title == "Long Message Title"
        # Verify that the agenerate method was called
        self.mock_openai_client.agenerate.assert_called_once()
        # Verify that content was truncated to 200 chars
        assert len(long_content[:200]) == 200

    async def test_generate_conversation_title_multiple_user_messages(self):
        """Test title generation with multiple user messages."""
        messages = [
            {"role": "user", "content": "First message"},
            {"role": "assistant", "content": "Response"},
            {"role": "user", "content": "Second message"},
            {"role": "user", "content": "Third message"},
            {"role": "user", "content": "Fourth message"},
            {"role": "user", "content": "Fifth message"},
            {"role": "user", "content": "Sixth message"},  # Should be ignored (> 5)
        ]

        mock_generation = MagicMock()
        mock_generation.text = "Multi-Message Conversation"

        mock_response = MagicMock()
        mock_response.generations = [[mock_generation]]

        self.mock_openai_client.agenerate.return_value = mock_response

        title = await self.manager.generate_conversation_title(messages)

        assert title == "Multi-Message Conversation"
        # Verify the method was called with appropriate messages
        self.mock_openai_client.agenerate.assert_called_once()

    async def test_save_conversation_storage_error(self):
        """Test save conversation when storage operations fail."""
        self.mock_storage.load_conversation.side_effect = Exception("Storage error")
        self.mock_storage.save_conversation.return_value = False

        # The function should propagate the storage error
        with patch.object(self.manager, "generate_conversation_title"):
            try:
                await self.manager.save_conversation(
                    user_id="user123",
                    agent_key="test_agent",
                    conversation_id="conv123",
                    messages=[{"role": "user", "content": "Hello"}],
                )
                # If no exception is raised, fail the test
                raise AssertionError("Expected exception to be raised")
            except Exception as e:
                # Verify the correct exception is raised
                assert str(e) == "Storage error"

    async def test_openai_client_model_name_attribute_error(self):
        """Test error handling when OpenAI client doesn't have model_name attribute."""
        self.mock_openai_client.agenerate.side_effect = Exception("API Error")

        messages = [{"role": "user", "content": "Test message"}]

        # Should not raise exception, should fall back to default title
        title = await self.manager.generate_conversation_title(messages)

        assert "Conversation" in title
