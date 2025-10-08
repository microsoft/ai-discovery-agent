import re


def extract_mermaid(response: str) -> list[str]:
    """
    Extract mermaid code blocks from the response string.
    Parameters:
    -----------
    response : str
        The response string containing mermaid code blocks
    Returns:
    --------
    List[str]
        A list of mermaid code blocks extracted from the response
    """
    mermaid_codes = []
    lines = response.split("\n")
    in_mermaid_block = False
    current_code = []
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
