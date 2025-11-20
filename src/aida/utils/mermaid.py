# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import re


def extract_mermaid(response: str) -> list[str]:
    """
    Extract mermaid code blocks from the response string.

    This function parses markdown-formatted text to identify and extract
    mermaid diagram definitions enclosed in ```mermaid code blocks.

    Parameters:
    -----------
    response : str
        The response string containing mermaid code blocks

    Returns:
    --------
    list[str]
        A list of mermaid code blocks extracted from the response

    Examples:
    ---------
    >>> text = "```mermaid\\ngraph TD\\nA-->B\\n```"
    >>> diagrams = extract_mermaid(text)
    >>> len(diagrams)
    1
    """
    mermaid_codes: list[str] = []
    lines = response.split("\n")
    in_mermaid_block = False
    current_code: list[str] = []
    for line in lines:
        if re.match(r"^``` ?mermaid$", line.strip()):
            in_mermaid_block = True
            current_code = []
        elif line.strip().startswith("```") and in_mermaid_block:
            in_mermaid_block = False
            if current_code:
                mermaid_codes.append("\n".join(current_code))
        elif in_mermaid_block:
            current_code.append(line)
    if in_mermaid_block and current_code:
        # If we reach the end of the response while still in a mermaid block
        mermaid_codes.append("\n".join(current_code))
    return mermaid_codes
