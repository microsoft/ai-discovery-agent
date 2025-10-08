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

from agents.agent_manager import ChainlitAgentManager
from tests.fixtures.data import SAMPLE_AGENT_CONFIG


class TestAgentManagerIntegration:
    """Integration tests for ChainlitAgentManager."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(SAMPLE_AGENT_CONFIG, f)
            yield f.name
        # Cleanup
        os.unlink(f.name)

    def test_load_configurations_with_real_file(self, temp_config_file):
        """Test loading configurations from actual file."""
        # Patch the PAGES_CONFIG_FILE constant
        with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)):
            manager = ChainlitAgentManager()

            # Verify configuration was loaded correctly
            assert manager.pages_config == SAMPLE_AGENT_CONFIG
            assert manager.agents_config == SAMPLE_AGENT_CONFIG["agents"]
            assert "facilitator" in manager.agents_config
            assert "expert" in manager.agents_config

    def test_agent_switching_workflow(self, temp_config_file):
        """Test complete agent switching workflow."""
        with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)):
            manager = ChainlitAgentManager()

            # Test initial state
            assert manager.current_agent is None

            # Test switching to facilitator
            success = manager.set_current_agent("facilitator")
            assert success is True
            assert manager.current_agent == "facilitator"

            # Test getting agent info
            agent_info = manager.get_agent_info("facilitator")
            assert agent_info is not None
            assert agent_info["model"] == "gpt-4o"
            assert agent_info["temperature"] == 0.7

            # Test switching to expert
            success = manager.set_current_agent("expert")
            assert success is True
            assert manager.current_agent == "expert"

            # Test switching to non-existent agent
            success = manager.set_current_agent("nonexistent")
            assert success is False
            assert manager.current_agent == "expert"  # Should remain unchanged

    def test_role_based_access_control_workflow(self, temp_config_file):
        """Test complete role-based access control workflow."""
        with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)):
            manager = ChainlitAgentManager()

            # Test regular user access
            user_agents = manager.get_available_agents(["user"])
            assert "facilitator" in user_agents
            assert "expert" not in user_agents  # admin_only

            # Test admin user access
            admin_agents = manager.get_available_agents(["admin", "user"])
            assert "facilitator" in admin_agents
            assert "expert" in admin_agents  # admin can access admin_only

            # Test no roles
            no_role_agents = manager.get_available_agents(None)
            assert "facilitator" in no_role_agents
            assert "expert" not in no_role_agents

            # Test empty roles
            empty_role_agents = manager.get_available_agents([])
            assert "facilitator" in empty_role_agents
            assert "expert" not in empty_role_agents


class TestAgentManagerErrorHandling:
    """Test error handling in agent manager."""

    def test_missing_config_file(self):
        """Test behavior when config file is missing."""
        with patch(
            "agents.agent_manager.PAGES_CONFIG_FILE", Path("/nonexistent/config.yaml")
        ):
            manager = ChainlitAgentManager()

            # Should have empty configs
            assert manager.pages_config == {}
            assert manager.agents_config == {}

            # Operations should handle empty config gracefully
            agents = manager.get_available_agents(["user"])
            assert agents == {}

            agent_info = manager.get_agent_info("any_agent")
            assert agent_info is None

            success = manager.set_current_agent("any_agent")
            assert success is False

    def test_malformed_config_file(self):
        """Test behavior with malformed YAML config."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")  # Invalid YAML
            f.flush()

            with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                manager = ChainlitAgentManager()

                # Should have empty configs due to parsing error
                assert manager.pages_config == {}
                assert manager.agents_config == {}

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

            with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                manager = ChainlitAgentManager()

                # Should still load the config
                assert manager.agents_config == incomplete_config["agents"]

                # But may have None/missing values for incomplete fields
                agent_info = manager.get_agent_info("incomplete_agent")
                assert agent_info is not None
                assert agent_info["model"] == "gpt-4o"
                assert "persona" not in agent_info or agent_info["persona"] is None

            # Cleanup
            os.unlink(f.name)


class TestAgentConfigurationValidation:
    """Test validation of agent configuration structures."""

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

            with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                manager = ChainlitAgentManager()

                agent_info = manager.get_agent_info("single_doc_agent")
                assert agent_info is not None
                assert agent_info["document"] == "prompts/single_doc.md"
                assert agent_info["model"] == "gpt-4o"

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

            with patch("agents.agent_manager.PAGES_CONFIG_FILE", Path(f.name)):
                manager = ChainlitAgentManager()

                agent_info = manager.get_agent_info("multi_doc_agent")
                assert agent_info is not None
                assert agent_info["documents"] == ["prompts/doc1.md", "prompts/doc2.md"]
                assert agent_info["model"] == "gpt-4o-mini"
                assert agent_info["temperature"] == 1.0

            # Cleanup
            os.unlink(f.name)
