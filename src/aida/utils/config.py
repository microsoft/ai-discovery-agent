# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Configuration loading utilities for AI Discovery Workshop Agent.
"""

import os
import tomllib
from pathlib import Path

import dotenv
from chainlit.secret import random_secret

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)


def setup_auth_secret() -> None:
    """
    Setup authentication secret for Chainlit.

    If CHAINLIT_AUTH_SECRET is not set, generates a random secret and saves it to .env file.
    """
    if not os.getenv("CHAINLIT_AUTH_SECRET"):
        logger.warning(
            "CHAINLIT_AUTH_SECRET is not set. Authentication will not be secure. Generating a random secret."
        )
        os.environ["CHAINLIT_AUTH_SECRET"] = random_secret()
        dotenv.set_key(
            ".env", "CHAINLIT_AUTH_SECRET", os.environ["CHAINLIT_AUTH_SECRET"]
        )


def load_program_info() -> str:
    """
    Load program information from pyproject.toml.

    Returns:
    --------
    str
        Formatted program information including name, version, authors, etc.
    """
    program_info = ""
    try:
        with open(Path(__file__).parent.parent / "pyproject.toml", "rb") as f:
            info = tomllib.load(f)
            # Extract all fields from the [project] section
            project_info = info.get("project", {})
            program_info += f"### {project_info.get('name', 'Unknown Program')} version {project_info.get('version', 'N/A')}\n"
            program_info += (
                f"- {project_info.get('description', 'No description available.')}\n"
            )
            program_info += f"- Author(s): {', '.join([author.get('name', '') for author in project_info.get('authors', [])])}\n"
            # get version
            program_info += f"- Version: {project_info.get('version', 'N/A')}\n"
            program_info += (
                f"- Homepage: {project_info.get('urls', {}).get('homepage', 'N/A')}\n"
            )
            program_info += f"- Repository: {project_info.get('urls', {}).get('repository', 'N/A')}\n"
            program_info += f"- Documentation: {project_info.get('urls', {}).get('documentation', 'N/A')}\n"
    except Exception as e:
        logger.error(f"Error reading pyproject.toml: {e}", exc_info=e, stack_info=True)
        program_info = "Error retrieving program information."

    return program_info
