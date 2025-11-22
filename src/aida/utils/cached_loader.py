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

from aida.exceptions import PromptLoadError
from aida.utils.logging_setup import get_logger

logger = get_logger(__name__)

BASE_PATH = Path.cwd()


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
    PromptLoadError
        If the persona file or any content file cannot be found or loaded.
    """
    logger.debug("Loading system messages from persona file: %s", persona_file_path)

    # Read the persona file
    persona_path = BASE_PATH / persona_file_path
    try:
        if not persona_path.exists():
            error_msg = f"Persona file not found: {persona_file_path}"
            logger.error(error_msg)
            raise PromptLoadError(persona_file_path, "file not found")

        with open(persona_path, encoding="utf-8") as f:
            system_prompt = f.read()

    except FileNotFoundError as e:
        error_msg = f"Persona file not found: {persona_file_path}"
        logger.error(error_msg)
        raise PromptLoadError(persona_file_path, str(e)) from e
    except PermissionError as e:
        error_msg = f"Permission denied reading persona file: {persona_file_path}"
        logger.error(error_msg)
        raise PromptLoadError(persona_file_path, str(e)) from e
    except UnicodeDecodeError as e:
        error_msg = f"Failed to decode persona file: {persona_file_path}"
        logger.error(error_msg)
        raise PromptLoadError(persona_file_path, str(e)) from e
    except OSError as e:
        error_msg = f"OS error reading persona file: {persona_file_path}"
        logger.error(error_msg, exc_info=True)
        raise PromptLoadError(persona_file_path, str(e)) from e

    # Add security instructions to the system prompt
    logger.info("Adding guardrails to system prompt")
    guardrails_path = BASE_PATH / "prompts/guardrails.md"
    try:
        if not guardrails_path.exists():
            logger.warning("Guardrails file not found, skipping")
        else:
            with open(guardrails_path, encoding="utf-8") as f:
                system_prompt += f.read()
    except (FileNotFoundError, PermissionError, UnicodeDecodeError, OSError) as e:
        # Guardrails are important but not critical - log warning and continue
        logger.warning(f"Failed to load guardrails file: {e}")

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
                content_path = BASE_PATH / file_path

                if not content_path.exists():
                    error_msg = f"Document file not found: {file_path}"
                    logger.error(error_msg)
                    raise PromptLoadError(file_path, "file not found")

                with open(content_path, encoding="utf-8") as f:
                    system_document = f.read()
                    messages.append(f"\n<documents>{system_document}</documents>")

            except PromptLoadError:
                # Re-raise our custom exception
                raise
            except FileNotFoundError as e:
                logger.error(f"Document file not found: {file_path}")
                raise PromptLoadError(file_path, str(e)) from e
            except PermissionError as e:
                logger.error(f"Permission denied reading document file: {file_path}")
                raise PromptLoadError(file_path, str(e)) from e
            except UnicodeDecodeError as e:
                logger.error(f"Failed to decode document file: {file_path}")
                raise PromptLoadError(file_path, str(e)) from e
            except OSError as e:
                logger.error(
                    f"OS error reading document file: {file_path}", exc_info=True
                )
                raise PromptLoadError(file_path, str(e)) from e

    logger.info(f"Successfully loaded {len(messages)} prompt messages")
    return messages
