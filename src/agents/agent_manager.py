# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import functools
from pathlib import Path
from typing import Any

import yaml
from yaml import SafeLoader

from utils.logging_setup import get_logger

PAGES_CONFIG_FILE = Path(__file__).parent.parent / "config/pages.yaml"

logger = get_logger(__name__)


"""Initialize the agent manager."""
agents_config: dict[str, Any] = {}
pages_config: dict[str, Any] = {}
current_agent: str | None = None


def load_configurations() -> None:
    """Load configuration from YAML files."""
    global agents_config, pages_config
    try:
        logger.info(f"Loading pages configuration from {PAGES_CONFIG_FILE}")
        with open(PAGES_CONFIG_FILE, encoding="utf-8") as file:
            pages_config = yaml.load(file, Loader=SafeLoader)
        agents_config = pages_config.get("agents", {})
    except (yaml.YAMLError, FileNotFoundError) as e:
        logger.error(
            f"Error loading pages configuration: {e}", exc_info=e, stack_info=True
        )
        agents_config = {}
        pages_config = {}


def get_available_agents(
    user_roles: list[str] | None = None,
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
    available_agents = {}

    if user_roles is None:
        user_roles = []

    logger.info(f"Cache info: {_extract_agents_from_sections.cache_info()}")

    available_agents = _extract_agents_from_sections(*user_roles)

    return available_agents


@functools.lru_cache(maxsize=32)
def _extract_agents_from_sections(*args: Any) -> dict[str, dict[str, Any]]:
    is_admin = "admin" in args
    sections = pages_config.get("sections", {})
    available_agents = {}
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
                    "config": agents_config.get(agent_key, {}),
                    "default": page_config.get("default", False),
                }
    return available_agents


def get_agent_info(agent_key: str) -> dict[str, Any] | None:
    """Get information about a specific agent."""
    if agent_key in agents_config:
        return agents_config[agent_key]
    return None


def set_current_agent(agent_key: str) -> bool:
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
    global current_agent
    if agent_key in agents_config:
        current_agent = agent_key
        return True
    return False


logger.info("Loading agent configurations")
load_configurations()
logger.info(f"Loaded {len(agents_config)} agents from configuration.")
