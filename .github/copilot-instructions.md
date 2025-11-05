# Copilot Instructions for AI Discovery Workshop Facilitator

This project is an AI-powered workshop facilitation system built with Chainlit that helps guide participants through AI discovery workshops. The system uses multiple AI agents with different personas and documents to provide expert guidance.

## Project Overview

**Core Technologies:**

- **Chainlit**: Web-based chat interface framework
- **Azure OpenAI**: AI model integration (GPT-4o, GPT-4o-mini, embeddings)
- **LangGraph & LangChain**: Agent orchestration and workflow management
- **YAML Configuration**: Agent and page configuration management
- **Azure Infrastructure**: Deployment using Bicep templates

**Key Components:**

- Multi-agent system with configurable personas
- Workshop facilitation through structured 12-step process
- Authentication system (password-based and OAuth)
- Mermaid diagram support for visual workflows
- Azure deployment automation

## Code Quality and Style Guidelines

### 1. **Type Annotations**

All function arguments and return values must be explicitly typed using Python's type
hints. Use the built-in generic types (`dict`, `list`, `tuple`, etc.) instead of the
deprecated `typing.Dict`, `typing.List`, and similar aliases. This aligns with the
project's Black and Ruff configuration:

```python
from typing import Any, Optional

def load_agent_config(config_path: str) -> dict[str, Any]:
    """Load agent configuration from YAML file."""
    return {}

async def process_message(message: str, agent_key: Optional[str] = None) -> str:
    """Process user message with specified agent."""
    return ""


def get_agent_keys(agent_ids: list[str]) -> list[str]:
    """Return a copy of the available agent identifiers."""
    return list(agent_ids)
```

### 2. **Pythonic Code**

Always prefer idiomatic Python patterns, especially for:

- **File operations**: Use `pathlib.Path` instead of `os.path`
- **Configuration loading**: Use context managers for file operations
- **Data processing**: Use comprehensions and built-in functions
- **Async operations**: Proper async/await patterns for Chainlit handlers

### 3. **Documentation Standards**

Every class and method requires clear docstrings following PEP 257:

```python
class ChainlitAgentManager:
    """
    Manages agent configuration and switching in Chainlit.

    This class handles loading agent configurations from YAML files,
    managing the current active agent, and providing agent information
    for the Chainlit interface.
    """

    def load_configurations(self) -> None:
        """
        Load configuration from YAML files.

        Loads both agent configurations and page structures from
        the pages.yaml configuration file. Handles file not found
        and YAML parsing errors gracefully.

        Raises:
            ConfigurationError: If configuration files are invalid
        """
```

### 4. **Black Linter Compliance**

