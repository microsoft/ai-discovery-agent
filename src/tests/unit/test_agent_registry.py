# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Unit tests for the AgentRegistry class."""

from unittest.mock import MagicMock, patch

import pytest

from aida.agents.agent_registry import AgentRegistry


class TestAgentRegistry:
    """Test cases for AgentRegistry class."""

    @pytest.fixture
    def registry(self):
        """Create a fresh AgentRegistry instance for each test."""
        with patch("aida.agents.agent_registry.PAGES_FILE") as mock_file:
            mock_file.exists.return_value = True
            with patch("builtins.open", create=True) as mock_open:
                mock_open.return_value.__enter__.return_value.read.return_value = (
                    "agents: {}"
                )
                with patch("yaml.safe_load", return_value={"agents": {}}):
                    return AgentRegistry()

    def test_get_agent_single_document(self, registry):
        """Test creating a single agent with one document."""
        sample_config = {
            "persona": "prompts/facilitator_persona.md",
            "document": "prompts/workshop_guide.md",
            "model": "gpt-4o",
            "temperature": 0.7,
        }

        with patch.object(registry, "get", return_value=sample_config):
            with patch("aida.agents.agent_registry.SingleAgent") as mock_single_agent:
                mock_instance = MagicMock()
                mock_single_agent.return_value = mock_instance

                result = registry.get_agent("facilitator")

                mock_single_agent.assert_called_once_with(
                    agent_key="facilitator",
                    persona="prompts/facilitator_persona.md",
                    model="gpt-4o",
                    temperature=0.7,
                    documents="prompts/workshop_guide.md",
                )
                assert result == mock_instance

    def test_get_agent_multiple_documents(self, registry):
        """Test creating a single agent with multiple documents."""
        sample_config = {
            "persona": "prompts/expert_persona.md",
            "documents": ["prompts/doc1.md", "prompts/doc2.md"],
            "model": "gpt-4o-mini",
            "temperature": 1.0,
        }

        with patch.object(registry, "get", return_value=sample_config):
            with patch("aida.agents.agent_registry.SingleAgent") as mock_single_agent:
                mock_instance = MagicMock()
                mock_single_agent.return_value = mock_instance

                result = registry.get_agent("expert")

                mock_single_agent.assert_called_once_with(
                    agent_key="expert",
                    persona="prompts/expert_persona.md",
                    model="gpt-4o-mini",
                    temperature=1.0,
                    documents=frozenset(["prompts/doc1.md", "prompts/doc2.md"]),
                )
                assert result == mock_instance

    def test_get_agent_graph_agent(self, registry):
        """Test creating a graph agent."""
        sample_config = {
            "condition": "Analyze input and route to appropriate specialist",
            "agents": [
                {"agent": "technical_expert", "condition": "technical"},
                {"agent": "business_expert", "condition": "business"},
            ],
            "model": "gpt-4o",
            "temperature": 0.5,
        }

        with patch.object(registry, "get", return_value=sample_config):
            with patch("aida.agents.agent_registry.GraphAgent") as mock_graph_agent:
                mock_instance = MagicMock()
                mock_graph_agent.return_value = mock_instance

                result = registry.get_agent("router")

                mock_graph_agent.assert_called_once_with(
                    agent_key="router",
                    condition="Analyze input and route to appropriate specialist",
                    agents=[
                        {"agent": "technical_expert", "condition": "technical"},
                        {"agent": "business_expert", "condition": "business"},
                    ],
                    model="gpt-4o",
                    temperature=0.5,
                )
                assert result == mock_instance

    def test_get_agent_invalid_config(self, registry):
        """Test handling of invalid agent configuration."""
        from aida.exceptions import AgentConfigurationError

        invalid_config = {"invalid": "config"}

        with patch.object(registry, "get", return_value=invalid_config):
            with pytest.raises(
                AgentConfigurationError,
                match="missing 'persona' or 'condition' field",
            ):
                registry.get_agent("invalid")

    def test_get_agent_empty_config(self, registry):
        """Test handling of empty agent configuration."""
        from aida.exceptions import AgentNotFoundError

        with patch.object(registry, "get", return_value=None):
            with pytest.raises(AgentNotFoundError, match="Agent 'empty' not found"):
                registry.get_agent("empty")

    def test_get_agent_not_found(self, registry):
        """Test handling when agent key is not found."""
        from aida.exceptions import AgentNotFoundError

        with patch.object(registry, "get", return_value=None):
            with pytest.raises(
                AgentNotFoundError, match="Agent 'nonexistent' not found"
            ):
                registry.get_agent("nonexistent")

    def test_all_method_returns_available_agents(self, registry):
        """Test the all() method returns agent configurations."""
        sample_agents = {
            "facilitator": {"persona": "prompts/facilitator.md"},
            "expert": {"persona": "prompts/expert.md"},
        }

        with patch.object(registry, "_agents", sample_agents):
            result = registry.all()
            assert result == sample_agents

    def test_get_method_basic_functionality(self, registry):
        """Test the basic get method functionality."""
        sample_config = {"persona": "test.md", "model": "gpt-4o"}

        with patch.object(registry, "_agents", {"test_agent": sample_config}):
            result = registry.get("test_agent")
            assert result == sample_config

            result_none = registry.get("nonexistent")
            assert result_none is None

    def test_agent_creation_with_default_model(self, registry):
        """Test agent creation uses default model when not specified."""
        config_no_model = {"persona": "prompts/test.md"}

        with patch.object(registry, "get", return_value=config_no_model):
            with patch("aida.agents.agent_registry.SingleAgent") as mock_single:
                mock_single.return_value = MagicMock()

                registry.get_agent("test")

                # Should use default model "gpt-4o"
                call_kwargs = mock_single.call_args.kwargs
                assert call_kwargs["model"] == "gpt-4o"
