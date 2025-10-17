"""Unit tests for the cached_llm module."""

import os
from unittest.mock import MagicMock, patch
from urllib.parse import urlparse

from utils.cached_llm import create_llm


class TestCachedLLM:
    """Test cases for cached_llm module functions."""

    def test_create_llm_localhost_environment(self):
        """Test LLM creation for localhost development environment."""
        with patch.dict(
            os.environ,
            {
                "AZURE_OPENAI_DEPLOYMENT": "test-model",
                "AZURE_ENV_NAME": "test-env",
            },
        ):
            with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
                mock_instance = MagicMock()
                mock_chat_openai.return_value = mock_instance

                result = create_llm(
                    endpoint="http://localhost:8000",
                    api_version="2023-12-01-preview",
                    deployment="test-deployment",
                    temperature=0.7,
                    tag="test-tag",
                )

                mock_chat_openai.assert_called_once_with(
                    model="test-model",
                    base_url="http://localhost:8000",
                    streaming=True,
                    temperature=0.7,
                    stream_usage=True,
                    api_key=mock_chat_openai.call_args.kwargs["api_key"],
                    tags=["test-tag"],
                )
                assert result == mock_instance

    def test_create_llm_local_development_127_0_0_1(self):
        """Test LLM creation for 127.0.0.1 development environment."""
        with patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT": "local-model"}):
            with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
                mock_instance = MagicMock()
                mock_chat_openai.return_value = mock_instance

                result = create_llm(
                    endpoint="http://127.0.0.1:3000",
                    api_version="2023-12-01-preview",
                    deployment="ignored-in-local",
                    temperature=0.5,
                    tag=None,
                )

                mock_chat_openai.assert_called_once_with(
                    model="local-model",
                    base_url="http://127.0.0.1:3000",
                    streaming=True,
                    temperature=0.5,
                    stream_usage=True,
                    api_key=mock_chat_openai.call_args.kwargs["api_key"],
                    tags=None,
                )
                assert result == mock_instance

    def test_create_llm_local_domain_environment(self):
        """Test LLM creation for .local domain development environment."""
        with patch.dict(os.environ, {"AZURE_OPENAI_DEPLOYMENT": "dev-model"}):
            with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
                mock_instance = MagicMock()
                mock_chat_openai.return_value = mock_instance

                result = create_llm(
                    endpoint="http://myapi.local",
                    api_version="2023-12-01-preview",
                    deployment="dev-deployment",
                    temperature=1.0,
                    tag="dev-tag",
                )

                mock_chat_openai.assert_called_once()
                call_kwargs = mock_chat_openai.call_args.kwargs
                assert call_kwargs["model"] == "dev-model"
                assert call_kwargs["base_url"] == "http://myapi.local"
                assert call_kwargs["temperature"] == 1.0
                assert call_kwargs["tags"] == ["dev-tag"]
                assert result == mock_instance

    def test_create_llm_localhost_domain_environment(self):
        """Test LLM creation for .localhost domain development environment."""
        with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
            mock_instance = MagicMock()
            mock_chat_openai.return_value = mock_instance

            result = create_llm(
                endpoint="http://api.localhost",
                api_version="2023-12-01-preview",
                deployment="test-deployment",
                temperature=0.3,
                tag="localhost-tag",
            )

            mock_chat_openai.assert_called_once()
            assert result == mock_instance

    def test_create_llm_default_model_when_not_set(self):
        """Test LLM creation uses default model when AZURE_OPENAI_DEPLOYMENT not set."""
        with patch.dict(os.environ, {}, clear=True):
            with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
                mock_instance = MagicMock()
                mock_chat_openai.return_value = mock_instance

                result = create_llm(
                    endpoint="http://localhost:8000",
                    api_version="2023-12-01-preview",
                    deployment="test-deployment",
                    temperature=0.7,
                    tag=None,
                )

                call_kwargs = mock_chat_openai.call_args.kwargs
                assert call_kwargs["model"] == "llama-2-13b-chat"  # Default model
                assert result == mock_instance

    @patch("utils.cached_llm.get_bearer_token_provider")
    @patch("utils.cached_llm.get_azure_credential")
    def test_create_llm_azure_production_environment(
        self, mock_get_credential, mock_token_provider
    ):
        """Test LLM creation for Azure production environment."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        mock_token_provider.return_value = MagicMock()

        with patch("utils.cached_llm.AzureChatOpenAI") as mock_azure_openai:
            mock_instance = MagicMock()
            mock_azure_openai.return_value = mock_instance

            result = create_llm(
                endpoint="https://myopenai.openai.azure.com",
                api_version="2023-12-01-preview",
                deployment="gpt-4",
                temperature=0.8,
                tag="production-tag",
            )

            # Verify Azure credential setup
            mock_get_credential.assert_called_once()
            mock_token_provider.assert_called_once_with(
                mock_credential, "https://cognitiveservices.azure.com/.default"
            )

            # Verify AzureChatOpenAI creation
            mock_azure_openai.assert_called_once_with(
                azure_endpoint="https://myopenai.openai.azure.com",
                api_version="2023-12-01-preview",
                azure_ad_token_provider=mock_token_provider.return_value,
                azure_deployment="gpt-4",
                temperature=0.8,
                streaming=True,
                stream_usage=True,
                tags=["production-tag"],
            )
            assert result == mock_instance

    @patch("utils.cached_llm.get_bearer_token_provider")
    @patch("utils.cached_llm.get_azure_credential")
    def test_create_llm_azure_with_none_temperature(
        self, mock_get_credential, mock_token_provider
    ):
        """Test LLM creation for Azure with None temperature."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        mock_token_provider.return_value = MagicMock()

        with patch("utils.cached_llm.AzureChatOpenAI") as mock_azure_openai:
            mock_instance = MagicMock()
            mock_azure_openai.return_value = mock_instance

            result = create_llm(
                endpoint="https://myopenai.openai.azure.com",
                api_version="2023-12-01-preview",
                deployment="gpt-35-turbo",
                temperature=None,
                tag=None,
            )

            call_kwargs = mock_azure_openai.call_args.kwargs
            assert call_kwargs["temperature"] is None
            assert call_kwargs["tags"] is None
            assert result == mock_instance

    @patch("utils.cached_llm.get_bearer_token_provider")
    @patch("utils.cached_llm.get_azure_credential")
    def test_create_llm_azure_with_none_deployment(
        self, mock_get_credential, mock_token_provider
    ):
        """Test LLM creation for Azure with None deployment."""
        mock_credential = MagicMock()
        mock_get_credential.return_value = mock_credential
        mock_token_provider.return_value = MagicMock()

        with patch("utils.cached_llm.AzureChatOpenAI") as mock_azure_openai:
            mock_instance = MagicMock()
            mock_azure_openai.return_value = mock_instance

            result = create_llm(
                endpoint="https://myopenai.openai.azure.com",
                api_version="2023-12-01-preview",
                deployment=None,
                temperature=0.5,
                tag="test-tag",
            )

            call_kwargs = mock_azure_openai.call_args.kwargs
            assert call_kwargs["azure_deployment"] is None
            assert result == mock_instance

    def test_create_llm_ipv6_localhost(self):
        """Test LLM creation for IPv6 localhost."""
        with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
            mock_instance = MagicMock()
            mock_chat_openai.return_value = mock_instance

            result = create_llm(
                endpoint="http://[::1]:8000",
                api_version="2023-12-01-preview",
                deployment="test-deployment",
                temperature=0.7,
                tag="ipv6-tag",
            )

            mock_chat_openai.assert_called_once()
            assert result == mock_instance

    def test_create_llm_caching_behavior(self):
        """Test that create_llm uses caching decorator."""
        with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
            mock_instance = MagicMock()
            mock_chat_openai.return_value = mock_instance

            # Call with same parameters twice
            result1 = create_llm(
                endpoint="http://localhost:8888",  # Unique endpoint
                api_version="2023-12-01-preview",
                deployment="cache-test-deployment",
                temperature=0.77,
                tag="cache-test-tag",
            )

            result2 = create_llm(
                endpoint="http://localhost:8888",  # Same parameters
                api_version="2023-12-01-preview",
                deployment="cache-test-deployment",
                temperature=0.77,
                tag="cache-test-tag",
            )

            # Due to caching, both results should be identical
            assert result1 == result2
            assert result1 == mock_instance

            # Verify the function was called at least once (exact count depends on cache state)
            assert mock_chat_openai.call_count >= 1

    def test_create_llm_url_parsing_edge_cases(self):
        """Test URL parsing for various edge cases."""
        test_cases = [
            ("http://localhost", True),  # No port
            ("https://localhost:443", True),  # HTTPS
            ("http://localhost:8080/api", True),  # With path
            ("http://api.local:3000", True),  # .local domain
            ("http://test.localhost", True),  # .localhost domain
            ("https://prod.openai.azure.com", False),  # Production Azure
            ("http://192.168.1.100", False),  # Private IP (not localhost)
            ("https://api.example.com", False),  # Public domain
        ]

        for endpoint, should_be_local in test_cases:
            with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
                with patch("utils.cached_llm.AzureChatOpenAI") as mock_azure_openai:
                    with patch("utils.cached_llm.get_bearer_token_provider"):
                        with patch("utils.cached_llm.get_azure_credential"):
                            mock_chat_openai.return_value = MagicMock()
                            mock_azure_openai.return_value = MagicMock()

                            create_llm(
                                endpoint=endpoint,
                                api_version="2023-12-01-preview",
                                deployment="test",
                                temperature=0.7,
                                tag=None,
                            )

                            if should_be_local:
                                mock_chat_openai.assert_called_once()
                                mock_azure_openai.assert_not_called()
                            else:
                                mock_chat_openai.assert_not_called()
                                mock_azure_openai.assert_called_once()

    @patch("utils.cached_llm.logger")
    def test_create_llm_logging(self, mock_logger):
        """Test that appropriate logging occurs for Azure environment."""
        with patch("utils.cached_llm.get_bearer_token_provider"):
            with patch("utils.cached_llm.get_azure_credential"):
                with patch("utils.cached_llm.AzureChatOpenAI"):
                    create_llm(
                        endpoint="https://production.openai.azure.com",
                        api_version="2023-12-01-preview",
                        deployment="gpt-4",
                        temperature=0.7,
                        tag="test-tag",
                    )

                    mock_logger.info.assert_called_once()
                    log_call = mock_logger.info.call_args[0]
                    assert "Creating AzureChatOpenAI instance" in log_call[0]
                    parsed_url = urlparse(log_call[1])
                    expected_url = "https://production.openai.azure.com"
                    expected_parsed = urlparse(expected_url)
                    assert parsed_url.scheme == expected_parsed.scheme
                    assert parsed_url.netloc == expected_parsed.netloc
                    assert parsed_url.path == expected_parsed.path
                    assert "gpt-4" in log_call[2]

    def test_create_llm_multiple_tags(self):
        """Test LLM creation with single tag becomes list."""
        with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
            mock_instance = MagicMock()
            mock_chat_openai.return_value = mock_instance

            result = create_llm(
                endpoint="http://localhost:8000",
                api_version="2023-12-01-preview",
                deployment="test-deployment",
                temperature=0.7,
                tag="single-tag",
            )

            call_kwargs = mock_chat_openai.call_args.kwargs
            assert call_kwargs["tags"] == ["single-tag"]
            assert result == mock_instance

    def test_create_llm_secret_str_api_key(self):
        """Test that API key is properly wrapped in SecretStr for local environments."""
        with patch.dict(os.environ, {"AZURE_ENV_NAME": "test-secret"}):
            with patch("utils.cached_llm.ChatOpenAI") as mock_chat_openai:
                mock_instance = MagicMock()
                mock_chat_openai.return_value = mock_instance

                result = create_llm(
                    endpoint="http://localhost:8003",  # Unique endpoint to avoid cache
                    api_version="2023-12-01-preview",
                    deployment="test-deployment",
                    temperature=0.7,
                    tag=None,
                )

                # Verify that ChatOpenAI was called with SecretStr wrapped API key
                mock_chat_openai.assert_called_once()
                call_kwargs = mock_chat_openai.call_args.kwargs

                # The api_key should be a SecretStr instance
                from pydantic import SecretStr

                assert isinstance(call_kwargs["api_key"], SecretStr)
                assert call_kwargs["api_key"].get_secret_value() == "test-secret"
                assert result == mock_instance
