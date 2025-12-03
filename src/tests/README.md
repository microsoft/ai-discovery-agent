# Testing Guide for AI Discovery Workshop Agent

This document provides guidance on running and understanding the test suite for the AI Discovery Workshop Agent.

## Overview

The project now includes a comprehensive test suite with both unit tests and integration tests to ensure code quality and reduce regressions.

## Test Structure

```
tests/
├── unit/                     # Unit tests for isolated component testing
│   ├── test_auth.py         # Authentication module tests
│   ├── test_agent_manager.py # Agent manager tests
│   ├── test_config_validation.py # Configuration validation tests
│   └── test_utils.py        # Utility modules tests
├── integration/             # Integration tests for component interaction
│   ├── test_auth_integration.py    # Authentication flow integration
│   ├── test_agent_integration.py  # Agent management integration
│   └── test_chat_integration.py   # Chat handling integration
└── fixtures/                # Test data and shared utilities
    ├── data.py              # Sample configurations and mock data
    └── __init__.py
```

## Running Tests

### Prerequisites

Ensure you have installed the development dependencies:

```bash
cd src
uv sync --group dev
```

### Run All Tests

```bash
cd src
source .venv/bin/activate
python -m pytest tests/ -v
```

### Run Specific Test Categories

**Unit Tests Only:**

```bash
python -m pytest tests/unit/ -v
```

**Integration Tests Only:**

```bash
python -m pytest tests/integration/ -v
```

**Specific Module:**

```bash
python -m pytest tests/unit/test_auth.py -v
```

### Test Coverage

To run tests with coverage reporting:

```bash
python -m pytest tests/ --cov=. --cov-report=html
```

This generates an HTML coverage report in `htmlcov/index.html`.

## Test Categories

### Unit Tests

Unit tests focus on testing individual components in isolation using mocks and stubs:

- **Authentication Tests** (`test_auth.py`):

  - Password authentication with bcrypt
  - OAuth authentication flows
  - Configuration loading and error handling

- **Agent Manager Tests** (`test_agent_manager.py`):

  - Configuration loading from YAML files
  - Role-based agent access control
  - Agent switching functionality

- **Configuration Validation Tests** (`test_config_validation.py`):

  - YAML file existence and validity
  - Agent and page definition consistency
  - Persona and document file existence
  - Model and temperature value validation
  - URL path and agent key uniqueness
  - See [unit/README_CONFIG_VALIDATION.md](unit/README_CONFIG_VALIDATION.md) for details

- **Utils Tests** (`test_utils.py`):
  - Configuration loading utilities
  - Logging setup functionality
  - Program information parsing

### Integration Tests

Integration tests verify that components work correctly together with real file operations and data flows:

- **Authentication Integration** (`test_auth_integration.py`):

  - End-to-end authentication with real file operations
  - Error handling with malformed configurations
  - OAuth environment detection

- **Agent Integration** (`test_agent_integration.py`):

  - Complete agent switching workflows
  - Role-based access control flows
  - Configuration validation with real YAML files

- **Chat Integration** (`test_chat_integration.py`):
  - Chat profile setup for different user roles
  - Session initialization workflows
  - Message routing structure validation

## Mocking Strategy

The test suite uses extensive mocking to isolate components:

- **Chainlit Components**: Mocked to avoid UI dependencies
- **File Operations**: Mocked for unit tests, real files for integration tests
- **Environment Variables**: Patched for testing different configurations
- **External Dependencies**: Azure OpenAI, bcrypt, and other external services

## Test Data

Test fixtures in `tests/fixtures/data.py` provide:

- Sample agent configurations
- Mock user data (regular and admin users)
- Authentication configurations
- Reusable mock objects

## Writing New Tests

### Unit Test Guidelines

1. Use `unittest.mock` for dependencies
2. Test one component at a time
3. Follow the AAA pattern (Arrange, Act, Assert)
4. Use descriptive test method names

Example:

```python
def test_component_behavior_when_condition(self):
    """Test that component behaves correctly under specific condition."""
    # Arrange
    mock_dependency = Mock()

    # Act
    result = component.method(mock_dependency)

    # Assert
    assert result == expected_value
```

### Integration Test Guidelines

1. Test component interactions
2. Use temporary files for file operations
3. Clean up resources in fixtures
4. Test complete workflows

### Test Naming Convention

- Test files: `test_<module_name>.py`
- Test classes: `Test<ComponentName>`
- Test methods: `test_<behavior>_<condition>`

## Continuous Integration

The test suite is designed to run in CI/CD environments:

- All tests use relative imports
- No external service dependencies
- Proper cleanup of temporary resources
- Cross-platform compatibility

## Troubleshooting

### Common Issues

**Import Errors**: Ensure you're running tests from the `src/` directory with the virtual environment activated.

**Mock Failures**: Verify mock paths match the actual import structure used in the code.

**Async Test Issues**: Use `pytest-asyncio` and proper `async`/`await` syntax.

### Debugging Tests

Run tests with additional verbosity:

```bash
python -m pytest tests/ -vv -s
```

Run a specific test:

```bash
python -m pytest tests/unit/test_auth.py::TestPasswordAuthentication::test_password_auth_callback_success -v
```

## Future Improvements

Potential enhancements to the test suite:

- Add performance tests for large configurations
- Implement property-based testing with Hypothesis
- Add end-to-end tests with a test Chainlit server
- Extend coverage to include LangChain agent implementations
- Add mutation testing to verify test quality
