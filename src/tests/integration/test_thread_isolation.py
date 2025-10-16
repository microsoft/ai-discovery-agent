# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Thread isolation tests for agent manager functionality.

Tests that different threads (simulating different user web sessions)
maintain separate agent states without interference.
"""

import os
import threading
import time
from pathlib import Path
from tempfile import NamedTemporaryFile
from unittest.mock import patch

import pytest
import yaml

from tests.fixtures.data import SAMPLE_AGENT_CONFIG


class TestAgentManagerThreadIsolation:
    """Test thread isolation in agent_manager module."""

    @pytest.fixture
    def temp_config_file(self):
        """Create a temporary config file."""
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(SAMPLE_AGENT_CONFIG, f)
            yield f.name
        # Cleanup
        os.unlink(f.name)

    def test_thread_isolated_current_agent(self, temp_config_file):
        """Test that current agent is isolated between threads."""
        results = {}
        errors = {}

        def thread_worker(thread_id: str, agent_key: str):
            """Worker function that sets an agent in its thread."""
            try:
                with patch(
                    "agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)
                ):
                    import agents.agent_manager as agent_manager

                    # Load configuration in this thread
                    agent_manager.load_configurations()

                    # Initially should be None
                    assert agent_manager.get_current_agent() is None

                    # Set the agent for this thread
                    success = agent_manager.set_current_agent(agent_key)
                    assert success is True

                    # Store the result
                    results[thread_id] = agent_manager.get_current_agent()

                    # Sleep briefly to ensure threads are running concurrently
                    time.sleep(0.1)

                    # Verify the agent is still set correctly after other threads run
                    final_agent = agent_manager.get_current_agent()
                    results[f"{thread_id}_final"] = final_agent

            except Exception as e:
                errors[thread_id] = str(e)

        # Create threads that set different agents
        thread1 = threading.Thread(
            target=thread_worker, args=("thread1", "facilitator")
        )
        thread2 = threading.Thread(target=thread_worker, args=("thread2", "expert"))

        # Start threads
        thread1.start()
        thread2.start()

        # Wait for completion
        thread1.join()
        thread2.join()

        # Check for errors
        assert not errors, f"Thread errors occurred: {errors}"

        # Verify each thread maintained its own agent
        assert results["thread1"] == "facilitator"
        assert results["thread2"] == "expert"
        assert results["thread1_final"] == "facilitator"
        assert results["thread2_final"] == "expert"

    def test_thread_shared_configurations_isolated_current_agent(
        self, temp_config_file
    ):
        """Test that configurations are shared while current agent is thread-local."""
        results = {}
        errors = {}

        # Use a single configuration that both threads will see
        config = {
            "agents": {
                "agent1": {
                    "persona": "prompts/persona1.md",
                    "model": "gpt-4o",
                    "temperature": 0.5,
                },
                "agent2": {
                    "persona": "prompts/persona2.md",
                    "model": "gpt-4o-mini",
                    "temperature": 1.0,
                },
            },
            "sections": {
                "main": [
                    {
                        "type": "agent",
                        "agent": "agent1",
                        "title": "Agent 1",
                        "header": "A1",
                        "subtitle": "First Agent",
                        "icon": "🔥",
                    },
                    {
                        "type": "agent",
                        "agent": "agent2",
                        "title": "Agent 2",
                        "header": "A2",
                        "subtitle": "Second Agent",
                        "icon": "⚡",
                    },
                ]
            },
        }

        # Create temporary config file
        with NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config, f)
            config_file = f.name

        try:

            def thread_worker(thread_id: str, agent_to_set: str):
                """Worker function that sets different current agents in different threads."""
                try:
                    with patch(
                        "agents.agent_manager.PAGES_CONFIG_FILE", Path(config_file)
                    ):
                        import agents.agent_manager as agent_manager

                        # Load configuration (should be shared globally)
                        agent_manager.load_configurations()

                        # Verify both agents are available (global configuration)
                        available_agents = list(agent_manager._agents_config.keys())
                        results[f"{thread_id}_available"] = available_agents

                        # Set current agent (should be thread-local)
                        success = agent_manager.set_current_agent(agent_to_set)
                        results[f"{thread_id}_set_success"] = success

                        # Sleep to ensure threads run concurrently
                        time.sleep(0.1)

                        # Verify current agent is still the one we set (thread-local)
                        current_agent = agent_manager.get_current_agent()
                        results[f"{thread_id}_current"] = current_agent

                        # Verify configuration is still shared
                        final_available = list(agent_manager._agents_config.keys())
                        results[f"{thread_id}_final_available"] = final_available

                except Exception as e:
                    errors[thread_id] = str(e)

            # Create threads that set different current agents
            thread1 = threading.Thread(target=thread_worker, args=("thread1", "agent1"))
            thread2 = threading.Thread(target=thread_worker, args=("thread2", "agent2"))

            # Start threads
            thread1.start()
            thread2.start()

            # Wait for completion
            thread1.join()
            thread2.join()

            # Check for errors
            assert not errors, f"Thread errors occurred: {errors}"

            # Verify configurations are shared (both threads see both agents)
            assert sorted(results["thread1_available"]) == ["agent1", "agent2"]
            assert sorted(results["thread2_available"]) == ["agent1", "agent2"]
            assert sorted(results["thread1_final_available"]) == ["agent1", "agent2"]
            assert sorted(results["thread2_final_available"]) == ["agent1", "agent2"]

            # Verify current agents are thread-local (different per thread)
            assert results["thread1_set_success"] is True
            assert results["thread2_set_success"] is True
            assert results["thread1_current"] == "agent1"
            assert results["thread2_current"] == "agent2"

        finally:
            # Cleanup
            os.unlink(config_file)

    def test_multiple_concurrent_agent_switches(self, temp_config_file):
        """Test multiple threads rapidly switching agents without interference."""
        results = {}
        errors = {}

        def thread_worker(thread_id: str):
            """Worker that rapidly switches between agents."""
            try:
                with patch(
                    "agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)
                ):
                    import agents.agent_manager as agent_manager

                    # Load configuration
                    agent_manager.load_configurations()

                    switches = []

                    # Perform rapid agent switches
                    for i in range(5):
                        agent = "facilitator" if i % 2 == 0 else "expert"
                        success = agent_manager.set_current_agent(agent)
                        current = agent_manager.get_current_agent()
                        switches.append(
                            {"agent": agent, "success": success, "current": current}
                        )
                        time.sleep(0.01)  # Brief pause between switches

                    results[thread_id] = switches

            except Exception as e:
                errors[thread_id] = str(e)

        # Create multiple threads
        threads = []
        for i in range(4):
            thread = threading.Thread(target=thread_worker, args=(f"thread{i}",))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Check for errors
        assert not errors, f"Thread errors occurred: {errors}"

        # Verify all threads completed their switches successfully
        for _thread_id, switches in results.items():
            assert len(switches) == 5
            for switch in switches:
                assert switch["success"] is True
                assert switch["current"] == switch["agent"]
                assert switch["current"] in ["facilitator", "expert"]

    def test_thread_isolation_with_role_based_access(self, temp_config_file):
        """Test that role-based access control is isolated between threads."""
        results = {}
        errors = {}

        def thread_worker(thread_id: str, user_roles: list[str]):
            """Worker that tests role-based access with different user roles."""
            try:
                with patch(
                    "agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)
                ):
                    import agents.agent_manager as agent_manager

                    # Load configuration
                    agent_manager.load_configurations()

                    # Get available agents for the user roles
                    available_agents = agent_manager.get_available_agents(user_roles)

                    results[thread_id] = {
                        "roles": user_roles,
                        "available_agents": list(available_agents.keys()),
                        "facilitator_available": "facilitator" in available_agents,
                        "expert_available": "expert" in available_agents,
                    }

                    # Sleep to ensure concurrent execution
                    time.sleep(0.1)

                    # Verify results are still correct after other threads
                    final_agents = agent_manager.get_available_agents(user_roles)
                    results[f"{thread_id}_final"] = {
                        "available_agents": list(final_agents.keys()),
                        "facilitator_available": "facilitator" in final_agents,
                        "expert_available": "expert" in final_agents,
                    }

            except Exception as e:
                errors[thread_id] = str(e)

        # Create threads with different user roles
        thread1 = threading.Thread(target=thread_worker, args=("user_thread", ["user"]))
        thread2 = threading.Thread(
            target=thread_worker, args=("admin_thread", ["admin", "user"])
        )
        thread3 = threading.Thread(target=thread_worker, args=("no_role_thread", []))

        # Start threads
        thread1.start()
        thread2.start()
        thread3.start()

        # Wait for completion
        thread1.join()
        thread2.join()
        thread3.join()

        # Check for errors
        assert not errors, f"Thread errors occurred: {errors}"

        # Verify role-based access is correctly isolated
        # User thread should only see facilitator (expert is admin_only)
        assert results["user_thread"]["facilitator_available"] is True
        assert results["user_thread"]["expert_available"] is False

        # Admin thread should see both agents
        assert results["admin_thread"]["facilitator_available"] is True
        assert results["admin_thread"]["expert_available"] is True

        # No role thread should only see facilitator
        assert results["no_role_thread"]["facilitator_available"] is True
        assert results["no_role_thread"]["expert_available"] is False

        # Verify results remained consistent after concurrent execution
        assert results["user_thread_final"]["facilitator_available"] is True
        assert results["user_thread_final"]["expert_available"] is False
        assert results["admin_thread_final"]["facilitator_available"] is True
        assert results["admin_thread_final"]["expert_available"] is True
        assert results["no_role_thread_final"]["facilitator_available"] is True
        assert results["no_role_thread_final"]["expert_available"] is False

    def test_cache_isolation_between_threads(self, temp_config_file):
        """Test that functools.lru_cache works correctly with thread-local data."""
        results = {}
        errors = {}

        def thread_worker(thread_id: str, user_roles: list[str]):
            """Worker that tests cache behavior with different user roles."""
            try:
                with patch(
                    "agents.agent_manager.PAGES_CONFIG_FILE", Path(temp_config_file)
                ):
                    import agents.agent_manager as agent_manager

                    # Load configuration
                    agent_manager.load_configurations()

                    # Clear cache to start fresh
                    agent_manager._extract_agents_from_sections.cache_clear()

                    # Get cache info before first call
                    cache_info_before = (
                        agent_manager._extract_agents_from_sections.cache_info()
                    )

                    # Make first call - should be a cache miss
                    available_agents1 = agent_manager.get_available_agents(user_roles)
                    cache_info_after_first = (
                        agent_manager._extract_agents_from_sections.cache_info()
                    )

                    # Make second call with same roles - should be a cache hit
                    available_agents2 = agent_manager.get_available_agents(user_roles)
                    cache_info_after_second = (
                        agent_manager._extract_agents_from_sections.cache_info()
                    )

                    results[thread_id] = {
                        "cache_hits_before": cache_info_before.hits,
                        "cache_misses_before": cache_info_before.misses,
                        "cache_hits_after_first": cache_info_after_first.hits,
                        "cache_misses_after_first": cache_info_after_first.misses,
                        "cache_hits_after_second": cache_info_after_second.hits,
                        "cache_misses_after_second": cache_info_after_second.misses,
                        "agents_consistent": available_agents1 == available_agents2,
                        "agent_count": len(available_agents1),
                    }

            except Exception as e:
                errors[thread_id] = str(e)

        # Create threads with different user roles
        thread1 = threading.Thread(target=thread_worker, args=("thread1", ["user"]))
        thread2 = threading.Thread(target=thread_worker, args=("thread2", ["admin"]))

        # Start threads
        thread1.start()
        thread2.start()

        # Wait for completion
        thread1.join()
        thread2.join()

        # Check for errors
        assert not errors, f"Thread errors occurred: {errors}"

        # Verify cache behavior in each thread
        for thread_id in ["thread1", "thread2"]:
            result = results[thread_id]

            # First call should increase misses
            assert result["cache_misses_after_first"] > result["cache_misses_before"]

            # Second call should increase hits (cache working)
            assert result["cache_hits_after_second"] > result["cache_hits_after_first"]

            # Results should be consistent
            assert result["agents_consistent"] is True
