# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
OAuth utility functions for handling network timeouts and errors.
"""

import os

import httpx

from utils.logging_setup import get_logger

logger = get_logger(__name__)

# Configure httpx timeouts for OAuth requests
OAUTH_TIMEOUT = httpx.Timeout(
    timeout=30.0,  # Total timeout
    connect=10.0,  # Connection timeout
    read=20.0,     # Read timeout
    write=10.0,    # Write timeout
)

def is_network_restricted_environment() -> bool:
    """
    Detect if we're running in a network-restricted environment.
    
    Returns:
        bool: True if we're likely in a VNet with restricted outbound access
    """
    # Check for Azure App Service indicators
    is_azure_app_service = any([
        os.getenv("WEBSITE_SITE_NAME"),
        os.getenv("WEBSITE_RESOURCE_GROUP"),
        os.getenv("APPSETTING_WEBSITE_SITE_NAME"),
    ])
    
    # Check for VNet integration indicators
    has_vnet_integration = any([
        os.getenv("WEBSITE_VNET_ROUTE_ALL"),
        os.getenv("WEBSITE_DNS_SERVER"),
    ])
    
    return is_azure_app_service and has_vnet_integration

async def test_github_connectivity() -> bool:
    """
    Test if we can reach GitHub's API endpoints.
    
    Returns:
        bool: True if GitHub is reachable, False otherwise
    """
    try:
        async with httpx.AsyncClient(timeout=OAUTH_TIMEOUT) as client:
            response = await client.get("https://api.github.com/zen")
            return response.status_code == 200
    except Exception as e:
        logger.warning(f"GitHub connectivity test failed: {e}")
        return False

def should_disable_oauth() -> bool:
    """
    Determine if OAuth should be disabled due to network restrictions.
    
    Returns:
        bool: True if OAuth should be disabled
    """
    return is_network_restricted_environment()

async def validate_oauth_prerequisites() -> str | None:
    """
    Validate that OAuth can work in the current environment.
    
    Returns:
        Optional[str]: Error message if OAuth won't work, None if it should work
    """
    if is_network_restricted_environment():
        github_reachable = await test_github_connectivity()
        if not github_reachable:
            return (
                "OAuth is disabled: GitHub API is not reachable from this environment. "
                "This is likely due to VNet restrictions. Please use password authentication."
            )

    return None