# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Azure credential management utilities.

This module provides functions for obtaining Azure credentials based on the
deployment environment (local development vs. production).

Functions:
----------
get_azure_credential() -> DefaultAzureCredential | ManagedIdentityCredential
    Returns the appropriate Azure credential object based on environment.

Usage Example:
--------------
In local development:

    >>> import os
    >>> os.environ["LOCAL_DEVELOPMENT"] = "true"
    >>> from aida.utils.credentials import get_azure_credential
    >>> credential = get_azure_credential()
    >>> # Returns DefaultAzureCredential for local dev
    >>> type(credential).__name__
    'DefaultAzureCredential'

In production (Azure):

    >>> import os
    >>> os.environ["LOCAL_DEVELOPMENT"] = "false"
    >>> from aida.utils.credentials import get_azure_credential
    >>> credential = get_azure_credential()
    >>> # Returns ManagedIdentityCredential for Azure resources
    >>> type(credential).__name__
    'ManagedIdentityCredential'

Authentication Methods (DefaultAzureCredential):
------------------------------------------------
When LOCAL_DEVELOPMENT=true, DefaultAzureCredential attempts authentication
methods in the following order:

1. Environment variables (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_CLIENT_SECRET)
2. Managed Identity (if deployed to Azure)
3. Azure CLI credentials (if logged in via 'az login')
4. Azure PowerShell credentials
5. Interactive browser authentication (as fallback)

Production Deployment:
----------------------
In production, Managed Identity should be configured for the Azure resource
(App Service, Container Instance, VM, etc.) to authenticate to other Azure
services without storing credentials.
"""

import os


def get_azure_credential():
    """
    Returns an Azure credential object based on the LOCAL_DEVELOPMENT environment variable.

    If LOCAL_DEVELOPMENT is set to "true" (case-insensitive), returns a DefaultAzureCredential instance,
    which is suitable for local development and supports multiple authentication methods.
    Otherwise, returns a ManagedIdentityCredential instance, which is intended for use in production environments
    where managed identity is available.

    Returns:
        DefaultAzureCredential or ManagedIdentityCredential: The appropriate Azure credential object.
    """
    from azure.identity import DefaultAzureCredential, ManagedIdentityCredential

    if os.getenv("LOCAL_DEVELOPMENT", "false").lower() == "true":
        # Use DefaultAzureCredential for local development; it attempts multiple authentication methods including environment variables, managed identity, Azure CLI, etc.
        credential = DefaultAzureCredential()  # CodeQL [SM05139] Okay use of DefaultAzureCredential as it is only used in development
    else:
        credential = ManagedIdentityCredential()
    return credential
