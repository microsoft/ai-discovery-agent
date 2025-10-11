# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
agent.py

This module defines the base Agent class for implementing conversational agents
that interact with Azure OpenAI services via LangGraph workflows. This replaces
direct Azure OpenAI API calls with LangGraph-based chat workflows while maintaining
backward compatibility.

MIGRATION NOTE: This module has been refactored to use LangGraph and LangChain's
AzureChatOpenAI instead of direct openai.AzureOpenAI client usage. The interface
remains the same for backward compatibility with existing code.

Classes:
---------
Agent
    Base class for agent implementations, now using LangGraph workflows for
    chat completion instead of direct Azure OpenAI API calls.

Dependencies:
-------------
- os
- typing (Dict, List)
- workflows.chat_graph (LangGraph implementation)
- streamlit
- streamlit.logger
"""

import abc
import os
from collections.abc import AsyncIterator
from typing import Any

from langchain.schema.runnable.config import RunnableConfig
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage
from langchain_core.runnables import Runnable
from langchain_openai import AzureChatOpenAI

from utils.cached_llm import create_llm
from utils.logging_setup import get_logger

AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-04-01-preview")

logger = get_logger(__name__)


class Agent(abc.ABC):
    """
    This abstract base class provides a foundation for building conversational AI agents
    that utilize LangGraph for workflow management and Azure OpenAI for language model
    interactions. It handles the core infrastructure for message processing, chain creation,
    and streaming responses.

    The class has been migrated from direct OpenAI client usage to LangChain's AzureChatOpenAI
    integration while maintaining backward compatibility with existing interfaces.

    Attributes
        Unique identifier for the agent instance.
        The Azure OpenAI model deployment name to use for this agent.
        Defaults to "gpt-4o" if not specified.
        The temperature parameter for controlling response randomness.
        Higher values (e.g., 1.0) make output more random, lower values (e.g., 0.0)
        make it more deterministic. Defaults to 1.0 if not specified.
    _llm : Optional[AzureChatOpenAI]
        Private cached instance of the Azure OpenAI chat model.
        Initialized lazily on first use.
    _chain : Optional[Runnable]
        Private cached instance of the compiled LangGraph chain.
        Currently unused but reserved for future optimization.

    Methods
    create_chain() -> Runnable
        Abstract method that must be implemented by subclasses to define
        the agent's workflow as a LangGraph chain.
    get_system_prompts() -> List[Dict[str, str]]
        Abstract method that must be implemented by subclasses to provide
        agent-specific system messages.
    astream(messages, config) -> AsyncIterator[Any]
        Asynchronously stream responses from the agent given a conversation history.

    Examples
    >>> class MyAgent(Agent):
    ...     def create_chain(self):
    ...         # Define custom workflow
    ...         pass
    ...     def get_system_prompts(self):
    ...         return [{"role": "system", "content": "You are a helpful assistant."}]
    >>>
    >>> agent = MyAgent("my-agent", "gpt-4o", 0.7)
    >>> async for chunk in agent.astream(messages, config):
    ...     print(chunk)

    - Subclasses must implement both `create_chain()` and `get_system_prompts()` methods.
    - The agent relies on environment-configured Azure OpenAI credentials.
    - Message format follows the standard OpenAI conversation structure with
      'role' and 'content' keys.
    """

    def __init__(
        self, agent_key: str, model: str | None, temperature: float | None
    ) -> None:
        """
        Initialize an Agent with configurable settings.

        Parameters:
        -----------
        agent_key : str
            Unique identifier for the agent.
        model : str, optional
            The model to use for this agent. Defaults to "gpt-4o".
        temperature : float, optional
            The temperature setting for response generation. Defaults to 1.
        """
        self.agent_key = agent_key
        self.model = model
        self.temperature = temperature
        self._llm: AzureChatOpenAI | None = None
        self._chain: Runnable | None = None

    def _get_azure_chat_openai(self, tag: str | None = None) -> AzureChatOpenAI:
        """
        This method implements lazy initialization of the Azure OpenAI chat model.
        If the instance doesn't exist, it creates one using the provided configuration
        parameters and caches it for subsequent calls.

        Parameters
        ----------
        tag : Optional[str], default=None
            Optional tag to associate with the LLM instance for tracking or
            identification purposes.

        Returns
        -------
            Configured Azure OpenAI chat model instance. Returns the cached
            instance if it already exists, otherwise creates a new one.

        Notes
        -----
        The method uses the following instance attributes:
        - `self.model`: The model name/identifier
        - `self.temperature`: The temperature parameter for response generation
        - `self._llm`: Cached LLM instance (private attribute)

        The method also relies on the following module-level constants:
        - `AZURE_OPENAI_ENDPOINT`: The Azure OpenAI service endpoint
        - `AZURE_OPENAI_API_VERSION`: The API version to use
        """

        if self._llm is None:
            self._llm = create_llm(
                AZURE_OPENAI_ENDPOINT,
                AZURE_OPENAI_API_VERSION,
                self.model,
                self.temperature,
                tag,
            )

        return self._llm

    @abc.abstractmethod
    def create_chain(self) -> Runnable:
        """
        Create and return a compiled state graph for this agent.

        Returns:
        --------
        RunnableSerializable
            An invocable chain.
        """
        pass

    def _convert_to_langchain_messages(
        self, messages: list[dict[str, str]]
    ) -> list[BaseMessage]:
        """
        Convert message dictionaries to LangChain message format.

        Parameters:
        -----------
        messages : List[Dict[str, str]]
            List of message dictionaries with 'role' and 'content' keys.

        Returns:
        --------
        List[BaseMessage]
            List of LangChain message objects.
        """
        langchain_messages = []

        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")

            if role == "system":
                langchain_messages.append(SystemMessage(content=content))
            elif role == "user":
                langchain_messages.append(HumanMessage(content=content))
            elif role == "assistant":
                langchain_messages.append(AIMessage(content=content))
            else:
                logger.warning(f"Unknown message role: {role}")
                # Default to human message for unknown roles
                langchain_messages.append(HumanMessage(content=content))

        return langchain_messages

    def astream(
        self, messages: list[dict[str, str]], config: RunnableConfig
    ) -> AsyncIterator[Any]:
        """
        Stream responses asynchronously from the agent chain.
        Args:
            messages: List of message dictionaries containing conversation history.
                Each dictionary should have 'role' and 'content' keys.
            config: Configuration object for the runnable chain execution.
        Returns:
            AsyncIterator[Any]: An async iterator that yields streamed responses
                from the agent chain.
        Raises:
            Exception: If the async LangGraph execution fails. The exception is
                logged before being re-raised.
        Note:
            This method combines system prompts with user messages before streaming
            through the created chain with message streaming mode enabled.
        """
        try:
            # langchain_messages = self._convert_to_langchain_messages(messages)
            chain = self.create_chain()
            full_messages = self.get_system_prompts() + messages

            return chain.astream(
                {"messages": full_messages}, config=config, stream_mode="messages"
            )
        except Exception as e:
            logger.exception(
                "Async LangGraph execution failed, using fallback response: %s", e
            )
            raise e

    @abc.abstractmethod
    def get_system_prompts(self) -> list[SystemMessage]:
        """
        Get the system messages for this agent.

        Returns:
        --------
        List[Dict[str, str]]
            A list of system messages for the agent.
        """
        pass
