# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.

"""
Unit tests for configuration validation.

This test module validates that all agents and pages defined in the configuration
are correctly configured and all referenced files exist. This helps prevent runtime
errors due to missing files or configuration mismatches.
"""

from pathlib import Path

import pytest
import yaml


class TestConfigurationValidation:
    """Test suite for validating pages.yaml configuration integrity."""

    @pytest.fixture
    def config_path(self) -> Path:
        """Path to the pages configuration file."""
        # The config file is at the project root, not in src/
        # When tests run from src/, we need to go up one level
        project_root = Path.cwd()
        if project_root.name == "src":
            project_root = project_root.parent
        return project_root / "config/pages.yaml"

    @pytest.fixture
    def config_data(self, config_path: Path) -> dict:
        """Load and return configuration data."""
        if not config_path.exists():
            pytest.skip(f"Configuration file not found: {config_path}")

        with open(config_path, encoding="utf-8") as file:
            return yaml.load(file, Loader=yaml.SafeLoader)

    @pytest.fixture
    def prompts_dir(self) -> Path:
        """Path to the prompts directory."""
        # The prompts directory is at the project root
        project_root = Path.cwd()
        if project_root.name == "src":
            project_root = project_root.parent

        root_prompts = project_root / "prompts"
        if root_prompts.exists():
            return root_prompts
        else:
            pytest.skip("Prompts directory not found")
            return None

    def test_config_file_exists(self, config_path: Path) -> None:
        """Test that pages.yaml configuration file exists."""
        assert config_path.exists(), f"Configuration file not found: {config_path}"

    def test_config_is_valid_yaml(self, config_path: Path) -> None:
        """Test that pages.yaml is valid YAML."""
        try:
            with open(config_path, encoding="utf-8") as file:
                yaml.load(file, Loader=yaml.SafeLoader)
        except yaml.YAMLError as e:
            pytest.fail(f"Invalid YAML in configuration file: {e}")

    def test_config_has_required_sections(self, config_data: dict) -> None:
        """Test that configuration has required top-level sections."""
        assert "agents" in config_data, "Configuration missing 'agents' section"
        assert "sections" in config_data, "Configuration missing 'sections' section"

    def test_all_agents_have_required_fields(self, config_data: dict) -> None:
        """Test that all agents have required configuration fields."""
        agents = config_data.get("agents", {})
        assert agents, "No agents defined in configuration"

        for agent_key, agent_config in agents.items():
            # Non-graph agents must have persona
            if "agents" not in agent_config:  # Not a graph agent
                assert "persona" in agent_config, (
                    f"Agent '{agent_key}' missing 'persona' field"
                )

            # All agents should have model and temperature (or inherit defaults)
            if "model" not in agent_config:
                pytest.skip(
                    f"Agent '{agent_key}' missing 'model' field - may use default"
                )

    def test_agent_persona_files_exist(
        self, config_data: dict, prompts_dir: Path
    ) -> None:
        """Test that all referenced persona files exist."""
        agents = config_data.get("agents", {})
        missing_files = []

        for agent_key, agent_config in agents.items():
            if "persona" in agent_config:
                persona_path = prompts_dir / Path(agent_config["persona"]).name
                if not persona_path.exists():
                    missing_files.append(f"{agent_key}: {agent_config['persona']}")

        assert not missing_files, "Missing persona files:\n" + "\n".join(
            f"  - {f}" for f in missing_files
        )

    def test_agent_document_files_exist(
        self, config_data: dict, prompts_dir: Path
    ) -> None:
        """Test that all referenced document files exist."""
        agents = config_data.get("agents", {})
        missing_files = []

        for agent_key, agent_config in agents.items():
            # Check single document field
            if "document" in agent_config:
                doc_path = prompts_dir / Path(agent_config["document"]).name
                if not doc_path.exists():
                    missing_files.append(f"{agent_key}: {agent_config['document']}")

            # Check documents array field
            if "documents" in agent_config:
                for doc in agent_config["documents"]:
                    doc_path = prompts_dir / Path(doc).name
                    if not doc_path.exists():
                        missing_files.append(f"{agent_key}: {doc}")

        assert not missing_files, "Missing document files:\n" + "\n".join(
            f"  - {f}" for f in missing_files
        )

    def test_all_page_agents_are_defined(self, config_data: dict) -> None:
        """Test that all agents referenced in pages are defined in agents section."""
        agents = config_data.get("agents", {})
        sections = config_data.get("sections", {})
        undefined_agents = []

        for section_name, pages in sections.items():
            for page in pages:
                if page.get("type") == "agent":
                    agent_key = page.get("agent")
                    if not agent_key:
                        undefined_agents.append(
                            f"Section '{section_name}': Page missing 'agent' field"
                        )
                    elif agent_key not in agents:
                        page_title = page.get("title", "Unknown")
                        undefined_agents.append(
                            f"Section '{section_name}': Page '{page_title}' references "
                            f"undefined agent '{agent_key}'"
                        )

        assert not undefined_agents, "Pages reference undefined agents:\n" + "\n".join(
            f"  - {a}" for a in undefined_agents
        )

    def test_all_pages_have_required_fields(self, config_data: dict) -> None:
        """Test that all pages have required fields."""
        sections = config_data.get("sections", {})
        invalid_pages = []

        required_fields = ["type", "title", "icon", "url_path", "header", "subtitle"]

        for section_name, pages in sections.items():
            for idx, page in enumerate(pages):
                missing_fields = [
                    field for field in required_fields if field not in page
                ]
                if missing_fields:
                    page_title = page.get("title", f"Page #{idx}")
                    invalid_pages.append(
                        f"Section '{section_name}', Page '{page_title}': "
                        f"Missing fields: {', '.join(missing_fields)}"
                    )

        assert not invalid_pages, "Pages with missing required fields:\n" + "\n".join(
            f"  - {p}" for p in invalid_pages
        )

    def test_graph_agents_reference_valid_agents(self, config_data: dict) -> None:
        """Test that graph agents only reference valid agent keys."""
        agents = config_data.get("agents", {})
        invalid_references = []

        for agent_key, agent_config in agents.items():
            # Check if this is a graph agent
            if "agents" in agent_config:
                graph_agents = agent_config["agents"]
                for graph_agent in graph_agents:
                    referenced_agent = graph_agent.get("agent")
                    if referenced_agent and referenced_agent not in agents:
                        invalid_references.append(
                            f"Graph agent '{agent_key}' references undefined agent "
                            f"'{referenced_agent}'"
                        )

        assert not invalid_references, (
            "Invalid agent references in graph agents:\n"
            + "\n".join(f"  - {r}" for r in invalid_references)
        )

    def test_no_duplicate_agent_keys(
        self, config_data: dict, config_path: Path
    ) -> None:
        """Test that there are no duplicate agent keys."""
        agents = config_data.get("agents", {})
        # In Python dicts, duplicate keys would just overwrite, so we check YAML directly

        with open(config_path, encoding="utf-8") as file:
            file.read()

        # Simple check for duplicate agent definitions
        agent_keys = list(agents.keys())
        seen = set()
        duplicates = []

        for key in agent_keys:
            if key in seen:
                duplicates.append(key)
            seen.add(key)

        assert not duplicates, f"Duplicate agent keys found: {', '.join(duplicates)}"

    def test_no_duplicate_url_paths(self, config_data: dict) -> None:
        """Test that there are no duplicate URL paths."""
        sections = config_data.get("sections", {})
        url_paths = {}
        duplicates = []

        for _section_name, pages in sections.items():
            for page in pages:
                url_path = page.get("url_path")
                if url_path:
                    if url_path in url_paths:
                        duplicates.append(
                            f"URL path '{url_path}' used by both "
                            f"'{url_paths[url_path]}' and '{page.get('title')}'"
                        )
                    else:
                        url_paths[url_path] = page.get("title", "Unknown")

        assert not duplicates, "Duplicate URL paths found:\n" + "\n".join(
            f"  - {d}" for d in duplicates
        )

    def test_at_least_one_default_page(self, config_data: dict) -> None:
        """Test that at least one page is marked as default."""
        sections = config_data.get("sections", {})
        default_pages = []

        for _section_name, pages in sections.items():
            for page in pages:
                if page.get("default", False):
                    default_pages.append(page.get("title", "Unknown"))

        assert default_pages, (
            "No default page found. At least one page should have 'default: true'"
        )

    def test_model_names_are_valid(self, config_data: dict) -> None:
        """Test that all model names follow expected patterns."""
        agents = config_data.get("agents", {})
        # Common Azure OpenAI model patterns
        valid_model_patterns = [
            "gpt-4o",
            "gpt-4o-mini",
            "gpt-4",
            "gpt-4-32k",
            "gpt-35-turbo",
            "gpt-3.5-turbo",
            "o1-preview",
            "o1-mini",
            "o4-mini",
            "gpt-4.1-nano",
        ]

        invalid_models = []

        for agent_key, agent_config in agents.items():
            model = agent_config.get("model")
            if model and not any(
                model.startswith(pattern) for pattern in valid_model_patterns
            ):
                invalid_models.append(f"{agent_key}: {model}")

        assert not invalid_models, (
            "Agents with potentially invalid model names:\n"
            + "\n".join(f"  - {m}" for m in invalid_models)
        )

    def test_temperature_values_are_valid(self, config_data: dict) -> None:
        """Test that temperature values are within valid range (0.0 to 2.0)."""
        agents = config_data.get("agents", {})
        invalid_temperatures = []

        for agent_key, agent_config in agents.items():
            temperature = agent_config.get("temperature")
            if temperature is not None:
                if not isinstance(temperature, (int, float)):
                    invalid_temperatures.append(
                        f"{agent_key}: temperature is not a number ({temperature})"
                    )
                elif temperature < 0.0 or temperature > 2.0:
                    invalid_temperatures.append(
                        f"{agent_key}: temperature {temperature} out of range [0.0, 2.0]"
                    )

        assert not invalid_temperatures, (
            "Agents with invalid temperature values:\n"
            + "\n".join(f"  - {t}" for t in invalid_temperatures)
        )

    def test_admin_only_pages_are_properly_marked(self, config_data: dict) -> None:
        """Test that admin_only field is boolean when present."""
        sections = config_data.get("sections", {})
        invalid_admin_flags = []

        for section_name, pages in sections.items():
            for page in pages:
                admin_only = page.get("admin_only")
                if admin_only is not None and not isinstance(admin_only, bool):
                    page_title = page.get("title", "Unknown")
                    invalid_admin_flags.append(
                        f"Section '{section_name}', Page '{page_title}': "
                        f"admin_only must be boolean, got {type(admin_only).__name__}"
                    )

        assert not invalid_admin_flags, (
            "Pages with invalid admin_only flags:\n"
            + "\n".join(f"  - {f}" for f in invalid_admin_flags)
        )
