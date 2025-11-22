# Configuration Guide

This document describes the configuration file formats used by the AI Discovery Agent application.

## Table of Contents

- [Pages Configuration](#pages-configuration)
- [Authentication Configuration](#authentication-configuration)
- [Environment Variables](#environment-variables)

## Pages Configuration

The pages configuration file (`config/pages.yaml`) defines the available agents and their navigation structure. This file uses YAML format and follows a specific schema.

### File Location

- **Production**: `config/pages.yaml`
- **Example**: `config/pages-example.yaml`
- **Schema**: `config/pages.schema.json`

### Structure Overview

```yaml
# yaml-language-server: $schema=./pages.schema.json

agents:
  # Agent definitions go here

sections:
  # Navigation sections go here
```

### Agent Definitions

Agents are AI assistants with specific personas and knowledge bases. Each agent can be configured in one of three ways:

#### 1. Single Agent (Persona Only)

A simple agent with just a persona definition:

```yaml
agents:
  facilitator:
    persona: prompts/facilitator_persona.md
    model: gpt-4o              # Optional: defaults to gpt-4o
    temperature: 0.7            # Optional: defaults to 1.0
```

#### 2. Single Agent with Document

An agent with a persona and a single knowledge document:

```yaml
agents:
  customer_rep:
    persona: prompts/contoso_zermatt_national_bank_persona.md
    document: prompts/contoso_zermatt_national_bank.md
    model: gpt-4o-mini          # Optional
    temperature: 0.5            # Optional
```

#### 3. Multi-Document Agent

An agent with access to multiple knowledge documents:

```yaml
agents:
  multi_doc_expert:
    persona: prompts/expert_persona.md
    documents:
      - prompts/domain_knowledge.md
      - prompts/best_practices.md
      - prompts/reference_guide.md
    model: gpt-4o               # Optional
    temperature: 0.8            # Optional
```

#### 4. Graph Agent (Conditional Routing)

A sophisticated agent that routes requests to specialized sub-agents based on conditions:

```yaml
agents:
  routing_agent:
    condition: "Analyze the user's input and determine the appropriate specialist"
    agents:
      - agent: technical_expert
        condition: technical
      - agent: business_expert
        condition: business
      - agent: general_assistant
        condition: general
    model: gpt-4o               # Optional
    temperature: 0.5            # Optional
```

### Agent Configuration Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `persona` | string | Yes (for single agents) | Path to the persona prompt file (markdown) |
| `document` | string | No | Path to a single knowledge document |
| `documents` | array of strings | No | Paths to multiple knowledge documents |
| `condition` | string | Yes (for graph agents) | Routing condition prompt for graph agents |
| `agents` | array of objects | Yes (for graph agents) | Sub-agent routing configurations |
| `model` | string | No | Azure OpenAI model deployment name (default: "gpt-4o") |
| `temperature` | float | No | Response randomness 0.0-2.0 (default: 1.0) |

### Section Configuration

Sections organize agents in the navigation interface. Each section contains one or more pages.

```yaml
sections:
  Coach:
    - type: agent
      agent: facilitator
      title: Facilitator
      icon: 🧑‍🏫
      url_path: Facilitator
      header: 🧑‍🏫 AI Discovery Workshop Facilitator
      subtitle: I'm your AI Design Thinking Expert and can guide you through the AI Discovery Workshop step by step.
      admin_only: true          # Optional: restrict to admin users
      default: false            # Optional: set as default agent

  Customers:
    - type: agent
      agent: customer_rep
      title: Bank Representative
      icon: 🏦
      url_path: BankRepresentative
      header: 🏦 Contoso Zermatt National Bank Representative
      subtitle: Ask me anything about our bank, internal processes and our day-to-day jobs.
```

### Page Configuration Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `type` | string | Yes | Page type (currently only "agent" is supported) |
| `agent` | string | Yes | Agent key from the agents section |
| `title` | string | Yes | Display title in navigation |
| `icon` | string | Yes | Emoji or icon for the page |
| `url_path` | string | Yes | URL path segment for the page |
| `header` | string | Yes | Header text displayed on the page |
| `subtitle` | string | Yes | Subtitle or description text |
| `admin_only` | boolean | No | If true, only users with "admin" role can access (default: false) |
| `default` | boolean | No | If true, this agent is selected by default (default: false) |

### Complete Example

```yaml
# yaml-language-server: $schema=./pages.schema.json

agents:
  # Simple facilitator agent
  facilitator:
    persona: prompts/facilitator_persona.md
    model: gpt-4o
    temperature: 0.7

  # Agent with single document
  bank_expert:
    persona: prompts/bank_persona.md
    document: prompts/bank_knowledge.md
    model: gpt-4o-mini

  # Multi-document agent
  comprehensive_expert:
    persona: prompts/expert_persona.md
    documents:
      - prompts/policies.md
      - prompts/procedures.md
      - prompts/guidelines.md

  # Graph routing agent
  smart_router:
    condition: "Route to appropriate specialist based on query type"
    agents:
      - agent: bank_expert
        condition: banking
      - agent: facilitator
        condition: workshop
    model: gpt-4o
    temperature: 0.5

sections:
  Coaching:
    - type: agent
      agent: facilitator
      title: Workshop Facilitator
      icon: 🧑‍🏫
      url_path: Facilitator
      header: 🧑‍🏫 AI Discovery Workshop Facilitator
      subtitle: Guide through the AI Discovery Workshop process
      default: true

  Experts:
    - type: agent
      agent: bank_expert
      title: Banking Expert
      icon: 🏦
      url_path: BankingExpert
      header: 🏦 Banking Specialist
      subtitle: Expert in banking operations and policies

    - type: agent
      agent: comprehensive_expert
      title: Comprehensive Expert
      icon: 📚
      url_path: ComprehensiveExpert
      header: 📚 Multi-Domain Expert
      subtitle: Access to comprehensive knowledge base

  Advanced:
    - type: agent
      agent: smart_router
      title: Smart Router
      icon: 🤖
      url_path: SmartRouter
      header: 🤖 Intelligent Routing Agent
      subtitle: Automatically routes to the best specialist
      admin_only: true
```

## Authentication Configuration

The authentication configuration file (`config/auth-config.yaml`) defines user credentials and roles for password-based authentication.

### File Location

- **Production**: `config/auth-config.yaml`
- **Example**: `config/auth-config-example.yaml`

### Structure

```yaml
credentials:
  usernames:
    # Username as key
    admin:
      first_name: John
      last_name: Doe
      password: admin-pass      # Will be auto-hashed on first use
      roles:
        - admin
        - user

    attendee:
      first_name: Jane
      last_name: Smith
      password: attendee-pass   # Will be auto-hashed on first use
      roles:
        - user
```

### User Configuration Properties

| Property | Type | Required | Description |
|----------|------|----------|-------------|
| `first_name` | string | No | User's first name |
| `last_name` | string | No | User's last name |
| `password` | string | Yes | User password (plain text on first use, will be hashed automatically) |
| `roles` | array of strings | No | User roles (e.g., "admin", "user") |

### Password Security

- **Initial Setup**: Passwords can be entered as plain text in the configuration file
- **Auto-Hashing**: On first successful login, passwords are automatically hashed using PBKDF2-SHA256
- **Storage**: Hashed passwords are stored back to the configuration file
- **Format**: `pbkdf2_sha256$<base64-encoded-salt-and-hash>`
- **Security**: Uses 100,000 iterations with 256-bit salt (OWASP recommended)

### Roles

Common roles include:

- `admin`: Full access to all features and admin-only agents
- `user`: Standard user access

Additional custom roles can be defined as needed for your organization.

### Example

```yaml
credentials:
  usernames:
    workshop_admin:
      first_name: Workshop
      last_name: Administrator
      password: secure-admin-password
      roles:
        - admin
        - user

    workshop_user:
      first_name: Workshop
      last_name: Participant
      password: secure-user-password
      roles:
        - user

    demo_user:
      first_name: Demo
      last_name: User
      password: demo-password
      # No roles specified - defaults to empty array
```

## Environment Variables

The application uses environment variables for sensitive configuration and runtime settings. These should be configured in a `.env` file (never committed to version control).

### Required Variables

#### Azure OpenAI Configuration

```bash
# Azure OpenAI endpoint URL
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/

# API version to use
AZURE_OPENAI_API_VERSION=2025-01-01-preview

# Model deployment name (optional, can be set per agent)
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

#### Authentication

```bash
# Secret key for Chainlit authentication (auto-generated if not set)
CHAINLIT_AUTH_SECRET=your-secret-key-here
```

### Optional Variables

#### Development Settings

```bash
# Enable local development mode (uses DefaultAzureCredential)
LOCAL_DEVELOPMENT=true

# Environment name
AZURE_ENV_NAME=dev
```

#### OAuth Configuration

Enable OAuth providers by setting their client credentials:

```bash
# GitHub OAuth
OAUTH_GITHUB_CLIENT_ID=your-github-client-id
OAUTH_GITHUB_CLIENT_SECRET=your-github-client-secret

# Google OAuth
OAUTH_GOOGLE_CLIENT_ID=your-google-client-id
OAUTH_GOOGLE_CLIENT_SECRET=your-google-client-secret

# Azure AD OAuth
OAUTH_AZURE_AD_CLIENT_ID=your-azure-ad-client-id
OAUTH_AZURE_AD_CLIENT_SECRET=your-azure-ad-client-secret
OAUTH_AZURE_AD_TENANT_ID=your-tenant-id
```

See [Chainlit OAuth Documentation](https://docs.chainlit.io/docs/authentication/oauth) for complete OAuth setup instructions.

#### Azure Storage (Conversation Persistence)

```bash
# Azure Storage connection string for conversation persistence
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=...

# Or use account name and key separately
AZURE_STORAGE_ACCOUNT_NAME=your-storage-account
AZURE_STORAGE_ACCOUNT_KEY=your-storage-key
```

#### Azure Table Storage

```bash
# Azure Table Storage endpoint for conversation metadata
AZURE_TABLE_STORAGE_ENDPOINT=https://your-account.table.core.windows.net/
```

### Environment File Example

Create a `.env` file in the project root:

```bash
# Azure OpenAI
AZURE_OPENAI_ENDPOINT=https://my-openai.openai.azure.com/
AZURE_OPENAI_API_VERSION=2025-01-01-preview
AZURE_OPENAI_DEPLOYMENT=gpt-4o

# Authentication
CHAINLIT_AUTH_SECRET=randomly-generated-secret-key

# Development
LOCAL_DEVELOPMENT=true

# Azure Storage (optional, for conversation persistence)
AZURE_STORAGE_CONNECTION_STRING=DefaultEndpointsProtocol=https;AccountName=myaccount;AccountKey=...
AZURE_TABLE_STORAGE_ENDPOINT=https://myaccount.table.core.windows.net/
```

## Best Practices

### Configuration Files

1. **Never commit secrets**: Use `.env` files for sensitive data
2. **Use examples**: Maintain example files (`.example.env`, `pages-example.yaml`)
3. **Validate schema**: Use YAML language server with schema validation
4. **Document changes**: Update this guide when adding new configuration options

### Security

1. **Password Management**:
   - Use strong passwords in production
   - Consider migrating to OAuth for production deployments
   - Regularly rotate passwords

2. **Environment Variables**:
   - Never commit `.env` files
   - Use Azure Key Vault for production secrets
   - Rotate Azure OpenAI keys regularly

3. **Access Control**:
   - Use `admin_only` flag to restrict sensitive agents
   - Define appropriate user roles
   - Review access permissions regularly

### Performance

1. **Model Selection**:
   - Use `gpt-4o-mini` for simple tasks to reduce costs
   - Use `gpt-4o` for complex reasoning tasks
   - Set appropriate temperature values (lower for deterministic responses)

2. **Document Management**:
   - Keep document files reasonably sized
   - Use multi-document agents sparingly (increases token usage)
   - Cache prompt files using the built-in caching mechanism

## Troubleshooting

### Common Issues

1. **Agent not appearing**: Check that the agent is referenced in a section
2. **Authentication fails**: Verify password format and hashing
3. **Model errors**: Ensure AZURE_OPENAI_DEPLOYMENT matches actual deployment name
4. **Permission denied**: Check user roles and `admin_only` flags
5. **YAML parse errors**: Validate against schema using YAML language server

### Debugging

Enable debug logging by setting the log level in your environment or code:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Additional Resources

- [Chainlit Documentation](https://docs.chainlit.io/)
- [Azure OpenAI Documentation](https://learn.microsoft.com/azure/ai-services/openai/)
- [LangChain Documentation](https://python.langchain.com/)
- [Project README](../README.md)
