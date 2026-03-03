# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""Unit tests for the cached_loader module."""

from unittest.mock import mock_open, patch

import pytest

from aida.exceptions import PromptLoadError
from aida.utils.cached_loader import load_prompt_files


class TestCachedLoader:
    """Test cases for cached_loader module functions."""

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_single_file(self, mock_file_open, mock_exists):
        """Test loading a single prompt file."""
        # Setup mock to return different content for persona and guardrails files
        mock_file_open.side_effect = [
            mock_open(read_data="Test persona content").return_value,
            mock_open(read_data="Guardrails content").return_value,
        ]

        result = load_prompt_files("prompts/persona.md")

        assert len(result) == 1
        assert "Test persona content" in result[0]
        assert "Guardrails content" in result[0]
        assert mock_file_open.call_count == 2  # persona + guardrails

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_with_documents_string(self, mock_file_open, mock_exists):
        """Test loading persona with single document as string."""
        mock_file_open.side_effect = [
            mock_open(read_data="Persona content").return_value,
            mock_open(read_data="Guardrails content").return_value,
            mock_open(read_data="Document content").return_value,
        ]

        result = load_prompt_files("prompts/persona.md", "prompts/doc.md")

        assert len(result) == 2
        assert "Persona content" in result[0]
        assert "Guardrails content" in result[0]
        assert "Document content" in result[1]
        assert mock_file_open.call_count == 3  # persona + guardrails + document

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_with_documents_frozenset(
        self, mock_file_open, mock_exists
    ):
        """Test loading persona with multiple documents as frozenset."""
        mock_file_open.side_effect = [
            mock_open(read_data="Persona content").return_value,
            mock_open(read_data="Guardrails content").return_value,
            mock_open(read_data="Document 1 content").return_value,
            mock_open(read_data="Document 2 content").return_value,
        ]

        documents = frozenset(["prompts/doc1.md", "prompts/doc2.md"])
        result = load_prompt_files("prompts/persona.md", documents)

        assert len(result) == 3  # persona+guardrails + doc1 + doc2
        assert "Persona content" in result[0]
        assert "Guardrails content" in result[0]
        # Check that both documents are loaded (order may vary due to frozenset)
        document_contents = [result[1], result[2]]
        assert any("Document 1 content" in content for content in document_contents)
        assert any("Document 2 content" in content for content in document_contents)
        assert mock_file_open.call_count == 4  # persona + guardrails + 2 documents

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_no_documents(self, mock_file_open, mock_exists):
        """Test loading only persona file with no documents."""
        mock_file_open.side_effect = [
            mock_open(read_data="Only persona content").return_value,
            mock_open(read_data="Guardrails content").return_value,
        ]

        result = load_prompt_files("prompts/persona.md", None)

        assert len(result) == 1
        assert "Only persona content" in result[0]
        assert "Guardrails content" in result[0]
        assert mock_file_open.call_count == 2  # persona + guardrails

    @patch("aida.utils.cached_loader.Path.exists", return_value=False)
    def test_load_prompt_files_file_not_found(self, mock_exists):
        """Test handling of file not found error."""
        with pytest.raises(PromptLoadError, match="file not found"):
            load_prompt_files("prompts/nonexistent.md")

    @patch("aida.utils.cached_loader.Path.exists", return_value=False)
    def test_load_prompt_files_read_error(self, mock_exists):
        """Test handling of file read error."""
        with pytest.raises(PromptLoadError, match="file not found"):
            load_prompt_files("prompts/error.md")

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_empty_file(self, mock_file_open, mock_exists):
        """Test loading empty file."""
        mock_file_open.side_effect = [
            mock_open(read_data="").return_value,
            mock_open(read_data="Guardrails content").return_value,
        ]

        result = load_prompt_files("prompts/empty.md")

        assert len(result) == 1
        assert "Guardrails content" in result[0]
        assert mock_file_open.call_count == 2

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_whitespace_only_file(self, mock_file_open, mock_exists):
        """Test loading file with only whitespace."""
        mock_file_open.side_effect = [
            mock_open(read_data="   \n\t  \n  ").return_value,
            mock_open(read_data="Guardrails content").return_value,
        ]

        result = load_prompt_files("prompts/whitespace.md")

        assert len(result) == 1
        assert "   \n\t  \n  " in result[0]  # Should preserve whitespace
        assert "Guardrails content" in result[0]

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_utf8_encoding(self, mock_file_open, mock_exists):
        """Test that files are read with UTF-8 encoding."""
        mock_file_open.side_effect = [
            mock_open(read_data="Content with unicode: 🚀 ñ é").return_value,
            mock_open(read_data="Guardrails content").return_value,
        ]

        result = load_prompt_files("prompts/unicode.md")

        assert len(result) == 1
        assert "Content with unicode: 🚀 ñ é" in result[0]
        # Verify encoding parameter is passed
        mock_file_open.assert_any_call(
            mock_file_open.call_args_list[0][0][0], encoding="utf-8"
        )

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_empty_documents_frozenset(
        self, mock_file_open, mock_exists
    ):
        """Test loading with empty frozenset of documents."""
        mock_file_open.side_effect = [
            mock_open(read_data="Persona only").return_value,
            mock_open(read_data="Guardrails content").return_value,
        ]

        result = load_prompt_files("prompts/persona.md", frozenset())

        assert len(result) == 1
        assert "Persona only" in result[0]
        assert "Guardrails content" in result[0]
        assert mock_file_open.call_count == 2

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_document_format(self, mock_file_open, mock_exists):
        """Test that documents are wrapped in <documents> tags."""
        mock_file_open.side_effect = [
            mock_open(read_data="Persona content").return_value,
            mock_open(read_data="Guardrails content").return_value,
            mock_open(read_data="Document content").return_value,
        ]

        result = load_prompt_files("prompts/persona.md", "prompts/doc.md")

        assert len(result) == 2
        assert "<documents>Document content</documents>" in result[1]

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open")
    def test_load_prompt_files_guardrails_read_error(
        self, mock_file_open, mock_exists
    ):
        """Test that a guardrails file read error raises PromptLoadError."""
        mock_file_open.side_effect = [
            mock_open(read_data="Persona content").return_value,  # persona
            PermissionError("Permission denied"),  # guardrails read error
        ]

        with pytest.raises(PromptLoadError, match="guardrails"):
            load_prompt_files("prompts/persona_guardrails_read_error.md")

    @patch(
        "aida.utils.cached_loader.Path.exists", side_effect=[True, False]
    )
    @patch("aida.utils.cached_loader.open", new_callable=mock_open)
    def test_load_prompt_files_guardrails_not_found(
        self, mock_file_open, mock_exists
    ):
        """Test that a missing guardrails file raises PromptLoadError."""
        mock_file_open.return_value = mock_open(read_data="Persona content").return_value

        with pytest.raises(PromptLoadError, match="guardrails"):
            load_prompt_files("prompts/persona_guardrails_not_found.md")

    @patch("aida.utils.cached_loader.Path.exists", return_value=True)
    @patch("aida.utils.cached_loader.open")
    def test_load_prompt_files_document_load_error_handling(
        self, mock_file_open, mock_exists
    ):
        """Test that document loading errors raise exceptions."""
        # First two opens succeed (persona, guardrails), third fails (document)
        mock_file_open.side_effect = [
            mock_open(read_data="Persona content").return_value,  # persona
            mock_open(read_data="Guardrails content").return_value,  # guardrails
            FileNotFoundError("Document not found"),  # document error
        ]

        # Should raise our custom exception
        with pytest.raises(PromptLoadError):
            load_prompt_files("prompts/persona.md", "prompts/missing.md")
