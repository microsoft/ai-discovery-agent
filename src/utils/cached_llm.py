# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

import os
from urllib.parse import urlparse

import chainlit as cl
from azure.identity import get_bearer_token_provider
from langchain.chat_models.base import BaseChatModel
from langchain_openai import AzureChatOpenAI, ChatOpenAI
from pydantic import SecretStr

from utils.credentials import get_azure_credential
from utils.logging_setup import get_logger

logger = get_logger(__name__)


@cl.cache
def create_llm(
    endpoint: str,
    api_version: str,
    deployment: str | None,
    temperature: float | None,
    tag: str | None,
) -> BaseChatModel:
    """
    Create an instance of AzureChatOpenAI with Azure AD authentication.

    Args:
        azure_endpoint (str): The Azure OpenAI service endpoint URL.
        api_version (str): The API version to use for the Azure OpenAI service.
        azure_deployment (Optional[str]): The name of the Azure OpenAI deployment.
        temperature (Optional[float]): The sampling temperature to use for text generation.
            Lower values make the output more deterministic.
        tag (Optional[str]): An optional tag to associate with the LLM instance.

    Returns:
        AzureChatOpenAI: A configured instance of AzureChatOpenAI with streaming enabled
            and Azure AD authentication.

    Note:
        This function uses get_azure_credential for authentication, which attempts
        multiple authentication methods in order (environment variables, managed identity,
        Azure CLI, etc.).
    """
    parsed_host = urlparse(endpoint).hostname
    # local development environments
    if (
        parsed_host in {"localhost", "127.0.0.1"}
        or (parsed_host and parsed_host.endswith(".local"))
        or (parsed_host and parsed_host.endswith(".localhost"))
    ):
        # Local model with model override
        model = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "llama-2-13b-chat")
        return ChatOpenAI(
            model=model,
            base_url=endpoint,
            streaming=True,
            temperature=temperature,
            stream_usage=True,
            api_key=SecretStr(
                os.environ.get("AZURE_ENV_NAME", "")
            ),  # used to bypass the api key requirement
            tags=[tag] if tag else None,
        )
    else:
        # Use Azure identity for authentication
        token_provider = get_bearer_token_provider(
            get_azure_credential(), "https://cognitiveservices.azure.com/.default"
        )
        logger.info(
            "Creating AzureChatOpenAI instance with endpoint: %s, deployment: %s",
            endpoint,
            deployment,
        )
        return AzureChatOpenAI(
            azure_endpoint=endpoint,
            api_version=api_version,
            azure_ad_token_provider=token_provider,
            azure_deployment=deployment,
            temperature=temperature,
            streaming=True,
            stream_usage=True,
            tags=[tag] if tag else None,
        )
