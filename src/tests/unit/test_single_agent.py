"""Unit tests for the SingleAgent class."""

from unittest.mock import MagicMock, patch

import pytest

from agents.single_agent import SingleAgent


class TestSingleAgent:
    """Test cases for SingleAgent class."""

    def test_init_with_single_document(self):
        """Test SingleAgent initialization with single document."""
        agent = SingleAgent(
            agent_key="test_agent",
            persona="prompts/facilitator_persona.md",
            model="gpt-4o",
            temperature=0.7,
            documents="prompts/workshop_guide.md",
        )

        assert agent.agent_key == "test_agent"
        assert agent.persona == "prompts/facilitator_persona.md"
        assert agent.documents == "prompts/workshop_guide.md"
        assert agent.model == "gpt-4o"
        assert agent.temperature == 0.7

    def test_init_with_multiple_documents(self):
        """Test SingleAgent initialization with multiple documents."""
        documents = frozenset(["prompts/doc1.md", "prompts/doc2.md"])
        agent = SingleAgent(
            agent_key="multi_agent",
            persona="prompts/expert_persona.md",
            model="gpt-4o-mini",
            temperature=1.0,
            documents=documents,
        )

        assert agent.agent_key == "multi_agent"
        assert agent.persona == "prompts/expert_persona.md"
        assert agent.documents == documents
        assert agent.model == "gpt-4o-mini"
        assert agent.temperature == 1.0

    def test_init_with_minimal_config(self):
        """Test SingleAgent initialization with minimal configuration."""
        agent = SingleAgent(
            agent_key="minimal_agent",
            persona="prompts/persona.md",
        )

        assert agent.agent_key == "minimal_agent"
        assert agent.persona == "prompts/persona.md"
        assert agent.documents is None
        assert agent.model is None
        assert agent.temperature is None

    def test_init_with_defaults(self):
        """Test agent initialization with default values."""
        agent = SingleAgent(
            agent_key="default_agent",
            persona="prompts/persona.md",
            model="gpt-4o",
        )

        assert agent.documents is None
        assert agent.temperature is None

    @patch("agents.single_agent.load_prompt_files")
    def test_get_system_prompts_single_document(self, mock_load_prompt_files):
        """Test system prompt generation with single document."""
        mock_load_prompt_files.return_value = [
            "Facilitator persona content",
            "Workshop guide content",
        ]

        agent = SingleAgent(
            agent_key="test_agent",
            persona="prompts/facilitator_persona.md",
            documents="prompts/workshop_guide.md",
        )
        system_prompts = agent.get_system_prompts()

        mock_load_prompt_files.assert_called_once_with(
            "prompts/facilitator_persona.md", "prompts/workshop_guide.md"
        )

        assert len(system_prompts) == 2
        assert system_prompts[0].content == "Facilitator persona content"
        assert system_prompts[1].content == "Workshop guide content"

    @patch("agents.single_agent.load_prompt_files")
    def test_get_system_prompts_multiple_documents(self, mock_load_prompt_files):
        """Test system prompt generation with multiple documents."""
        mock_load_prompt_files.return_value = [
            "Expert persona content",
            "Domain knowledge content",
            "Best practices content",
        ]

        documents = frozenset(["prompts/doc1.md", "prompts/doc2.md"])
        agent = SingleAgent(
            agent_key="multi_agent",
            persona="prompts/expert_persona.md",
            documents=documents,
        )
        system_prompts = agent.get_system_prompts()

        mock_load_prompt_files.assert_called_once_with(
            "prompts/expert_persona.md", documents
        )

        assert len(system_prompts) == 3
        assert system_prompts[0].content == "Expert persona content"
        assert system_prompts[1].content == "Domain knowledge content"
        assert system_prompts[2].content == "Best practices content"

    @patch("agents.single_agent.load_prompt_files")
    def test_get_system_prompts_no_documents(self, mock_load_prompt_files):
        """Test system prompt generation with no documents."""
        mock_load_prompt_files.return_value = ["Persona content only"]

        agent = SingleAgent(
            agent_key="no_docs",
            persona="prompts/persona.md",
        )
        system_prompts = agent.get_system_prompts()

        mock_load_prompt_files.assert_called_once_with("prompts/persona.md", None)
        assert len(system_prompts) == 1
        assert system_prompts[0].content == "Persona content only"

    @patch("agents.single_agent.load_prompt_files")
    def test_get_system_prompts_load_error_handling(self, mock_load_prompt_files):
        """Test error handling when prompt loading fails."""
        mock_load_prompt_files.side_effect = FileNotFoundError("Prompt file not found")

        agent = SingleAgent(
            agent_key="error_test",
            persona="prompts/persona.md",
        )

        with pytest.raises(FileNotFoundError):
            agent.get_system_prompts()

    @patch("agents.single_agent.ChatPromptTemplate")
    @patch("agents.single_agent.MessagesPlaceholder")
    def test_create_chain(self, mock_messages_placeholder, mock_chat_prompt_template):
        """Test chain creation functionality."""
        # Mock the template components
        mock_placeholder = MagicMock()
        mock_messages_placeholder.return_value = mock_placeholder

        mock_template = MagicMock()
        mock_chat_prompt_template.from_messages.return_value = mock_template

        agent = SingleAgent(
            agent_key="test_agent",
            persona="prompts/persona.md",
            model="gpt-4o",
            temperature=0.7,
        )

        # Mock the _get_azure_chat_openai method
        with patch.object(agent, "_get_azure_chat_openai") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # First call should create the chain
            chain1 = agent.create_chain()

            # Verify the components were called correctly
            mock_messages_placeholder.assert_called_once_with("messages")
            mock_chat_prompt_template.from_messages.assert_called_once_with(
                [mock_placeholder]
            )
            mock_get_llm.assert_called_once_with(tag="response")

            # Second call should return cached chain
            chain2 = agent.create_chain()
            assert chain1 is chain2  # Same instance

            # Should not call the components again
            assert mock_messages_placeholder.call_count == 1
            assert mock_chat_prompt_template.from_messages.call_count == 1
            assert mock_get_llm.call_count == 1

    def test_create_chain_caching(self):
        """Test that create_chain caches the result."""
        agent = SingleAgent(
            agent_key="cache_test",
            persona="prompts/persona.md",
        )

        with patch.object(agent, "_get_azure_chat_openai") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # First call
            chain1 = agent.create_chain()
            assert agent._chain is not None

            # Second call should return cached instance
            chain2 = agent.create_chain()
            assert chain1 is chain2

    def test_str_representation(self):
        """Test string representation of SingleAgent."""
        agent = SingleAgent(
            agent_key="test_agent",
            persona="prompts/persona.md",
        )
        str_repr = str(agent)

        # Should use the base Agent's string representation
        assert "test_agent" in str_repr

    def test_inheritance_from_agent(self):
        """Test that SingleAgent properly inherits from Agent."""
        agent = SingleAgent(
            agent_key="inheritance_test",
            persona="prompts/persona.md",
            model="gpt-4o",
            temperature=0.5,
        )

        # Should have Agent's attributes
        assert hasattr(agent, "agent_key")
        assert hasattr(agent, "model")
        assert hasattr(agent, "temperature")
        assert hasattr(agent, "_llm")
        assert hasattr(agent, "_chain")

        # Should have Agent's methods
        assert hasattr(agent, "_get_azure_chat_openai")
        assert hasattr(agent, "astream")

    @patch("agents.single_agent.load_prompt_files")
    def test_logging_in_get_system_prompts(self, mock_load_prompt_files):
        """Test that logging occurs in get_system_prompts."""
        mock_load_prompt_files.return_value = ["Test content"]

        agent = SingleAgent(
            agent_key="log_test",
            persona="prompts/persona.md",
            documents="prompts/doc.md",
        )

        with patch("agents.single_agent.logger") as mock_logger:
            agent.get_system_prompts()

            # Verify debug logging was called
            mock_logger.debug.assert_called_once()
            call_args = mock_logger.debug.call_args[0]
            assert "Loading system messages for SingleAgent" in call_args[0]
            assert "log_test" in call_args[1]
            assert "prompts/persona.md" in call_args[2]
            assert "prompts/doc.md" in call_args[3]

    def test_agent_key_assignment(self):
        """Test that agent_key is properly assigned."""
        test_keys = ["simple", "with-dashes", "with_underscores", "with.dots"]

        for key in test_keys:
            agent = SingleAgent(
                agent_key=key,
                persona="prompts/persona.md",
            )
            assert agent.agent_key == key

    def test_persona_assignment(self):
        """Test that persona path is properly assigned."""
        test_personas = [
            "prompts/simple.md",
            "prompts/nested/deep/persona.md",
            "different_extension.txt",
        ]

        for persona in test_personas:
            agent = SingleAgent(
                agent_key="test",
                persona=persona,
            )
            assert agent.persona == persona

    def test_model_and_temperature_inheritance(self):
        """Test that model and temperature are passed to parent Agent class."""
        agent = SingleAgent(
            agent_key="test",
            persona="prompts/persona.md",
            model="custom-model",
            temperature=0.123,
        )

        # These should be set by the parent Agent.__init__
        assert agent.model == "custom-model"
        assert agent.temperature == 0.123
