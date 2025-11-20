# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
graph_agent.py

This module defines the GraphAgent class, an implementation of a decision tree agent
with conditional routing capabilities for use in conversational AI applications.
The GraphAgent evaluates incoming messages against a condition prompt and routes
them to appropriate sub-agents based on the evaluation result.

Classes:
--------
AgentState : TypedDict
    State definition for tracking input, decision, output, and messages.
GraphAgent : Agent
    Implements a graph-based agent with conditional routing to sub-agents.

Usage Example:
--------------
Creating and using a GraphAgent for intelligent routing:

    >>> from aida.agents.graph_agent import GraphAgent
    >>> from langchain_core.runnables import RunnableConfig
    >>> 
    >>> # Define routing configuration
    >>> routing_config = {
    ...     "agent_key": "smart_router",
    ...     "condition": "Analyze the user query and determine if it's technical, business, or general",
    ...     "agents": [
    ...         {"agent": "technical_expert", "condition": "technical"},
    ...         {"agent": "business_expert", "condition": "business"},
    ...         {"agent": "general_assistant", "condition": "general"}
    ...     ],
    ...     "model": "gpt-4o",
    ...     "temperature": 0.5
    ... }
    >>> 
    >>> # Create the graph agent
    >>> router = GraphAgent(
    ...     agent_key=routing_config["agent_key"],
    ...     condition=routing_config["condition"],
    ...     agents=routing_config["agents"],
    ...     model=routing_config["model"],
    ...     temperature=routing_config["temperature"]
    ... )
    >>> 
    >>> # Use the agent - it will automatically route to the appropriate sub-agent
    >>> messages = [{"role": "user", "content": "How do I optimize database queries?"}]
    >>> config = RunnableConfig()
    >>> async for chunk in router.astream(messages, config):
    ...     # The router will direct this to the technical_expert
    ...     print(chunk)

Workflow:
---------
1. The GraphAgent evaluates the input using the condition prompt
2. Based on the evaluation, it selects the appropriate sub-agent
3. The selected sub-agent processes the request
4. The response is returned to the user

Note:
-----
- All sub-agents must be registered in the agent_registry before use
- The condition prompt should guide the LLM to output one of the condition values
- GraphAgent itself doesn't have system prompts - it delegates to sub-agents

