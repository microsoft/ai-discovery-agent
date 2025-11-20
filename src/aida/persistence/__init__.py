# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Persistence package for conversation management.

This package provides persistence capabilities for storing and retrieving
conversation history and metadata. It includes implementations for Azure
Storage (Blob Storage and Table Storage) and defines the conversation
management interface.

Modules:
--------
azure_storage : Azure Storage implementation for conversation persistence
conversation_manager : High-level conversation management service

Classes:
--------
AzureStorageManager : Manages conversation storage in Azure Blob Storage
AzureTableManager : Manages conversation metadata in Azure Table Storage
AzureStorageConversationManager : Complete conversation lifecycle management

Usage Example:
--------------
Setting up conversation persistence::

    from aida.persistence.conversation_manager import (
        AzureStorageConversationManager
    )
    from aida.persistence.azure_storage import (
        AzureStorageManager,
        AzureTableManager
    )

    # Initialize storage managers
    blob_manager = AzureStorageManager(
        connection_string="your-connection-string"
    )
    table_manager = AzureTableManager(
        endpoint="https://your-account.table.core.windows.net/"
    )

    # Combine into conversation manager
    storage_manager = blob_manager  # Simplified example
    conv_manager = AzureStorageConversationManager(
        storage_manager=storage_manager,
        openai_client=llm_client  # For title generation
    )

    # Create a new conversation
    conversation_id = await conv_manager.create_conversation(
        user_id="user123",
        agent_key="facilitator"
    )

    # Save conversation messages
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi! How can I help?"}
    ]
    await conv_manager.save_conversation(
        user_id="user123",
        agent_key="facilitator",
        conversation_id=conversation_id,
        messages=messages
    )

    # List user's conversations
    conversations = await conv_manager.list_conversations(
        user_id="user123",
        agent_key="facilitator"
    )

Features:
---------
- Automatic conversation title generation using Azure OpenAI
- Conversation metadata tracking (message count, timestamps)
- User and agent-scoped conversation organization
- Conversation listing, loading, and deletion
- Integration with Azure Blob Storage and Table Storage

See Also:
---------
- aida.interfaces.ConversationManager : Abstract base class
- Azure Storage documentation : https://docs.microsoft.com/azure/storage/
"""

from .azure_storage import AzureStorageManager
from .conversation_manager import ConversationManager

__all__ = ["AzureStorageManager", "ConversationManager"]
