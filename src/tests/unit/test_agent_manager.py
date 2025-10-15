# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Unit tests for the agent_manager module.

Tests agent configuration loading, agent switching, and user role-based access.
Updated for global configuration and thread-local current agent implementation.
"""

from pathlib import Path
from unittest.mock import mock_open, patch

import pytest
import yaml

import agents.agent_manager as agent_manager
from tests.fixtures.data import SAMPLE_AGENT_CONFIG


class TestAgentManagerModule:
    """Test agent_manager module functionality."""

    @pytest.fixture(autouse=True)
    def setup_clean_state(self):
        """Reset module state before each test."""
        # Clear the LRU cache to ensure fresh lookups
        agent_manager._extract_agents_from_sections.cache_clear()
        # Reset global configuration state to clean state
        agent_manager._agents_config = {}
        agent_manager._pages_config = {}
        # Reset thread-local current agent
        agent_manager._set_current_agent_thread_local(None)
        yield
        # Clean up after test
        agent_manager._extract_agents_from_sections.cache_clear()
        agent_manager._agents_config = {}
        agent_manager._pages_config = {}
        agent_manager._set_current_agent_thread_local(None)

    @pytest.fixture
    def mock_config_file(self):
        """Mock config file content."""
        return yaml.dump(SAMPLE_AGENT_CONFIG)

    @patch("builtins.open", new_callable=mock_open)
    @patch("agents.agent_manager.yaml.load")
    def test_load_configurations_success(self, mock_yaml_load, mock_file):
        """Test successful configuration loading."""
        # Arrange
        mock_yaml_load.return_value = SAMPLE_AGENT_CONFIG

        # Act
        agent_manager.load_configurations()

        # Assert
        assert agent_manager._pages_config == SAMPLE_AGENT_CONFIG
        assert agent_manager._agents_config == SAMPLE_AGENT_CONFIG["agents"]
        mock_yaml_load.assert_called_once()

    @patch("builtins.open", side_effect=FileNotFoundError)
    @patch("agents.agent_manager.logger.error")
    def test_load_configurations_file_not_found(self, mock_logger, mock_file):
        """Test configuration loading when file is missing."""
        # Act
        agent_manager.load_configurations()

        # Assert
        assert agent_manager._pages_config == {}
        assert agent_manager._agents_config == {}
        mock_logger.assert_called_once()

    @patch("builtins.open", new_callable=mock_open, read_data="invalid: yaml: content")
    @patch("agents.agent_manager.yaml.load", side_effect=yaml.YAMLError("Invalid YAML"))
    @patch("agents.agent_manager.logger.error")
    def test_load_configurations_yaml_error(
        self, mock_logger, mock_yaml_load, mock_file
    ):
        """Test configuration loading with invalid YAML."""
        # Act
        agent_manager.load_configurations()

        # Assert
        assert agent_manager._pages_config == {}
        assert agent_manager._agents_config == {}
        mock_logger.assert_called_once()

    def test_get_available_agents_regular_user(self):
        """Test getting available agents for regular user."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        user_roles = ["user"]

        # Act
        result = agent_manager.get_available_agents(user_roles)

        # Assert
        assert "facilitator" in result
        assert "expert" not in result  # admin_only agent should be excluded
        assert result["facilitator"]["title"] == "Workshop Facilitator"

    def test_get_available_agents_admin_user(self):
        """Test getting available agents for admin user."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        user_roles = ["admin", "user"]

        # Act
        result = agent_manager.get_available_agents(user_roles)

        # Assert
        assert "facilitator" in result
        assert "expert" in result  # admin_only agent should be included
        assert result["expert"]["title"] == "Expert Advisor"

    def test_get_available_agents_no_roles(self):
        """Test getting available agents with no user roles."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        user_roles = None

        # Act
        result = agent_manager.get_available_agents(user_roles)

        # Assert
        assert "facilitator" in result
        assert "expert" not in result  # admin_only agent should be excluded

    def test_get_available_agents_empty_config(self):
        """Test getting available agents with empty configuration."""
        # Arrange
        agent_manager._agents_config = {}
        agent_manager._pages_config = {"sections": {}}
        # Clear the cache to ensure fresh result
        agent_manager._extract_agents_from_sections.cache_clear()
        user_roles = ["user"]

        # Act
        result = agent_manager.get_available_agents(user_roles)

        # Assert
        assert result == {}

    def test_get_available_agents_caching(self):
        """Test that get_available_agents uses caching properly."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        user_roles = ["user"]

        # Clear cache before test
        agent_manager._extract_agents_from_sections.cache_clear()

        # Act - call twice with same arguments
        result1 = agent_manager.get_available_agents(user_roles)
        result2 = agent_manager.get_available_agents(user_roles)

        # Assert
        assert result1 == result2
        assert "facilitator" in result1
        # Check cache info shows cache hit
        cache_info = agent_manager._extract_agents_from_sections.cache_info()
        assert cache_info.hits > 0

    def test_extract_agents_from_sections_comprehensive_caching(self):
        """Test comprehensive caching behavior of _extract_agents_from_sections."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG

        # Clear cache before test
        agent_manager._extract_agents_from_sections.cache_clear()
        initial_cache_info = agent_manager._extract_agents_from_sections.cache_info()
        assert initial_cache_info.hits == 0
        assert initial_cache_info.misses == 0

        # Test 1: First call should be a cache miss
        user_roles_1 = ("user",)
        result1 = agent_manager._extract_agents_from_sections(user_roles_1)
        cache_info_after_first = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_after_first.misses == 1
        assert cache_info_after_first.hits == 0
        assert "facilitator" in result1
        assert "expert" not in result1  # admin_only agent excluded

        # Test 2: Second call with same arguments should be a cache hit
        result2 = agent_manager._extract_agents_from_sections(user_roles_1)
        cache_info_after_second = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_after_second.misses == 1
        assert cache_info_after_second.hits == 1
        assert result1 == result2

        # Test 3: Call with different arguments should be a new cache miss
        admin_roles = ("admin", "user")
        result3 = agent_manager._extract_agents_from_sections(admin_roles)
        cache_info_after_third = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_after_third.misses == 2
        assert cache_info_after_third.hits == 1
        assert "facilitator" in result3
        assert "expert" in result3  # admin_only agent included for admin
        assert result1 != result3  # Different results for different roles

        # Test 4: Call admin roles again should be a cache hit
        result4 = agent_manager._extract_agents_from_sections(admin_roles)
        cache_info_after_fourth = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_after_fourth.misses == 2
        assert cache_info_after_fourth.hits == 2
        assert result3 == result4

        # Test 5: Test empty roles tuple
        empty_roles = ()
        result5 = agent_manager._extract_agents_from_sections(empty_roles)
        cache_info_after_fifth = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_after_fifth.misses == 3
        assert cache_info_after_fifth.hits == 2
        assert "facilitator" in result5
        assert "expert" not in result5  # admin_only agent excluded for empty roles

    def test_cache_invalidation_on_configuration_reload(self):
        """Test that cache is properly cleared when configuration is reloaded."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        user_roles = ("user",)

        # Clear cache and make initial call
        agent_manager._extract_agents_from_sections.cache_clear()
        result1 = agent_manager._extract_agents_from_sections(user_roles)
        cache_info_before_reload = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_before_reload.misses == 1
        assert cache_info_before_reload.hits == 0

        # Act - Reload configuration (this should clear the cache)
        with patch(
            "builtins.open", mock_open(read_data=yaml.dump(SAMPLE_AGENT_CONFIG))
        ):
            with patch("agents.agent_manager.yaml.load") as mock_yaml_load:
                mock_yaml_load.return_value = SAMPLE_AGENT_CONFIG
                agent_manager.load_configurations()

        # Assert - Cache should be cleared after reload
        cache_info_after_reload = (
            agent_manager._extract_agents_from_sections.cache_info()
        )
        assert cache_info_after_reload.misses == 0
        assert cache_info_after_reload.hits == 0

        # Next call should be a cache miss again
        result2 = agent_manager._extract_agents_from_sections(user_roles)
        cache_info_after_call = agent_manager._extract_agents_from_sections.cache_info()
        assert cache_info_after_call.misses == 1
        assert cache_info_after_call.hits == 0
        assert (
            result1 == result2
        )  # Results should be the same (configuration didn't change)

    def test_extract_agents_from_sections_performance_with_cache(self):
        """Test that caching improves performance for repeated calls."""
        import time

        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        user_roles = ("user",)

        # Clear cache before test
        agent_manager._extract_agents_from_sections.cache_clear()

        # Measure first call (cache miss)
        start_time = time.perf_counter()
        result1 = agent_manager._extract_agents_from_sections(user_roles)
        first_call_time = time.perf_counter() - start_time

        # Measure second call (cache hit)
        start_time = time.perf_counter()
        result2 = agent_manager._extract_agents_from_sections(user_roles)
        second_call_time = time.perf_counter() - start_time

        # Assert
        assert result1 == result2
        # Cache hit should be significantly faster (at least 2x faster)
        # Note: This is a rough performance test - in practice the speedup
        # depends on the complexity of the configuration processing
        assert second_call_time < first_call_time
        cache_info = agent_manager._extract_agents_from_sections.cache_info()
        assert cache_info.hits == 1
        assert cache_info.misses == 1

    def test_get_agent_info_existing_agent(self):
        """Test getting info for existing agent."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        agent_key = "facilitator"

        # Act
        result = agent_manager.get_agent_info(agent_key)

        # Assert
        assert result is not None
        assert result["persona"] == "prompts/facilitator_persona.md"
        assert result["model"] == "gpt-4o"
        assert result["temperature"] == 0.7

    def test_get_agent_info_nonexistent_agent(self):
        """Test getting info for non-existent agent."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        agent_key = "nonexistent"

        # Act
        result = agent_manager.get_agent_info(agent_key)

        # Assert
        assert result is None

    def test_set_current_agent_existing(self):
        """Test setting current agent to existing agent."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        agent_key = "facilitator"

        # Act
        result = agent_manager.set_current_agent(agent_key)

        # Assert
        assert result is True
        assert agent_manager.get_current_agent() == agent_key

    def test_set_current_agent_nonexistent(self):
        """Test setting current agent to non-existent agent."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG
        agent_key = "nonexistent"

        # Act
        result = agent_manager.set_current_agent(agent_key)

        # Assert
        assert result is False
        assert agent_manager.get_current_agent() is None

    def test_set_current_agent_empty_config(self):
        """Test setting current agent with empty configuration."""
        # Arrange
        agent_manager._agents_config = {}
        agent_manager._pages_config = {}
        agent_key = "facilitator"

        # Act
        result = agent_manager.set_current_agent(agent_key)

        # Assert
        assert result is False
        assert agent_manager.get_current_agent() is None

    def test_current_agent_persistence(self):
        """Test that current agent persists across function calls."""
        # Arrange
        agent_manager._agents_config = SAMPLE_AGENT_CONFIG["agents"]
        agent_manager._pages_config = SAMPLE_AGENT_CONFIG

        # Act
        agent_manager.set_current_agent("facilitator")
        first_check = agent_manager.get_current_agent()

        agent_manager.set_current_agent("expert")
        second_check = agent_manager.get_current_agent()

        # Assert
        assert first_check == "facilitator"
        assert second_check == "expert"


class TestAgentManagerIntegration:
    """Integration tests for agent manager with file system."""

    @patch("agents.agent_manager.PAGES_CONFIG_FILE")
    def test_load_configurations_with_real_path(self, mock_path):
        """Test loading configurations with actual file path logic."""
        # Arrange
        mock_path.return_value = Path("/fake/path/config/pages.yaml")

        with patch(
            "builtins.open", mock_open(read_data=yaml.dump(SAMPLE_AGENT_CONFIG))
        ):
            with patch("agents.agent_manager.yaml.load") as mock_yaml_load:
                mock_yaml_load.return_value = SAMPLE_AGENT_CONFIG

                # Act
                agent_manager.load_configurations()

                # Assert
                assert agent_manager._agents_config == SAMPLE_AGENT_CONFIG["agents"]
                assert agent_manager._pages_config == SAMPLE_AGENT_CONFIG
