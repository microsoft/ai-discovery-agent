# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Configuration loading utilities for AI Discovery Workshop Agent.
"""

import os
import re
from importlib.metadata import PackageNotFoundError, distribution

import dotenv
from chainlit.secret import random_secret

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)


def setup_auth_secret() -> None:
    """
    Setup authentication secret for Chainlit.

    If CHAINLIT_AUTH_SECRET is not set, generates a random secret and sets it
    in the environment. Attempts to persist the secret to .env file, but
    continues gracefully if the file cannot be written (e.g., read-only
    filesystem or insufficient permissions in a container).
    """
    if not os.getenv("CHAINLIT_AUTH_SECRET"):
        logger.warning(
            "CHAINLIT_AUTH_SECRET is not set. Generating a random secret for authentication."
        )
        secret = random_secret()
        os.environ["CHAINLIT_AUTH_SECRET"] = secret
        try:
            dotenv.set_key(".env", "CHAINLIT_AUTH_SECRET", secret)
            logger.info("Generated and saved CHAINLIT_AUTH_SECRET to .env file")
        except OSError as e:
            logger.warning(
                "Could not persist CHAINLIT_AUTH_SECRET to .env file "
                "(read-only filesystem or insufficient permissions). "
                "The secret is set in memory and will be regenerated on restart. "
                "Set CHAINLIT_AUTH_SECRET as an environment variable for persistence. "
                f"Underlying error: {e}"
            , exc_info=True)


def load_program_info() -> str:
    """
    Load program information from installed package metadata.

    Returns:
    --------
    str
        Formatted program information including name, version, authors, etc.
    """
    program_info = ""
    try:
        # Get the distribution for this package
        dist = distribution("aida")

        # Extract metadata
        metadata = dist.metadata
        name = metadata.get("Name", "Unknown Program")
        version = metadata.get("Version", "N/A")
        summary = metadata.get("Summary", "No description available.")
        author = metadata.get("Author", "N/A")
        author_email = metadata.get("Author-Email", "")
        home_page = metadata.get("Home-Page", "N/A")

        # Format author information
        author_info = author
        if author_email and author != "N/A":
            author_info = f"{author} <{author_email}>"

        # Build program info string
        program_info += f"### {name} version {version}\n"
        program_info += f"- {summary}\n"
        program_info += f"- Author(s): {author_info}\n"
        program_info += f"- Version: {version}\n"
        program_info += f"- Homepage: {home_page}\n"

        # Try to get additional URLs from metadata if available
        project_urls = metadata.get_all("Project-URL") or []
        repository_url = "N/A"
        documentation_url = "N/A"

        for url_line in project_urls:
            if not url_line:
                continue

            # Use regex to flexibly parse label and URL with various separators
            # Matches: "label, url", "label,url", "label: url", "label:url", etc.
            match = re.match(r"^([^,:]+?)\s*[,:]\s*(.+)$", url_line)

            if match:
                try:
                    label, url = match.groups()
                    label = label.strip()
                    url = url.strip()

                    if "repository" in label.lower() or "github" in label.lower():
                        repository_url = url
                    elif "documentation" in label.lower() or "docs" in label.lower():
                        documentation_url = url
                except Exception as e:
                    logger.warning(
                        f"Error processing Project-URL entry: {url_line}. Error: {e}"
                    )
                    continue
            else:
                logger.warning(
                    f"Malformed Project-URL entry: {url_line}. Expected format: 'label, url' or 'label: url'"
                )

        program_info += f"- Repository: {repository_url}\n"
        program_info += f"- Documentation: {documentation_url}\n"

    except PackageNotFoundError:
        logger.error("Package 'aida' not found in installed packages", exc_info=True)
        program_info = "Error: Package not found in installed packages."
    except Exception as e:
        logger.error(
            f"Error retrieving package metadata: {e}", exc_info=True, stack_info=True
        )
        program_info = "Error retrieving program information."

    return program_info
