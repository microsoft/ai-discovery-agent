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

## Best Practices for Copilot Task Assignment

When creating issues or tasks for Copilot to work on, follow these guidelines to ensure the best results:

### Ideal Tasks for Copilot

**✅ Good Candidates:**
- Bug fixes with clear reproduction steps
- Adding unit or integration tests for existing functionality
- Documentation updates and improvements
- Code refactoring that follows established patterns
- Implementing new features based on existing patterns
- Accessibility improvements
- Performance optimizations with clear metrics
- Configuration updates following existing schemas

**❌ Avoid Assigning:**
- Complex architectural changes requiring new design decisions
- Security-critical authentication or authorization logic changes
- Production-critical hotfixes without thorough review
- Tasks requiring business domain expertise not documented in the codebase
- Cross-repository changes
- Changes requiring access to external systems or secrets

### Writing Effective Issue Descriptions

**Good Issue Template:**
```markdown
## Problem
Clear description of what needs to be fixed or implemented

## Expected Behavior
Specific, measurable outcomes

## Files Involved
- List of files that likely need changes
- Reference similar implementations if applicable

## Acceptance Criteria
- [ ] Specific requirement 1
- [ ] Tests added/updated
- [ ] Documentation updated
- [ ] Linting and formatting passes
```

**Example - Good Issue:**
```markdown
Title: Add unit tests for cached_loader.py

## Problem
The cached_loader module lacks comprehensive unit test coverage

## Expected Behavior
- All public methods in cached_loader.py should have unit tests
- Edge cases (empty cache, expired cache) should be tested
- Mock external file system calls

## Files Involved
- src/aida/utils/cached_loader.py (target)
- tests/unit/test_cached_loader.py (reference for patterns)

## Acceptance Criteria
- [ ] Test coverage > 90% for cached_loader.py
- [ ] All tests pass
- [ ] Follow existing pytest patterns in tests/unit/
```

**Example - Bad Issue:**
```markdown
Title: Improve the app

The app needs to be better and faster.
```

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

### 5. **General Linting Rules**

