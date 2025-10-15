# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Integration tests for agent manager functionality.

Tests agent configuration loading, switching, and role-based access with real file operations.
"""

import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
import yaml

from tests.fixtures.data import SAMPLE_AGENT_CONFIG


class TestAgentManagerIntegration:
    """Integration tests for agent_manager module."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(SAMPLE_AGENT_CONFIG, f)
            yield f.name
        # Cleanup
        os.unlink(f.name)

    @pytest.fixture(autouse=True)
    def reset_module_state(self):
        """Reset agent_manager module state before each test."""
        # Import here to avoid import at module level
        import agents.agent_manager as agent_manager

        # Store original state from global configuration
        original_agents_config = agent_manager._agents_config.copy()
        original_pages_config = agent_manager._pages_config.copy()
        original_current_agent = agent_manager._get_current_agent_thread_local()

        yield

        # Restore original state to global configuration and thread-local current agent
        agent_manager._agents_config = original_agents_config
        agent_manager._pages_config = original_pages_config
        agent_manager._set_current_agent_thread_local(original_current_agent)

    def test_load_configurations_with_real_file(self, temp_config_file):
        """Test loading configurations from actual file."""
        # Patch the PAGES_CONFIG_FILE constant
        with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)):
            import agents.agent_manager as agent_manager

            # Reload the module by calling load_configurations
            agent_manager.load_configurations()

            # Verify configuration was loaded correctly
            assert agent_manager._pages_config == SAMPLE_AGENT_CONFIG
            assert agent_manager._agents_config == SAMPLE_AGENT_CONFIG["agents"]
            assert "facilitator" in agent_manager._agents_config
            assert "expert" in agent_manager._agents_config

    def test_agent_switching_workflow(self, temp_config_file):
        """Test complete agent switching workflow."""
        with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)):
            import agents.agent_manager as agent_manager

            # Load configuration
            agent_manager.load_configurations()

            # Test initial state
            assert agent_manager.get_current_agent() is None

            # Test switching to facilitator
            success = agent_manager.set_current_agent("facilitator")
            assert success is True
            assert agent_manager.get_current_agent() == "facilitator"

            # Test getting agent info
            agent_info = agent_manager.get_agent_info("facilitator")
            assert agent_info is not None
            assert agent_info["model"] == "gpt-4o"
            assert agent_info["temperature"] == 0.7

            # Test switching to expert
            success = agent_manager.set_current_agent("expert")
            assert success is True
            assert agent_manager.get_current_agent() == "expert"

            # Test switching to non-existent agent
            success = agent_manager.set_current_agent("nonexistent")
            assert success is False
            assert (
                agent_manager.get_current_agent() == "expert"
            )  # Should remain unchanged

    def test_role_based_access_control_workflow(self, temp_config_file):
        """Test complete role-based access control workflow."""
        with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)):
            import agents.agent_manager as agent_manager

            # Load configuration
            agent_manager.load_configurations()

            # Test regular user access
            user_agents = agent_manager.get_available_agents(["user"])
            assert "facilitator" in user_agents
            assert "expert" not in user_agents  # admin_only

            # Test admin user access
            admin_agents = agent_manager.get_available_agents(["admin", "user"])
            assert "facilitator" in admin_agents
            assert "expert" in admin_agents  # admin can access admin_only

            # Test no roles
            no_role_agents = agent_manager.get_available_agents(None)
            assert "facilitator" in no_role_agents
            assert "expert" not in no_role_agents

            # Test empty roles
            empty_role_agents = agent_manager.get_available_agents([])
            assert "facilitator" in empty_role_agents
            assert "expert" not in empty_role_agents


