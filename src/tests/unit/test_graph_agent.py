# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Unit tests for the GraphAgent class."""

from unittest.mock import MagicMock, patch

import pytest

from aida.agents.graph_agent import AgentState, GraphAgent


class TestGraphAgent:
    """Test cases for GraphAgent class."""

    @pytest.fixture
    def sample_agents_config(self):
        """Sample agents configuration for testing."""
        return [
            {"agent": "technical_expert", "condition": "technical"},
            {"agent": "business_expert", "condition": "business"},
        ]

    def test_init_with_standard_config(self, sample_agents_config):
        """Test GraphAgent initialization with standard configuration."""
        agent = GraphAgent(
            agent_key="router_agent",
            condition="Analyze input and route to appropriate specialist",
            agents=sample_agents_config,
            model="gpt-4o",
            temperature=0.5,
        )

        assert agent.agent_key == "router_agent"
        assert agent.condition == "Analyze input and route to appropriate specialist"
        assert agent.agents == sample_agents_config
        assert agent.model == "gpt-4o"
        assert agent.temperature == 0.5

    def test_init_with_minimal_config(self):
        """Test GraphAgent initialization with minimal configuration."""
        agents = [{"agent": "single_agent", "condition": "always"}]
        agent = GraphAgent(
            agent_key="minimal_router",
            condition="Simple routing",
            agents=agents,
            model=None,
            temperature=None,
        )

        assert agent.agent_key == "minimal_router"
        assert agent.condition == "Simple routing"
        assert agent.agents == agents
        assert agent.model is None
        assert agent.temperature is None

    def test_init_with_default_temperature(self):
        """Test that default temperature is 0.7."""
        agents = [{"agent": "test_agent", "condition": "test"}]
        agent = GraphAgent(
            agent_key="temp_test",
            condition="Test condition",
            agents=agents,
            model="gpt-4o",
        )

        assert agent.temperature == 0.7

    def test_get_system_prompts_returns_empty_list(self, sample_agents_config):
        """Test that GraphAgent returns empty system prompts."""
        agent = GraphAgent(
            agent_key="test_router",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        system_prompts = agent.get_system_prompts()
        assert system_prompts == []

    def test_inheritance_from_agent(self, sample_agents_config):
        """Test that GraphAgent properly inherits from Agent."""
        agent = GraphAgent(
            agent_key="inheritance_test",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
            temperature=0.3,
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

    @patch("aida.agents.graph_agent.StateGraph")
    def test_create_chain_workflow_creation(
        self, mock_state_graph, sample_agents_config
    ):
        """Test chain creation with proper workflow setup."""
        # Mock the StateGraph and its methods
        mock_workflow = MagicMock()
        mock_state_graph.return_value = mock_workflow
        mock_compiled = MagicMock()
        mock_workflow.compile.return_value = mock_compiled

        agent = GraphAgent(
            agent_key="test_router",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        # First call should create the chain
        chain1 = agent.create_chain()

        # Verify StateGraph was initialized with AgentState
        mock_state_graph.assert_called_once_with(AgentState)

        # Verify nodes were added
        assert mock_workflow.add_node.call_count == 3

        # Verify edges were added
        assert mock_workflow.add_edge.call_count == 2

        # Verify conditional edges were added
        mock_workflow.add_conditional_edges.assert_called_once()

        # Verify entry point was set
        mock_workflow.set_entry_point.assert_called_once_with("start")

        # Verify workflow was compiled
        mock_workflow.compile.assert_called_once()

        assert chain1 == mock_compiled

        # Second call should return cached chain
        chain2 = agent.create_chain()
        assert chain1 is chain2
        assert mock_workflow.compile.call_count == 1  # Should not compile again

    @patch("aida.agents.graph_agent.StateGraph")
    def test_create_chain_error_handling(self, mock_state_graph, sample_agents_config):
        """Test error handling in chain creation."""
        # Mock StateGraph to raise an exception
        mock_state_graph.side_effect = Exception("Failed to create workflow")

        agent = GraphAgent(
            agent_key="error_test",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        with patch("aida.agents.graph_agent.logger") as mock_logger:
            with pytest.raises(Exception, match="Failed to create workflow"):
                agent.create_chain()

            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0]
            assert "Failed to create ConditionGraph" in error_call[0]

    def test_start_agent_with_input(self, sample_agents_config):
        """Test _start_agent method with input in state."""
        agent = GraphAgent(
            agent_key="test_router",
            condition="Analyze the input: {input}",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        # Mock the chain invoke method
        with patch.object(agent, "_get_azure_chat_openai") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # Mock the chain's invoke method to return the mock response
            with patch("aida.agents.graph_agent.ChatPromptTemplate") as mock_template:
                mock_prompt = MagicMock()
                mock_template.from_messages.return_value = mock_prompt

                # Create a chain mock that returns our desired response
                mock_chain = MagicMock()
                mock_response = MagicMock()
                mock_response.content = "technical"
                mock_chain.invoke.return_value = mock_response

                # Mock the | operator to return our chain
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)

                state = {
                    "input": "I need help with API integration",
                    "messages": [],
                }

                result = agent._start_agent(state)

            assert result["decision"] == "technical"
            assert result["input"] == "I need help with API integration"
            assert "Agent decision: technical" in result["output"]
            assert result["messages"] == []

    def test_start_agent_without_input_uses_messages(self, sample_agents_config):
        """Test _start_agent method without input, uses messages."""
        from langchain_core.messages import AIMessage, HumanMessage

        agent = GraphAgent(
            agent_key="test_router",
            condition="Analyze the conversation: {input}",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        # Mock the chain invoke method
        with patch.object(agent, "_get_azure_chat_openai") as mock_get_llm:
            mock_llm = MagicMock()
            mock_get_llm.return_value = mock_llm

            # Mock the chain's invoke method to return the mock response
            with patch("aida.agents.graph_agent.ChatPromptTemplate") as mock_template:
                mock_prompt = MagicMock()
                mock_template.from_messages.return_value = mock_prompt

                # Create a chain mock that returns our desired response
                mock_chain = MagicMock()
                mock_response = MagicMock()
                mock_response.content = "business"
                mock_chain.invoke.return_value = mock_response

                # Mock the | operator to return our chain
                mock_prompt.__or__ = MagicMock(return_value=mock_chain)

                messages = [
                    HumanMessage(content="What's our market strategy?"),
                    AIMessage(content="Let me analyze that for you."),
                ]
                state = {"input": "", "messages": messages}

                result = agent._start_agent(state)

            assert result["decision"] == "business"
            assert "human: what's our market strategy?" in result["input"].lower()
            assert "ai: let me analyze that for you." in result["input"].lower()

    def test_start_agent_response_parsing_variations(self, sample_agents_config):
        """Test different response formats from LLM in _start_agent."""
        agent = GraphAgent(
            agent_key="test_router",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        test_cases = [
            # Test string response
            {"response": MagicMock(content="  TECHNICAL  "), "expected": "technical"},
            # Test list content response
            {
                "response": MagicMock(content=["Business Analysis"]),
                "expected": "business analysis",
            },
            # Test empty list content
            {"response": MagicMock(content=[]), "expected": ""},
            # Test direct string response
            {
                "response": "Simple String Response",
                "expected": "simple string response",
            },
        ]

        for case in test_cases:
            with patch.object(agent, "_get_azure_chat_openai") as mock_get_llm:
                mock_llm = MagicMock()
                mock_get_llm.return_value = mock_llm

                # Mock the chain's invoke method to return the mock response
                with patch(
                    "aida.agents.graph_agent.ChatPromptTemplate"
                ) as mock_template:
                    mock_prompt = MagicMock()
                    mock_template.from_messages.return_value = mock_prompt

                    # Create a chain mock that returns our desired response
                    mock_chain = MagicMock()
                    mock_chain.invoke.return_value = case["response"]

                    # Mock the | operator to return our chain
                    mock_prompt.__or__ = MagicMock(return_value=mock_chain)

                    state = {"input": "test input", "messages": []}
                    result = agent._start_agent(state)

                    assert result["decision"] == case["expected"]

    @patch("aida.agents.agent_registry.agent_registry.get_agent")
    def test_agent_node_success(self, mock_get_agent, sample_agents_config):
        """Test successful _agent_node execution."""
        agent = GraphAgent(
            agent_key="test_router",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        # Mock the agent registry and agent
        mock_agent = MagicMock()
        mock_agent.get_system_prompts.return_value = []
        mock_chain = MagicMock()
        mock_chain.invoke.return_value = "Agent response"
        mock_agent.create_chain.return_value = mock_chain
        mock_get_agent.return_value = mock_agent

        state = {
            "decision": "technical_expert",
            "input": "test input",
            "messages": [],
            "output": "",
        }

        result = agent._agent_node(state)

        mock_get_agent.assert_called_once_with("technical_expert")
        mock_agent.get_system_prompts.assert_called_once()
        mock_agent.create_chain.assert_called_once()
        mock_chain.invoke.assert_called_once()

        assert result["output"] == "Agent response"

    @patch("aida.agents.agent_registry.agent_registry.get_agent")
    def test_agent_node_agent_not_found(self, mock_get_agent, sample_agents_config):
        """Test _agent_node when agent is not found."""
        agent = GraphAgent(
            agent_key="test_router",
            condition="Test condition",
            agents=sample_agents_config,
            model="gpt-4o",
        )

        # Mock registry to return None (agent not found)
        mock_get_agent.return_value = None

        state = {
            "decision": "nonexistent_agent",
            "input": "test input",
            "messages": [],
            "output": "",
        }

        with patch("aida.agents.graph_agent.logger") as mock_logger:
            with pytest.raises(
                ValueError, match="Agent nonexistent_agent not found in registry"
            ):
                agent._agent_node(state)

            # Verify error was logged
            mock_logger.error.assert_called_once()
            error_call = mock_logger.error.call_args[0]
            assert "Agent nonexistent_agent not found in registry" in error_call[0]

    def test_agents_list_assignment(self):
        """Test that agents list is properly assigned and accessible."""
        test_agents = [
            {"agent": "agent1", "condition": "condition1"},
            {"agent": "agent2", "condition": "condition2"},
            {"agent": "agent3", "condition": "condition3"},
        ]

        agent = GraphAgent(
            agent_key="list_test",
            condition="Test condition",
            agents=test_agents,
            model="gpt-4o",
        )

        assert agent.agents == test_agents
        assert len(agent.agents) == 3
        assert agent.agents[0]["agent"] == "agent1"
        assert agent.agents[1]["condition"] == "condition2"

    def test_condition_assignment(self):
        """Test that condition string is properly assigned."""
        test_conditions = [
            "Simple condition",
            "Complex condition with {input} placeholder",
            "Multi-line\ncondition\nstring",
        ]

        for condition in test_conditions:
            agent = GraphAgent(
                agent_key="condition_test",
                condition=condition,
                agents=[{"agent": "test", "condition": "test"}],
                model="gpt-4o",
            )
            assert agent.condition == condition

    def test_empty_agents_list(self):
        """Test GraphAgent with empty agents list."""
        agent = GraphAgent(
            agent_key="empty_test",
            condition="Test condition",
            agents=[],
            model="gpt-4o",
        )

        assert agent.agents == []
        assert len(agent.agents) == 0