Dependencies:
-------------
- langchain_core: For message handling and prompt templates
- langgraph: For state graph workflow construction
"""

from collections.abc import Hashable, Sequence
from typing import Annotated, Any, TypedDict, cast

from langchain_core.messages import BaseMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable
from langgraph.graph import END, StateGraph
from langgraph.graph.message import add_messages

from aida.utils.logging_setup import get_logger

from .agent import Agent

logger = get_logger(__name__)


class AgentState(TypedDict):
    """
    State definition for the graph agent workflow.

    This state tracks the input, decision routing, output, and conversation
    messages throughout the graph agent's decision tree execution.

    Attributes:
    -----------
    input : str
        The original input text that triggered the agent evaluation.
    output : str
        The final output or response from the selected agent.
    decision : str
        The routing decision made by the condition evaluation.
    messages : Annotated[Sequence[BaseMessage], add_messages]
        List of conversation messages with automatic message addition functionality.
    """

    input: str
    output: str
    decision: str
    messages: Annotated[Sequence[BaseMessage], add_messages]


class GraphAgent(Agent):
    """
    Implementation of a graph-based decision tree agent with conditional routing capabilities.

    This agent uses a condition prompt to evaluate incoming messages and route them to
    different sub-agents based on the evaluation result. It creates a LangGraph workflow
    with conditional edges to implement the decision logic.
    """

    def __init__(
        self,
        agent_key: str,
        condition: str,
        agents: list[dict[str, str]],
        model: str | None,
        temperature: float | None = 0.7,
    ) -> None:
        """
        Initialize a GraphAgent with conditional routing capabilities.

        Parameters:
        -----------
        agent_key : str
            Unique identifier for the agent.
        condition : str
            The condition prompt used to evaluate incoming messages and determine routing.
        agents : List[Dict[str, str]]
            List of agent configurations containing agent keys and their conditions.
        model : str, optional
            The model to use for this agent. Defaults to "gpt-4o".
        temperature : float, optional
            The temperature setting for response generation. Defaults to 0.7.
        """
        super().__init__(agent_key, model, temperature)
        self.condition = condition
        self.agents = agents

    def get_system_prompts(self) -> list[SystemMessage]:
        """
        Get the system messages for this graph agent.

        Note: GraphAgent doesn't have its own system messages as it routes to other agents.

        Returns:
        --------
        List[Dict[str, str]]
            An empty list as graph agents don't have system messages.
        """
        return []

    def _agent_node(self, state: AgentState) -> dict[str, Any]:
        """
        Execute a specific agent based on the decision made in the start node.

        Parameters:
        -----------
        state : AgentState
            Current state containing the decision and conversation context.

        Returns:
        --------
        Dict[str, Any]
            Updated state with the selected agent's response.

        Raises:
        -------
        ValueError
            If the requested agent is not found in the registry.
        """
        from . import agent_registry

        agent = agent_registry.get_agent(state["decision"])
        if agent is None:
            logger.error(
                f"Agent {state['decision']} not found in registry.", stack_info=True
            )
            raise ValueError(f"Agent {state['decision']} not found in registry.")

        # Convert system prompts to BaseMessage objects
        system_messages = agent.get_system_prompts()
        messages = system_messages + list(state["messages"])
        chain = agent.create_chain()
        msg = chain.invoke({"messages": messages}, stream_mode="messages")
        return {"output": msg}

    def _start_agent(self, state: AgentState) -> dict[str, Any]:
        """
        Evaluate the condition and determine which agent should handle the request.

        This method uses the condition prompt to analyze the input and make a routing decision.
        It extracts the input from the state and sends it to the condition evaluation prompt.

        Parameters:
        -----------
        state : AgentState
            Current state containing either 'input' or conversation messages.

        Returns:
        --------
        Dict[str, Any]
            Updated state with 'decision' (agent to route to) and 'input' (processed input).
        """
        start_prompt = ChatPromptTemplate.from_messages([("system", self.condition)])
        chain = start_prompt | self._get_azure_chat_openai()
        input_text = state["input"] if "input" in state else ""

        # if input_text is empty, we can use the last messages from the conversation up to maximum 5 messages
        if not input_text and "messages" in state:
            messages = state["messages"][-6:]
            input_text = " ".join(
                [
                    (
                        f"{str(msg.type)}: {str(msg.content)}\n"
                        if isinstance(msg, BaseMessage)
                        else ""
                    )
                    for msg in messages
                ]
            )

        response = chain.invoke({"input": input_text})
        # take the decision from the response - handle both string and complex responses
        if hasattr(response, "content") and isinstance(response.content, str):
            decision = response.content.strip().lower()
        elif hasattr(response, "content") and isinstance(response.content, list):
            # Handle case where content might be a list
            decision = (
                str(response.content[0] if response.content else "").strip().lower()
            )
        else:
            decision = str(response).strip().lower()

        output = f"Agent decision: {decision}"

        # Return the response for the next agent (decision and input required from the Agent State)
        return {
            "decision": decision,
            "input": input_text,
            "messages": state["messages"],
            "output": output,
        }

    def create_chain(self) -> Runnable:
        """
        Create and return a compiled state graph for this agent.

        Returns:
        --------
        CompiledStateGraph
            A compiled state graph representing the agent's workflow.
        """
        if self._chain is None:
            try:
                # Create the Workflow as StateGraph using the AgentState
                workflow = StateGraph(AgentState)
                # Add the nodes (start_agent, stock_agent, rag_agent)
                workflow.add_node("start", self._start_agent)
                decisions: dict[str, str] = {}
                for agent in self.agents:
                    workflow.add_node(
                        agent["agent"],
                        self._agent_node,
                        metadata={"agent_key": agent},
                    )
                    # Add the final edges to the END node
                    workflow.add_edge(agent["agent"], END)
                    decisions[agent["agent"]] = agent["condition"]

                # Add the conditional edge from start -> lamba (decision) -> defined agents
                # Cast to dict[Hashable, str] to satisfy mypy type checking
                workflow.add_conditional_edges(
                    "start",
                    lambda x: x["decision"],
                    cast(dict[Hashable, str], decisions),
                )
                # Set the workflow entry point
                workflow.set_entry_point("start")
                # Compile the workflow
                self._chain = workflow.compile()

            except Exception as e:
                logger.error(
                    f"Failed to create ConditionGraph: {e}", exc_info=e, stack_info=True
                )
                raise

        return self._chain
