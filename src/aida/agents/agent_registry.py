# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Agent registry for AI Discovery Workshop Agent (unified YAML version)

Loads agent definitions from the unified pages.yaml and provides lookup utilities.

Classes:
---------
Agent:
    Base class for agent implementations.

SingleAgent:
    Implementation of a single agent with one persona.

AgentRegistry:
    A class to manage and retrieve agent definitions from the unified YAML file.

Singletons:
-----------
agent_registry:
    A singleton instance of the AgentRegistry class for global use.
"""

from pathlib import Path

import yaml

from aida.exceptions import (
    AgentConfigurationError,
    AgentNotFoundError,
    ConfigurationError,
)
from aida.utils.logging_setup import get_logger

from .agent import Agent
from .graph_agent import GraphAgent
from .single_agent import SingleAgent

PAGES_FILE = Path.cwd() / "config/pages.yaml"

logger = get_logger(__name__)


class AgentRegistry:
    """
    A registry for managing agent definitions loaded from a unified YAML file.

    Methods:
    --------
    __init__(pages_file):
        Initializes the registry by loading agent definitions from the specified YAML file.

    get(agent_key):
        Retrieves the definition of a specific agent by its key.

    get_agent(agent_key):
        Creates and returns an Agent instance for the specified agent key.

    all():
        Returns all agent definitions as a dictionary.
    """

    def __init__(self, pages_file: Path = PAGES_FILE) -> None:
        """
        Initialize the AgentRegistry by loading agent definitions from the YAML file.

        Parameters:
        -----------
        pages_file : Path, optional
            The path to the YAML file containing agent definitions. Defaults to PAGES_FILE.

        Raises:
        -------
        ConfigurationError:
            If the configuration file is missing, invalid, or cannot be read.
        """
        logger.info("Loading agent definitions from %s", pages_file)

        try:
            if not pages_file.exists():
                error_msg = f"Agent configuration file not found: {pages_file}"
                logger.error(error_msg)
                raise ConfigurationError(error_msg, str(pages_file)) from None

            with open(pages_file, encoding="utf-8") as f:
                try:
                    config = yaml.safe_load(f)
                except yaml.YAMLError as e:
                    error_msg = f"Invalid YAML in agent configuration: {e}"
                    logger.error(error_msg, exc_info=True)
                    raise ConfigurationError(error_msg, str(pages_file)) from e

                if not config:
                    error_msg = "Agent configuration file is empty"
                    logger.error(error_msg)
                    raise ConfigurationError(error_msg, str(pages_file)) from None

                if "agents" not in config:
                    error_msg = "No 'agents' section in configuration"
                    logger.error(error_msg)
                    raise ConfigurationError(error_msg, str(pages_file)) from None

                self._agents = config["agents"]
                logger.info(
                    f"Successfully loaded {len(self._agents)} agent definitions"
                )

        except ConfigurationError:
            # Re-raise our custom exception
            raise
        except OSError as e:
            error_msg = f"Failed to read agent configuration file: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(error_msg, str(pages_file)) from e
        except Exception as e:
            error_msg = f"Unexpected error loading agent configuration: {e}"
            logger.error(error_msg, exc_info=True)
            raise ConfigurationError(error_msg, str(pages_file)) from e

    def get(self, agent_key: str) -> dict | None:
        """
        Retrieve the definition of a specific agent by its key.

        Parameters:
        -----------
        agent_key : str
            The key of the agent to retrieve.

        Returns:
        --------
        dict or None
            The agent definition if found, otherwise None.
        """
        return self._agents.get(agent_key)

    def get_agent(self, agent_key: str) -> Agent | None:
        """
        Create and return an Agent instance for the specified agent key.

        Parameters:
        -----------
        agent_key : str
            The key of the agent to create.

        Returns:
        --------
        Agent or None
            An instance of the appropriate Agent subclass if the key is found,
            otherwise None.

        Raises:
        -------
        AgentNotFoundError:
            If the agent key is not found in the registry.
        AgentConfigurationError:
            If the agent configuration is invalid or missing required fields.
        """

        agent_config = self.get(agent_key)
        if not agent_config:
            logger.warning("Agent key '%s' not found in registry", agent_key)
            raise AgentNotFoundError(agent_key)

        try:
            model = agent_config.get("model", "gpt-4o")
            temperature = agent_config.get("temperature")

            # Determine if it's a single or multi agent based on the config
            if "persona" in agent_config:
                # Single agent
                documents = None
                if "document" in agent_config:
                    documents = agent_config["document"]
                elif "documents" in agent_config:
                    documents = frozenset(agent_config["documents"])

                logger.info(
                    "Creating SingleAgent for key '%s' with model '%s'",
                    agent_key,
                    model,
                )
                return SingleAgent(
                    agent_key=agent_key,
                    persona=agent_config["persona"],
                    model=model,
                    documents=documents,
                    temperature=temperature,
                )
            elif "condition" in agent_config:
                logger.info(
                    "Creating GraphAgent for key '%s' with model '%s'",
                    agent_key,
                    model,
                )
                return GraphAgent(
                    agent_key=agent_key,
                    condition=agent_config["condition"],
                    model=model,
                    temperature=temperature,
                    agents=agent_config.get("agents", []),
                )
            else:
                error_msg = "missing 'persona' or 'condition' field"
                logger.error(
                    "Invalid agent configuration for key '%s': %s",
                    agent_key,
                    error_msg,
                )
                raise AgentConfigurationError(agent_key, error_msg) from None

        except AgentConfigurationError:
            # Re-raise our custom exception
            raise
        except KeyError as e:
            error_msg = f"missing required field: {e}"
            logger.error(
                "Invalid agent configuration for key '%s': %s",
                agent_key,
                error_msg,
                exc_info=True,
            )
            raise AgentConfigurationError(agent_key, error_msg) from e
        except Exception as e:
            error_msg = f"unexpected error: {e}"
            logger.error(
                "Error creating agent for key '%s': %s",
                agent_key,
                error_msg,
                exc_info=True,
            )
            raise AgentConfigurationError(agent_key, error_msg) from e

    def all(self) -> dict:
        """
        Retrieve all agent definitions.

        Returns:
        --------
        dict
            A dictionary of all agent definitions.
        """
        return self._agents


# Singleton instance
agent_registry = AgentRegistry()