class TestAgentManagerErrorHandling:
    """Test error handling in agent manager."""

    @pytest.fixture(autouse=True)
    def reset_module_state(self):
        """Reset agent_manager module state before each test."""
        import agents.agent_manager as agent_manager

        # Store original state from global configuration
        original_agents_config = agent_manager._agents_config.copy()
        original_pages_config = agent_manager._pages_config.copy()
        original_current_agent = agent_manager._get_current_agent_thread_local()

        yield

        # Restore original state to global configuration and thread-local current agent
        agent_manager._agents_config = original_agents_config
        agent_manager._pages_config = original_pages_config
        agent_manager._set_current_agent_thread_local(original_current_agent)

    def test_missing_config_file(self):
        """Test behavior when config file is missing."""
        with patch(
            "agents.agent_manager.PAGES_CONFIG_FILE", Path("/nonexistent/config.yaml")
        ):
            import agents.agent_manager as agent_manager

            # Load configuration (should handle missing file gracefully)
            agent_manager.load_configurations()

            # Should have empty configs
            assert agent_manager._pages_config == {}
            assert agent_manager._agents_config == {}

            # Clear cache to ensure fresh lookup
            agent_manager._extract_agents_from_sections.cache_clear()

            # Operations should handle empty config gracefully
            agents = agent_manager.get_available_agents(["user"])
            assert agents == {}

            agent_info = agent_manager.get_agent_info("any_agent")
            assert agent_info is None

            success = agent_manager.set_current_agent("any_agent")
            assert success is False

    def test_malformed_config_file(self):
        """Test behavior with malformed YAML config."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML
            f.flush()

            try:
                with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                    import agents.agent_manager as agent_manager

                    # Load configuration (should handle parsing error gracefully)
                    agent_manager.load_configurations()

                    # Should have empty configs due to parsing error
                    assert agent_manager._pages_config == {}
                    assert agent_manager._agents_config == {}
            finally:
                # Cleanup
                os.unlink(f.name)

    def test_incomplete_config_structure(self):
        """Test behavior with incomplete config structure."""
        incomplete_config = {
            "agents": {
                "incomplete_agent": {
                    "model": "gpt-4o",
                    # Missing persona, temperature, etc.
                }
            },
            "sections": {
                "main": [
                    {
                        "type": "agent",
                        "agent": "incomplete_agent",
                        "title": "Incomplete Agent",
                        # Missing required fields
                    }
                ]
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(incomplete_config, f)
            f.flush()

            try:
                with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                    import agents.agent_manager as agent_manager

                    # Load configuration
                    agent_manager.load_configurations()

                    # Should still load the config
                    assert agent_manager._agents_config == incomplete_config["agents"]

                    # But may have None/missing values for incomplete fields
                    agent_info = agent_manager.get_agent_info("incomplete_agent")
                    assert agent_info is not None
                    assert agent_info["model"] == "gpt-4o"
                    assert "persona" not in agent_info or agent_info["persona"] is None
            finally:
                # Cleanup
                os.unlink(f.name)


class TestAgentConfigurationValidation:
    """Test validation of agent configuration structures."""

    @pytest.fixture(autouse=True)
    def reset_module_state(self):
        """Reset agent_manager module state before each test."""
        import agents.agent_manager as agent_manager

        # Store original state from global configuration
        original_agents_config = agent_manager._agents_config.copy()
        original_pages_config = agent_manager._pages_config.copy()
        original_current_agent = agent_manager._get_current_agent_thread_local()

        yield

        # Restore original state to global configuration and thread-local current agent
        agent_manager._agents_config = original_agents_config
        agent_manager._pages_config = original_pages_config
        agent_manager._set_current_agent_thread_local(original_current_agent)

    def test_valid_single_document_agent(self):
        """Test agent with single document configuration."""
        config = {
            "agents": {
                "single_doc_agent": {
                    "persona": "prompts/persona.md",
                    "document": "prompts/single_doc.md",
                    "model": "gpt-4o",
                    "temperature": 0.5,
                }
            },
            "sections": {
                "main": [
                    {
                        "type": "agent",
                        "agent": "single_doc_agent",
                        "title": "Single Doc Agent",
                        "header": "Single",
                        "subtitle": "Single Document Agent",
                    }
                ]
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()

            try:
                with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                    import agents.agent_manager as agent_manager

                    # Load configuration
                    agent_manager.load_configurations()

                    agent_info = agent_manager.get_agent_info("single_doc_agent")
                    assert agent_info is not None
                    assert agent_info["document"] == "prompts/single_doc.md"
                    assert agent_info["model"] == "gpt-4o"
            finally:
                # Cleanup
                os.unlink(f.name)

    def test_valid_multiple_documents_agent(self):
        """Test agent with multiple documents configuration."""
        config = {
            "agents": {
                "multi_doc_agent": {
                    "persona": "prompts/persona.md",
                    "documents": [
                        "prompts/doc1.md",
                        "prompts/doc2.md",
                    ],
                    "model": "gpt-4o-mini",
                    "temperature": 1.0,
                }
            },
            "sections": {
                "main": [
                    {
                        "type": "agent",
                        "agent": "multi_doc_agent",
                        "title": "Multi Doc Agent",
                        "header": "Multi",
                        "subtitle": "Multiple Documents Agent",
                    }
                ]
            },
        }

        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            f.flush()

            try:
                with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                    import agents.agent_manager as agent_manager

                    # Load configuration
                    agent_manager.load_configurations()

                    agent_info = agent_manager.get_agent_info("multi_doc_agent")
                    assert agent_info is not None
                    assert agent_info["documents"] == [
                        "prompts/doc1.md",
                        "prompts/doc2.md",
                    ]
                    assert agent_info["model"] == "gpt-4o-mini"
                    assert agent_info["temperature"] == 1.0
            finally:
                # Cleanup
                os.unlink(f.name)
