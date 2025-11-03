# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Persistence layer for the AI Discovery Workshop Agent.

This module provides conversation storage and management capabilities using Azure Storage,
with support for user privacy, multiple conversations per agent, and automatic conversation titling.
"""

from .azure_storage import AzureStorageManager
from .conversation_manager import ConversationManager

__all__ = ["AzureStorageManager", "ConversationManager"]
