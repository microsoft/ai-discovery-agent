"""
Agents package for the AI Discovery Workshop Agent application.

This package provides agent implementations for conversational AI using LangGraph workflows.
It includes base agent classes, specific implementations, and a registry for agent management.

Classes:
--------
Agent : Base abstract class for agent implementations
SingleAgent : Implementation for single-persona agents
GraphAgent : Implementation for graph-based conditional routing agents

Constants:
----------
RESPONSE_TAG : str
    Tag used to identify response messages in LangGraph workflows

Modules:
--------
agent : Base agent class definitions
single_agent : Single agent implementation
graph_agent : Graph agent implementation
agent_registry : Agent registry and factory
"""

# This file makes the agents directory a Python package

from .agent import Agent
from .agent_manager import ChainlitAgentManager
from .agent_registry import agent_registry

RESPONSE_TAG = "response"

__all__ = ["agent_registry", "Agent", "ChainlitAgentManager", "RESPONSE_TAG"]
