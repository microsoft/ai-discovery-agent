# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
"""
Agent Manager Module

This module manages agent configurations and provides functionality to load, cache,
and retrieve agent information based on user roles and permissions.

The module loads agent configurations from YAML files and provides:
- Global configuration management for agents and pages
- Role-based agent filtering
- Cached agent extraction for improved performance
- Agent information retrieval

Global Variables:
-----------------
_agents_config : dict[str, Any]
    Global dictionary storing agent configurations
_pages_config : dict[str, Any]
    Global dictionary storing pages configurations
PAGES_CONFIG_FILE : Path
    Path to the pages configuration YAML file

Functions:
----------
load_configurations() -> None
    Load agent and page configurations from YAML files
get_available_agents(user_roles: list[str] | None = None) -> dict[str, dict[str, Any]]
    Get available agents filtered by user roles
get_agent_info(agent_key: str) -> dict[str, Any] | None
    Retrieve configuration information for a specific agent

Notes:
------
- The module uses LRU caching to optimize repeated agent queries
- Admin users have access to all agents including admin-only ones
- Configuration is loaded at module initialization
"""

import functools
from pathlib import Path
from typing import Any

import yaml

from aida.utils.logging_setup import get_logger

PAGES_CONFIG_FILE = Path.cwd() / "config/pages.yaml"

logger = get_logger(__name__)


# Global configuration state (shared across all threads)
_agents_config: dict[str, Any] = {}
_pages_config: dict[str, Any] = {}


def load_configurations() -> None:
    """Load configuration from YAML files."""
    global _agents_config, _pages_config

    try:
        logger.info(f"Loading pages configuration from {PAGES_CONFIG_FILE}")
        with open(PAGES_CONFIG_FILE, encoding="utf-8") as file:
            pages_config = yaml.load(file, Loader=yaml.SafeLoader)
        agents_config = pages_config.get("agents", {})

        # Store in global variables
        _agents_config = agents_config
        _pages_config = pages_config

    except (yaml.YAMLError, FileNotFoundError) as e:
        logger.error(
            f"Error loading pages configuration: {e}", exc_info=e, stack_info=True
        )
        # Store empty configs in global variables
        _agents_config = {}
        _pages_config = {}

    # Clear the cache since the configuration data has changed
    _extract_agents_from_sections.cache_clear()


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

    logger.debug(f"Cache info: {_extract_agents_from_sections.cache_info()}")

    available_agents = _extract_agents_from_sections(tuple(user_roles))

    return available_agents


@functools.lru_cache(maxsize=32)
def _extract_agents_from_sections(
    user_roles: tuple[str, ...],
) -> dict[str, dict[str, Any]]:
    global _agents_config, _pages_config

    is_admin = "admin" in user_roles
    sections = _pages_config.get("sections", {})
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
                    "config": _agents_config.get(agent_key, {}),
                    "default": page_config.get("default", False),
                }
    return available_agents


def get_agent_info(agent_key: str) -> dict[str, Any] | None:
    """Get information about a specific agent."""
    global _agents_config
    if agent_key in _agents_config:
        return _agents_config[agent_key]
    return None


logger.info("Loading agent configurations")
load_configurations()
# Log the number of loaded agents
logger.info(f"Loaded {len(_agents_config)} agents from configuration.")
