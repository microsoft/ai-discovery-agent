# Chainlit Application

This is a Chainlit application that utilizes various agents to process user inputs and generate responses. The application is built using the Chainlit framework and integrates with LangChain for advanced language model capabilities.

## Architecture

The application has been refactored into modular components for improved maintainability:

- **`main.py`** - Application entry point and global state management
- **`auth.py`** - Authentication logic (password & OAuth)
- **`chat_handlers.py`** - Chainlit event handlers and message processing
- **`utils/config.py`** - Configuration loading utilities
- **`utils/logging_setup.py`** - Logging setup utilities
- **`chainlit_app.py`** - Legacy compatibility layer (for existing deployment scripts)

## Dependencies

- `chainlit>=2.8.0` - Main framework for the web application
- `bcrypt>=4.3.0` - Password hashing
- `python-dotenv>=1.1.0` - Environment variable loading
- `openai>=1.104.2` - OpenAI API integration
- `azure-identity>=1.23.0` - Azure authentication
- `langchain>=0.3.27` - Language model framework
- `PyYAML>=6.0.2` - YAML configuration parsing

## Configuration Files

- `config/auth-config.yaml` - Authentication configuration
- `config/pages.yaml` - Page structure and agent configuration

## Testing

The application includes a comprehensive test suite with both unit and integration tests:

### Quick Start

```bash
# Install test dependencies
uv sync --group dev

# Run all tests
uv run pytest tests/ -v

# Run specific test categories
uv run pytest tests/unit/ -v          # Unit tests only
uv run pytest tests/integration/ -v   # Integration tests only
uv run pytest tests/ --cov=. --cov-report=html --cov-report=term  # Tests with coverage report
```

### Manual Test Execution

```bash
# Run with pytest directly
uv run pytest tests/ -v

# Run specific test files
uv run pytest tests/unit/test_auth.py -v
```

### Test Structure

- `tests/unit/` - Unit tests for isolated component testing
- `tests/integration/` - Integration tests for component interaction
- `tests/fixtures/` - Test data and reusable utilities
- `tests/README.md` - Detailed testing documentation

The test suite covers:

- Authentication flows (password and OAuth)
- Agent configuration management
- Role-based access control
- Chat session handling
- Error scenarios and edge cases

Tests use mocking to isolate components and ensure reliable, fast execution without external dependencies.

## Code Quality and Formatting

The project uses pre-commit hooks to maintain code quality and consistent formatting. To review and fix all formatting mistakes across the entire codebase:

```bash
# Review and automatically fix formatting issues
uv run pre-commit run --all-files
```

This command will:

- Check and fix code formatting (Black)
- Lint code for style issues (Ruff)
- Validate YAML files
- Check for common issues like trailing whitespace
- Ensure consistent line endings

Run this command before committing changes to ensure your code meets the project's quality standards.
