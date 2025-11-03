# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Cached prompt file loader utility.

This module provides caching functionality for loading prompt files and creating
initial message structures for AI agents. It uses Chainlit's caching mechanism
to optimize file loading performance.

Functions:
----------
load_prompt_files : Cached function to load persona and document files
"""

from pathlib import Path

import chainlit as cl

from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)

BASE_PATH = Path(__file__).parent.parent


@cl.cache
def load_prompt_files(
    persona_file_path: str,
    content_file_paths: str | frozenset[str] | None = None,
) -> list[str]:
    """
    Cached function to load content from prompt files and create initial messages.

    This function uses Chainlit's caching mechanism to avoid reloading files
    on every function call. The cache persists for the duration of the session
    and significantly improves performance when repeatedly accessing the same files.

    This function reads a persona file and optional content files to create
    a list of system messages. It automatically adds guardrails from the
    guardrails.md file and handles multiple content files.

    Parameters:
    -----------
    persona_file_path : str
        Path to the persona/system prompt file.
    content_file_paths : Optional[Union[str, frozenset[str]]], optional
        Path to a single content/context file, or a list of file paths.
        If None, only the persona prompt will be loaded.
        It is important that the list is frozen to ensure immutability
        and proper caching behavior.

    Returns:
    --------
    List[str]
        List of message objects with the system prompts loaded.

    Raises:
    -------
    FileNotFoundError
        If the persona file or any content file cannot be found.
    PermissionError
        If file access is denied.
    UnicodeDecodeError
        If file encoding is incompatible.
    """
    logger.debug("Loading system messages from persona file: %s", persona_file_path)
    # Read the persona file
    with open(BASE_PATH / persona_file_path, encoding="utf-8") as f:
        system_prompt = f.read()
    logger.info("Adding guardrails to system prompt")
    # Add security instructions to the system prompt
    with open(BASE_PATH / "prompts/guardrails.md", encoding="utf-8") as f:
        system_prompt += f.read()

    messages = [system_prompt]

    # Handle content file(s)
    if content_file_paths:
        # Convert single string to frozenset for uniform handling
        if isinstance(content_file_paths, str):
            file_paths_to_process = frozenset([content_file_paths])
        else:
            file_paths_to_process = content_file_paths

        # Process each content file
        for file_path in file_paths_to_process:
            try:
                logger.debug("Loading content from file: %s", file_path)
                with open(BASE_PATH / file_path, encoding="utf-8") as f:
                    system_document = f.read()
                    messages.append(f"\n<documents>{system_document}</documents>")
            except (FileNotFoundError, PermissionError, UnicodeDecodeError) as e:
                logger.exception("Error loading document file %s: %s", file_path, e)

    return messages
