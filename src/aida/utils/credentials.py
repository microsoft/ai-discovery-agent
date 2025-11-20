# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

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
        credential = (
            DefaultAzureCredential()
        )  # CodeQL [SM05139] Okay use of DefaultAzureCredential as it is only used in development
    else:
        credential = ManagedIdentityCredential()
    return credential