Follow [Ruff](https://ruff.rs/) linting rules as specified in the `pyproject.toml` file. Address all warnings and errors reported by Ruff before committing code.

Ensure that pre-commit rules are followed, including import sorting, unused imports removal, and code complexity checks.

## Project-Specific Development Guidelines

### Copyright and Licensing

All code contributions must include the following copyright header:

```
Copyright (c) Microsoft Corporation.
Licensed under the MIT license.
```

For example, in each Python file, include the following at the top:

```python
# Copyright (c) Microsoft Corporation.
# Licensed under the MIT license.
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

## Build, Test, and Validation Workflow

### Local Development Setup

**Prerequisites:**
```bash
# Python 3.12 required
python --version  # Should be 3.12+

# Install uv for dependency management
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Setup Steps:**
```bash
cd src
uv sync                          # Install all dependencies including dev tools
uv run pre-commit install        # Install pre-commit hooks
```

### Running Quality Checks

**Before Committing Changes:**

```bash
# 1. Run pre-commit hooks (Black, Ruff, file checks)
uv run pre-commit run --all-files

# 2. Run linting
uv run ruff check .

# 3. Run type checking (if applicable)
uv run -m compileall src/

# 4. Run tests with coverage
uv run pytest tests/ -v --cov=aida --cov-report=term-missing

# 5. Run security checks
uv run bandit -r aida/ -f sarif -o bandit-results.sarif
```

**Fix Common Issues:**
```bash
# Auto-fix linting issues
uv run ruff check --fix .

# Auto-format code
uv run black .

# Check for missing copyright headers
./scripts/check-copyright-headers.sh
```

### CI/CD Pipeline

**Continuous Integration (`.github/workflows/01-ci.yml`):**
- Runs on all PRs and pushes (except to `main`)
- Steps:
  1. Pre-commit hooks (Black, Ruff, YAML checks)
  2. Copyright header validation
  3. Python compilation check
  4. Full test suite (pytest)
  5. Security scans (Bandit, Checkov, CodeQL)

**Continuous Deployment (`.github/workflows/02-ci-cd.yml`):**
- Runs on pushes to `main` branch
- Steps:
  1. Build and provision Azure infrastructure
  2. Deploy to staging slot
  3. Manual approval required for production swap

**Security Scanning:**
- `03-checkov-security.yml` - Infrastructure as Code security
- `04-bandit-security.yml` - Python code security
- `codeql.yml` - Advanced code analysis

### Testing Philosophy

**Test Structure:**
```
tests/
├── unit/           # Fast, isolated unit tests (no external deps)
├── integration/    # Tests with mocked external services
└── fixtures/       # Shared test data and mocks
```

**Test Requirements:**
- All new features must include unit tests
- Integration tests for complex workflows
- Mock Azure OpenAI and Storage calls in tests
- Aim for >80% code coverage on new code
- Tests must be fast (<10 seconds for unit tests)

**Example Test Pattern:**
```python
@pytest.mark.asyncio
async def test_feature(mock_azure_client):
    """Test description following docstring conventions."""
    # Arrange
    mock_azure_client.return_value = expected_response

    # Act
    result = await function_under_test()

    # Assert
    assert result == expected_value
    mock_azure_client.assert_called_once()
```

## Security Considerations for AI/LLM Applications

### Prompt Injection Prevention

**Never trust user input in prompts:**
```python
# ❌ BAD - Vulnerable to prompt injection
prompt = f"User said: {user_input}"

# ✅ GOOD - Use structured messages with roles
messages = [
    {"role": "system", "content": system_persona},
    {"role": "user", "content": user_input}  # Clearly separated
]
```

### Azure OpenAI Security

**API Key Management:**
- Use Managed Identity for Azure resources (preferred)
- Never commit API keys to repository
- Store secrets in `.env` file (gitignored)
- Use environment variables for all sensitive configuration

**Rate Limiting and Cost Control:**
```python
# Implement token limits and caching
from aida.utils.cached_llm import get_cached_llm

llm = get_cached_llm(
    max_tokens=1000,          # Limit response size
    temperature=0.7,          # Consistent with config
)
```

### Data Privacy

**Conversation Storage:**
- Conversations stored in Azure Blob Storage
- Use private endpoints for data plane access
- Enable encryption at rest (default)
- Implement role-based access control (RBAC)

**PII Handling:**
- Do not log user messages verbatim
- Sanitize logs of sensitive information
- Follow data retention policies
- Implement proper access controls for stored conversations

### Security Checklist for PRs

- [ ] No secrets or API keys in code
- [ ] All external inputs validated and sanitized
- [ ] Azure OpenAI calls use appropriate safety settings
- [ ] Prompt injection mitigations in place
- [ ] Tests include security edge cases
- [ ] Dependencies updated (no known vulnerabilities)
- [ ] Security scans pass (Bandit, CodeQL, Checkov)

## Common Pitfalls and Troubleshooting

### Agent Configuration Issues

**Problem:** Agent fails to load persona or document files

**Solution:**
```python
# Verify file paths are relative to project root
persona_path = Path(__file__).parent.parent / "prompts" / "persona.md"
if not persona_path.exists():
    raise FileNotFoundError(f"Persona not found: {persona_path}")
```

**Problem:** YAML configuration not validating

**Solution:**
- Check against `pages.schema.json`
- Use YAML language server comments
- Validate with example files in `config/`

### Azure OpenAI Connection Issues

**Problem:** `ResourceNotFoundError` when calling Azure OpenAI

**Common Causes:**
1. Model deployment name mismatch
2. Missing environment variables
3. Incorrect API version

**Solution:**
```bash
# Verify environment variables
echo $AZURE_OPENAI_ENDPOINT
echo $AZURE_OPENAI_API_VERSION
echo $AZURE_OPENAI_API_KEY  # Should not be empty

# Check model deployment names match infra/resources.bicep
```

### Chainlit Session Issues

**Problem:** Session data not persisting between messages

**Solution:**
```python
# Always use cl.user_session for state management
import chainlit as cl

@cl.on_chat_start
async def start():
    # Initialize session state
    cl.user_session.set("agent_manager", agent_manager)

@cl.on_message
async def main(message: cl.Message):
    # Retrieve from session
    agent_manager = cl.user_session.get("agent_manager")
```

### Test Failures

**Problem:** Tests fail with Azure Storage errors

**Solution:**
- Use Azurite for local testing
- Mock Azure Storage calls in unit tests
- Check `AZURE_STORAGE_CONNECTION_STRING` in `.env`

**Problem:** Async tests hanging or timing out

**Solution:**
```python
# Use pytest-asyncio properly
@pytest.mark.asyncio
async def test_async_function():
    # Ensure awaiting all async calls
    result = await async_function()
```

### Deployment Issues

**Problem:** GitHub Actions deployment fails on provision step

**Common Causes:**
1. Missing Azure credentials or OIDC configuration
2. Insufficient permissions on Azure subscription
3. Resource naming conflicts

**Solution:**
- Check GitHub secrets and variables are configured
- Verify service principal has Contributor role
- Ensure `resourceToken` is unique in your environment

## Quick Reference: Common Commands

**Development:**
```bash
uv run -m chainlit run -dhw chainlit_app.py    # Run app locally
uv run pytest tests/ -v                        # Run all tests
uv run ruff check --fix .                      # Lint and fix
uv run black .                                 # Format code
```

**Testing:**
```bash
uv run pytest tests/unit/ -v                   # Unit tests only
uv run pytest tests/integration/ -v            # Integration tests only
uv run pytest --cov=aida --cov-report=html     # Coverage report
```

**Azure Deployment:**
```bash
azd auth login                                 # Login to Azure
azd provision                                  # Create/update infrastructure
azd deploy                                     # Deploy to staging
azd up                                         # Provision + deploy
```

**Quality Checks:**
```bash
uv run pre-commit run --all-files              # All pre-commit hooks
./scripts/check-copyright-headers.sh           # Copyright headers
./scripts/generate-notice.sh --no-dev          # Update NOTICE file
```

By following these comprehensive guidelines, we ensure that the AI Discovery Workshop Facilitator codebase remains maintainable, extensible, and aligned with the project's specific requirements for workshop facilitation and multi-agent AI interactions.
