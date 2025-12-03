# Configuration Validation Tests

## Purpose

The `test_config_validation.py` test suite validates the integrity of the `config/pages.yaml` configuration file to prevent runtime errors due to:

- Missing or invalid configuration files
- Undefined agent references
- Missing persona or document files
- Invalid model names or temperature values
- Duplicate agent keys or URL paths
- Misconfigured pages

## Running the Tests

From the project root or src directory:

```bash
# Run all configuration validation tests
cd src && uv run pytest tests/unit/test_config_validation.py -v

# Run a specific test
cd src && uv run pytest tests/unit/test_config_validation.py::TestConfigurationValidation::test_all_page_agents_are_defined -v
```

## Test Coverage

### File Existence Tests

- `test_config_file_exists`: Ensures `config/pages.yaml` exists
- `test_config_is_valid_yaml`: Validates YAML syntax
- `test_agent_persona_files_exist`: Verifies all persona files exist
- `test_agent_document_files_exist`: Verifies all document files exist

### Configuration Integrity Tests

- `test_config_has_required_sections`: Checks for 'agents' and 'sections'
- `test_all_agents_have_required_fields`: Validates agent configurations
- `test_all_page_agents_are_defined`: **Critical** - Ensures pages only reference defined agents
- `test_all_pages_have_required_fields`: Validates page configurations

### Graph Agent Tests

- `test_graph_agents_reference_valid_agents`: Ensures graph agents reference valid sub-agents

### Uniqueness Tests

- `test_no_duplicate_agent_keys`: Prevents duplicate agent definitions
- `test_no_duplicate_url_paths`: Prevents URL conflicts

### Value Validation Tests

- `test_model_names_are_valid`: Validates Azure OpenAI model names
- `test_temperature_values_are_valid`: Ensures temperatures are in range [0.0, 2.0]
- `test_admin_only_pages_are_properly_marked`: Validates boolean flags
- `test_at_least_one_default_page`: Ensures at least one default page exists

## Common Issues Detected

### Issue 1: Undefined Agent Reference (CURRENT)

**Error**: Page references agent that doesn't exist in agents section

**Example**:

```
Pages reference undefined agents:
  - Section 'Customers': Page 'Auto Claims Call Center' references undefined agent 'auto_claims_call_center'
```

**Cause**: Agent is defined as `auto_claims_customer` but page references `auto_claims_call_center`

**Fix**: Update the agent key in the agents section to match the page reference:

```yaml
agents:
  auto_claims_call_center: # Changed from auto_claims_customer
    persona: prompts/auto_claims_customer_persona.md
    document: prompts/auto_claims_damage_report_use_case.md
    temperature: 0.5
    model: gpt-4o
```

### Issue 2: Missing Persona/Document Files

**Error**: Referenced file doesn't exist

**Example**:

```
Missing persona files:
  - facilitator: prompts/facilitator_persona.md
```

**Fix**: Create the missing file or update the path in configuration

### Issue 3: Invalid Model Name

**Error**: Model name doesn't match expected patterns

**Example**:

```
Agents with potentially invalid model names:
  - my_agent: gpt-5-turbo
```

**Fix**: Use a valid Azure OpenAI model name (gpt-4o, gpt-4o-mini, etc.)

### Issue 4: Invalid Temperature Value

**Error**: Temperature outside valid range

**Example**:

```
Agents with invalid temperature values:
  - my_agent: temperature 3.0 out of range [0.0, 2.0]
```

**Fix**: Set temperature between 0.0 and 2.0

## Integration with CI/CD

These tests should be run as part of the CI pipeline to catch configuration errors before deployment:

```yaml
# Example GitHub Actions step
- name: Validate Configuration
  run: |
    cd src
    uv run pytest tests/unit/test_config_validation.py -v
```

## Benefits

1. **Early Error Detection**: Catches configuration errors during development, not at runtime
2. **Clear Error Messages**: Provides specific information about what's wrong and where
3. **Prevents Deployment Issues**: Ensures configuration is valid before deploying to production
4. **Documentation**: Tests serve as documentation of configuration requirements
5. **Prevents User-Facing Errors**: Avoids errors like "Agent not found in registry"

## Future Enhancements

Potential additions to the test suite:

- [ ] Validate JSON schema compliance
- [ ] Check for orphaned prompt files (files not referenced in config)
- [ ] Validate icon emoji format
- [ ] Check URL path formatting (no spaces, special chars)
- [ ] Validate subtitle length (UX consideration)
- [ ] Test configuration loading performance
- [ ] Validate graph agent condition syntax
- [ ] Check for circular references in graph agents
