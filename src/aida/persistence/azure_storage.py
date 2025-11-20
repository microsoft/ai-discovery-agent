# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Azure Storage implementation for conversation persistence.

This module provides secure, user-private conversation storage using Azure Blob Storage
with proper encryption and access controls.

Supports two authentication modes:
1. Connection string (AZURE_STORAGE_CONNECTION_STRING or passed directly)
2. Managed Identity / AAD (when AZURE_STORAGE_ACCOUNT_URL is set and no connection string is provided)
"""

import json
import os
from datetime import UTC, datetime
from typing import Any

from azure.core.exceptions import (
    AzureError,
    ClientAuthenticationError,
    ResourceExistsError,
    ResourceNotFoundError,
    ServiceRequestError,
)
from azure.storage.blob import ContentSettings
from azure.storage.blob.aio import BlobServiceClient  # Updated to async client

from aida.exceptions import (
    ConversationNotFoundError,
    StorageAccessError,
    StorageError,
)
from aida.utils.credentials import get_azure_credential
from aida.utils.logging_setup import get_logger, get_structured_logger

logger = get_logger(__name__)


class AzureStorageManager:
    """
    Manages conversation storage in Azure Blob Storage with user privacy controls.

    Features:
    - User-scoped blob containers for privacy isolation
    - Encrypted conversation data storage
    - Automatic blob naming and organization
    - Conversation metadata management
    """

    def __init__(
        self,
        connection_string: str | None = None,
        container_prefix: str = "conversations",
    ):
        """
        Initialize Azure Storage manager.

        Args:
            connection_string: Azure Storage connection string. If None, attempts managed identity.
            container_prefix: Prefix for conversation containers.

        Raises:
            ValueError: If neither a connection string nor an account URL is available.
        """
        self.connection_string: str | None = connection_string or os.getenv(
            "AZURE_STORAGE_CONNECTION_STRING"
        )
        self.container_prefix: str = container_prefix

        if self.connection_string and (
            "AccountKey=" in self.connection_string
            or "SharedAccessSignature=" in self.connection_string
        ):
            # Connection string auth path
            self.blob_service_client = BlobServiceClient.from_connection_string(
                self.connection_string
            )
            logger.info(
                "AzureStorageManager initialized with connection string authentication."
            )
        else:
            # Managed identity / AAD path
            account_url = os.getenv("AZURE_STORAGE_ACCOUNT_URL")
            if not account_url:
                raise ValueError(
                    "Azure Storage configuration missing. Provide AZURE_STORAGE_CONNECTION_STRING "
                    "or set AZURE_STORAGE_ACCOUNT_URL for managed identity."
                )
            credential = get_azure_credential()
            self.blob_service_client = BlobServiceClient(
                account_url=account_url, credential=credential
            )
            logger.info(
                f"AzureStorageManager initialized with {type(credential).__name__}."
            )

    def _get_user_container_name(self, user_id: str) -> str:
        """
        Generate container name for user conversations.

        Args:
            user_id: User identifier

        Returns:
            Container name following Azure naming conventions
        """
        # Azure container names must be lowercase and contain only letters, numbers, and hyphens
        safe_user_id = (
            user_id.lower().replace("_", "-").replace("@", "-at-").replace(".", "-")
        )
        return f"{self.container_prefix}-{safe_user_id}"

    def _get_conversation_blob_name(self, agent_key: str, conversation_id: str) -> str:
        """
        Generate blob name for a specific conversation.

        Args:
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            Blob name for the conversation
        """
        return f"{agent_key}/{conversation_id}.json"

    async def _ensure_container_exists(self, container_name: str) -> None:
        """
        Ensure user container exists with proper security settings.

        Args:
            container_name: Name of the container to create/verify.

        Raises:
            StorageAccessError: If container creation or access fails.
        """
        try:
            container_client = self.blob_service_client.get_container_client(
                container_name
            )
            try:
                # Check if container exists by trying to get properties
                await container_client.get_container_properties()
                logger.debug(f"Container {container_name} already exists")
            except ResourceNotFoundError:
                # Container doesn't exist, create it with private access
                logger.info(f"Creating new private container: {container_name}")
                await container_client.create_container(public_access=None)
                logger.info(f"Successfully created private container: {container_name}")
        except ResourceExistsError:
            # Container was created by another concurrent request
            logger.debug(f"Container {container_name} was created concurrently")
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed for container {container_name}: {e}"
            logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg)
        except ServiceRequestError as e:
            error_msg = f"Network error accessing container {container_name}: {e}"
            logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg)
        except AzureError as e:
            error_msg = f"Azure Storage error for container {container_name}: {e}"
            logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg)
        except Exception as e:
            error_msg = f"Unexpected error ensuring container {container_name} exists: {e}"
            logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg)

    async def save_conversation(
        self,
        user_id: str,
        agent_key: str,
        conversation_id: str,
        conversation_data: dict[str, Any],
    ) -> bool:
        """
        Save conversation data to Azure Storage.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier
            conversation_data: Conversation data to store

        Returns:
            True if successful, False otherwise

        Raises:
            StorageAccessError: If storage access fails.
        """
        storage_logger = get_structured_logger(
            __name__, user_id=user_id, agent_key=agent_key, conversation_id=conversation_id
        )

        try:
            container_name = self._get_user_container_name(user_id)
            await self._ensure_container_exists(container_name)

            blob_name = self._get_conversation_blob_name(agent_key, conversation_id)

            # Add metadata
            data_with_metadata = {
                "conversation_id": conversation_id,
                "agent_key": agent_key,
                "user_id": user_id,
                "created_at": conversation_data.get(
                    "created_at", datetime.now(UTC).isoformat()
                ),
                "updated_at": datetime.now(UTC).isoformat(),
                **conversation_data,
            }

            # Convert to JSON
            try:
                json_data = json.dumps(data_with_metadata, ensure_ascii=False, indent=2)
            except (TypeError, ValueError) as e:
                error_msg = f"Failed to serialize conversation data: {e}"
                storage_logger.error(error_msg)
                raise StorageError(error_msg, user_id, conversation_id)

            # Upload blob with JSON content type
            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )
            await blob_client.upload_blob(
                json_data,
                overwrite=True,
                content_settings=ContentSettings(content_type="application/json"),
            )

            storage_logger.info("Successfully saved conversation")
            return True

        except (StorageAccessError, StorageError):
            # Re-raise our custom exceptions
            raise
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed while saving conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except ServiceRequestError as e:
            error_msg = f"Network error while saving conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except AzureError as e:
            error_msg = f"Azure Storage error while saving conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except Exception as e:
            error_msg = f"Unexpected error saving conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg, user_id, conversation_id)

    async def load_conversation(
        self, user_id: str, agent_key: str, conversation_id: str
    ) -> dict[str, Any] | None:
        """
        Load conversation data from Azure Storage.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            Conversation data if found, None otherwise

        Raises:
            ConversationNotFoundError: If the conversation doesn't exist.
            StorageAccessError: If storage access fails.
        """
        storage_logger = get_structured_logger(
            __name__, user_id=user_id, agent_key=agent_key, conversation_id=conversation_id
        )

        try:
            container_name = self._get_user_container_name(user_id)
            blob_name = self._get_conversation_blob_name(agent_key, conversation_id)

            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )

            blob_data = await blob_client.download_blob()
            content = await blob_data.readall()

            try:
                conversation_data = json.loads(content.decode("utf-8"))
            except (json.JSONDecodeError, UnicodeDecodeError) as e:
                error_msg = f"Failed to parse conversation data: {e}"
                storage_logger.error(error_msg)
                raise StorageError(error_msg, user_id, conversation_id)

            storage_logger.info("Successfully loaded conversation")
            return conversation_data

        except ResourceNotFoundError:
            storage_logger.debug("Conversation not found")
            raise ConversationNotFoundError(user_id, conversation_id)
        except (ConversationNotFoundError, StorageError):
            # Re-raise our custom exceptions
            raise
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed while loading conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except ServiceRequestError as e:
            error_msg = f"Network error while loading conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except AzureError as e:
            error_msg = f"Azure Storage error while loading conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except Exception as e:
            error_msg = f"Unexpected error loading conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg, user_id, conversation_id)

    async def list_conversations(
        self, user_id: str, agent_key: str | None = None
    ) -> list[dict[str, Any]]:
        """
        List conversations for a user, optionally filtered by agent.

        Args:
            user_id: User identifier
            agent_key: Optional agent filter

        Returns:
            List of conversation metadata

        Raises:
            StorageAccessError: If storage access fails.
        """
        storage_logger = get_structured_logger(
            __name__, user_id=user_id, agent_key=agent_key
        )

        try:
            container_name = self._get_user_container_name(user_id)
            container_client = self.blob_service_client.get_container_client(
                container_name
            )

            conversations = []
            prefix = f"{agent_key}/" if agent_key else ""

            async for blob in container_client.list_blobs(name_starts_with=prefix):
                if blob.name.endswith(".json"):
                    # Extract agent and conversation ID from blob name
                    parts = blob.name.replace(".json", "").split("/")
                    if len(parts) == 2:
                        blob_agent_key, conversation_id = parts
                        conversations.append(
                            {
                                "conversation_id": conversation_id,
                                "agent_key": blob_agent_key,
                                "last_modified": (
                                    blob.last_modified.isoformat()
                                    if blob.last_modified
                                    else None
                                ),
                                "size": blob.size,
                            }
                        )

            # Sort by last modified (newest first)
            conversations.sort(key=lambda x: x["last_modified"] or "", reverse=True)
            storage_logger.info(f"Found {len(conversations)} conversations")
            return conversations

        except ResourceNotFoundError:
            storage_logger.debug("No conversations container found - returning empty list")
            return []
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed while listing conversations: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id)
        except ServiceRequestError as e:
            error_msg = f"Network error while listing conversations: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id)
        except AzureError as e:
            error_msg = f"Azure Storage error while listing conversations: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id)
        except Exception as e:
            error_msg = f"Unexpected error listing conversations: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg, user_id)

    async def delete_conversation(
        self, user_id: str, agent_key: str, conversation_id: str
    ) -> bool:
        """
        Delete a conversation from Azure Storage.

        Args:
            user_id: User identifier
            agent_key: Agent identifier
            conversation_id: Conversation identifier

        Returns:
            True if successful, False otherwise

        Raises:
            ConversationNotFoundError: If the conversation doesn't exist.
            StorageAccessError: If storage access fails.
        """
        storage_logger = get_structured_logger(
            __name__, user_id=user_id, agent_key=agent_key, conversation_id=conversation_id
        )

        try:
            container_name = self._get_user_container_name(user_id)
            blob_name = self._get_conversation_blob_name(agent_key, conversation_id)

            blob_client = self.blob_service_client.get_blob_client(
                container=container_name, blob=blob_name
            )

            await blob_client.delete_blob()
            storage_logger.info("Successfully deleted conversation")
            return True

        except ResourceNotFoundError:
            storage_logger.warning("Conversation not found for deletion")
            raise ConversationNotFoundError(user_id, conversation_id)
        except ClientAuthenticationError as e:
            error_msg = f"Authentication failed while deleting conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except ServiceRequestError as e:
            error_msg = f"Network error while deleting conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except AzureError as e:
            error_msg = f"Azure Storage error while deleting conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageAccessError(error_msg, user_id, conversation_id)
        except Exception as e:
            error_msg = f"Unexpected error deleting conversation: {e}"
            storage_logger.error(error_msg, exc_info=True)
            raise StorageError(error_msg, user_id, conversation_id)
