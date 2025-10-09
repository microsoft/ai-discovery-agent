# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

from pathlib import Path
from typing import Any

import yaml
from yaml import SafeLoader

from utils.logging_setup import get_logger

PAGES_CONFIG_FILE = Path(__file__).parent.parent / "config/pages.yaml"

logger = get_logger(__name__)


class ChainlitAgentManager:
    """
    Manages agent configuration and switching in Chainlit.
    """

    def __init__(self) -> None:
        """Initialize the agent manager."""
        self.agents_config: dict[str, Any] = {}
        self.pages_config: dict[str, Any] = {}
        self.current_agent: str | None = None
        self.load_configurations()

    def load_configurations(self) -> None:
        """Load configuration from YAML files."""
        try:
            with open(PAGES_CONFIG_FILE, encoding="utf-8") as file:
                self.pages_config = yaml.load(file, Loader=SafeLoader)
            self.agents_config = self.pages_config.get("agents", {})
        except (yaml.YAMLError, FileNotFoundError) as e:
            logger.error(
                f"Error loading pages configuration: {e}", exc_info=e, stack_info=True
            )
            self.agents_config = {}
            self.pages_config = {}

    def get_available_agents(
        self, user_roles: list[str] | None = None
    ) -> dict[str, dict[str, Any]]:
        """
        Get available agents based on user roles.

        Parameters:
        -----------
        user_roles : Optional[List[str]]
            List of user roles, defaults to None

        Returns:
        --------
        Dict[str, Dict[str, Any]]
            Dictionary of available agents with their configurations
        """
        is_admin = user_roles and "admin" in user_roles
        available_agents = {}

        sections = self.pages_config.get("sections", {})
        for section_name, pages in sections.items():
            for page_config in pages:
                if page_config.get("type") == "agent":
                    # Skip admin-only pages for non-admins
                    if page_config.get("admin_only", False) and not is_admin:
                        continue

                    agent_key = page_config["agent"]
                    available_agents[agent_key] = {
                        "title": page_config["title"],
                        "icon": page_config["icon"],
                        "header": page_config["header"],
                        "subtitle": page_config["subtitle"],
                        "section": section_name,
                        "config": self.agents_config.get(agent_key, {}),
                        "default": page_config.get("default", False),
                    }

        return available_agents

    def get_agent_info(self, agent_key: str) -> dict[str, Any] | None:
        """Get information about a specific agent."""
        if agent_key in self.agents_config:
            return self.agents_config[agent_key]
        return None

    def set_current_agent(self, agent_key: str) -> bool:
        """
        Set the current active agent.

        Parameters:
        -----------
        agent_key : str
            The key of the agent to set as current

        Returns:
        --------
        bool
            True if agent was set successfully, False otherwise
        """
        if agent_key in self.agents_config:
            self.current_agent = agent_key
            return True
        return False