Format all code according to [Black](https://black.readthedocs.io/en/stable/) guidelines. Use line length of 88 characters and ensure proper spacing.

## Project-Specific Development Guidelines

### Copyright and Licensing

All code contributions must include the following copyright header:

```
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
```

### 5. **Agent Configuration Management**

When working with agent configurations, follow these patterns:

**Single Agent Configuration:**

```yaml
agents:
  facilitator:
    persona: prompts/facilitator_persona.md
    document: prompts/workshop_guide.md # Optional single document
    model: gpt-4o
    temperature: 0.7
```

**Multi-Document Agent Configuration:**

```yaml
agents:
  expert_advisor:
    persona: prompts/expert_persona.md
    documents: # Multiple documents for broader knowledge
      - prompts/domain_knowledge.md
      - prompts/best_practices.md
    model: gpt-4o-mini
    temperature: 1.0
```

**Graph Agent Configuration:**

```yaml
agents:
  routing_agent:
    condition: "Analyze input and route to appropriate specialist"
    agents:
      - agent: "technical_expert"
        condition: "technical"
      - agent: "business_expert"
        condition: "business"
    model: gpt-4o
    temperature: 0.5
```

### 6. **Chainlit Integration Patterns**

Follow these patterns when working with Chainlit:

**Session Management:**

```python
import chainlit as cl

@cl.on_chat_start
async def start() -> None:
    """Initialize chat session with agent selection."""
    agent_manager = ChainlitAgentManager()
    cl.user_session.set("agent_manager", agent_manager)

@cl.on_message
async def main(message: cl.Message) -> None:
    """Handle incoming messages with proper agent routing."""
    agent_manager = cl.user_session.get("agent_manager")
    response = await agent_manager.process_message(message.content)
    await cl.Message(content=response).send()
```

**Agent Navigation:**

```python
async def handle_agent_command(command: str) -> None:
    """Handle agent switching commands like !facilitator or !expert."""
    if command.startswith("!"):
        agent_key = command[1:]  # Remove ! prefix
        success = await switch_to_agent(agent_key)
        if success:
            await cl.Message(f"Switched to {agent_key} agent").send()
```

### 7. **Configuration File Management**

When modifying configuration files:

**YAML Schema Validation:**

- Always validate against `pages.schema.json`
- Use YAML language server comments: `# yaml-language-server: $schema=./pages.schema.json`
- Test configuration changes with example files before applying

**Environment Configuration:**

- Use `.env` files for sensitive configuration (Azure OpenAI keys)
- Keep example files updated (`auth-config-example.yaml`, `pages-example.yaml`)
- Document required environment variables in README

### 8. **Azure OpenAI Integration**

When working with AI models:

**Model Configuration:**

```python
# Use environment variables for Azure OpenAI configuration
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_API_VERSION = os.getenv("AZURE_OPENAI_API_VERSION", "2025-01-01-preview")

# Support multiple model types from bicep configuration
SUPPORTED_MODELS = ["gpt-4o", "gpt-4o-mini", "o4-mini", "text-embedding-ada-002"]
```

**Error Handling:**

```python
async def call_azure_openai(messages: List[Dict], model: str) -> str:
    """Call Azure OpenAI with proper error handling."""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Azure OpenAI call failed: {e}", exc_info=True)
        raise AIModelError(f"Failed to generate response: {e}")
```

### 9. **Workshop Facilitation Logic**

When implementing workshop-related features:

**12-Step Process Management:**

```python
class WorkshopStep(Enum):
    """Enumeration of workshop steps."""
    UNDERSTAND_BUSINESS = 1
    CHOOSE_TOPIC = 2
    IDEATE_ACTIVITIES = 3
    # ... continue for all 12 steps

async def validate_step_completion(current_step: WorkshopStep, user_input: str) -> bool:
    """Validate if current step requirements are met before proceeding."""
```

**Persona Management:**

```python
def load_persona_prompt(persona_path: str) -> str:
    """Load persona prompt with proper error handling."""
    persona_file = Path(__file__).parent.parent / persona_path
    if not persona_file.exists():
        raise FileNotFoundError(f"Persona file not found: {persona_path}")

    return persona_file.read_text(encoding="utf-8")
```

### 10. **Mermaid Diagram Support**

When implementing diagram features:

**Diagram Generation:**

```python
def generate_mermaid_workflow(steps: List[str]) -> str:
    """Generate Mermaid diagram for workshop workflow."""
    diagram = "graph TD\n"
    for i, step in enumerate(steps, 1):
        diagram += f"    Step{i}[{step}]\n"
        if i < len(steps):
            diagram += f"    Step{i} --> Step{i+1}\n"
    return diagram
```

### 11. **Azure Deployment Considerations**

When modifying infrastructure or deployment:

**Bicep Template Updates:**

- Update model deployments in `infra/resources.bicep` when adding new AI models
- Ensure environment variables are properly configured in App Service settings
- Test deployment changes with `azd provision` before committing

**GitHub Actions:**

- Maintain required secrets and variables as documented in README
- Test federated authentication setup for secure deployment

## Testing Guidelines

Currently, this project doesn't have a formal testing framework. When adding tests:

**Recommended Testing Structure:**

```
tests/
├── unit/
│   ├── test_agent_manager.py
│   ├── test_config_loader.py
│   └── test_persona_loader.py
├── integration/
│   ├── test_chainlit_integration.py
│   └── test_azure_openai.py
└── fixtures/
    ├── sample_config.yaml
    └── sample_persona.md
```

**Mock External Dependencies:**

```python
# Mock Azure OpenAI calls in tests
@patch('openai.AsyncClient')
async def test_agent_response(mock_client):
    """Test agent response generation."""
    mock_client.return_value.chat.completions.create.return_value = MockResponse()
```

## Documentation Requirements

### 12. **Documentation Updates**

When making changes, ensure corresponding documentation is updated:

- **README.md**: Update installation, configuration, and usage instructions
- **Agent Documentation**: Update persona files and example configurations
- **Configuration Schema**: Update JSON schema files when adding new configuration options
- **Deployment Guides**: Update Azure deployment and GitHub Actions documentation

### 13. **Code Comments**

Add comments for complex workshop logic, AI model interactions, and configuration parsing:

```python
# Parse multi-document configuration for agents that need
# access to multiple knowledge sources (e.g., bank policies + procedures)
documents = config.get("documents", [])
if documents:
    # Load each document and combine for comprehensive context
    combined_context = await self._load_multiple_documents(documents)
```

By following these comprehensive guidelines, we ensure that the AI Discovery Workshop Facilitator codebase remains maintainable, extensible, and aligned with the project's specific requirements for workshop facilitation and multi-agent AI interactions.
