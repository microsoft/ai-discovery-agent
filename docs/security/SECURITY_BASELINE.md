# Security Baseline & Controls

> **Purpose:** Document baseline security controls and configurations for the AI Discovery Workshop Facilitator
> **Last Updated:** October 2025

## Overview

This document establishes the security baseline for the AI Discovery Workshop Facilitator system, documenting implemented controls, configuration standards, and validation procedures.

## 1. Infrastructure Security (IaC)

### 1.1 Azure Bicep Security

**Tool:** Checkov (Bridgecrew)
**Configuration:** `.github/workflows/03-bicep-security.yml`
**Scan Frequency:** On every PR and push to release branches

**Implemented Checks:**
- ✅ Network security controls (private endpoints, VNet integration)
- ✅ Identity and access management (managed identities, RBAC)
- ✅ Data encryption (at rest and in transit)
- ✅ Logging and monitoring configuration
- ✅ Compliance with Azure security baselines

**Suppressed Checks (with justification):**
```bicep
// CKV_AZURE_17: App Service requires HTTPS (already enforced via httpsOnly: true)
// CKV_AZURE_212: App Service requires client certificates (not required for this workload)
// CKV_AZURE_222: App Service requires VNET integration (implemented)
// CKV_AZURE_225: App Service Plan zone redundancy (cost optimization trade-off)
```

**Validation:**
```bash
cd infra
checkov -d . --framework bicep --quiet
```

### 1.2 Network Security Controls

| Control | Configuration | Status |
|---------|--------------|--------|
| **Virtual Network** | Dedicated VNet with app and private subnets | ✅ Implemented |
| **Private Endpoints** | Azure OpenAI, Storage Account | ✅ Implemented |
| **VNet Integration** | App Service connected to app subnet | ✅ Implemented |
| **Storage Firewall** | Default deny, allow from VNet | ✅ Implemented |
| **TLS Version** | Minimum TLS 1.2 enforced | ✅ Implemented |
| **HTTPS Only** | Enforced on App Service | ✅ Implemented |
| **Public Access** | Disabled for OpenAI and Storage | ✅ Implemented |

**Configuration Details:**

```bicep
// Private Endpoint for Azure OpenAI
resource azureOpenAI 'Microsoft.CognitiveServices/accounts@2024-04-01-preview' = {
  properties: {
    publicNetworkAccess: 'Disabled'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}

// App Service Security
resource web 'Microsoft.Web/sites@2024-11-01' = {
  properties: {
    httpsOnly: true
    virtualNetworkSubnetId: vnet.outputs.appSubnetId
  }
  siteConfig: {
    minTlsVersion: '1.2'
    ftpsState: 'Disabled'
  }
}
```

### 1.3 Identity & Access Management

**Managed Identity Configuration:**
- Type: System-assigned
- Scope: Per-resource (App Service production, App Service staging)
- Credential Management: Azure-managed (no stored secrets)

**RBAC Role Assignments:**

| Principal | Role | Scope | Justification |
|-----------|------|-------|--------------|
| App Service (prod) | Cognitive Services OpenAI User | Azure OpenAI | Model inference only |
| App Service (prod) | Storage Blob Data Contributor | Storage Account | Conversation persistence |
| App Service (staging) | Cognitive Services OpenAI User | Azure OpenAI | Testing |
| App Service (staging) | Storage Blob Data Contributor | Storage Account | Testing |
| Local Developer | Cognitive Services OpenAI User | Azure OpenAI | Development |

**Key Security Features:**
- ✅ `disableLocalAuth: true` on Azure OpenAI (no API keys)
- ✅ Scoped role assignments (no Owner/Contributor)
- ✅ Separate identities for production and staging
- ✅ Just-in-time access via Azure CLI for developers

### 1.4 Data Protection

| Control | Implementation | Validation |
|---------|---------------|------------|
| **Encryption at Rest** | Azure Storage encryption (Microsoft-managed keys) | Default enabled |
| **Encryption in Transit** | TLS 1.2+ enforced | App Service config |
| **Public Blob Access** | Disabled at account level | Storage config |
| **Data Isolation** | Private endpoints, VNet | Network config |
| **Backup** | Not currently implemented | ⚠️ Recommended |

**Storage Account Security:**
```bicep
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  properties: {
    allowBlobPublicAccess: false
    minimumTlsVersion: 'TLS1_2'
    networkAcls: {
      defaultAction: 'Deny'
      bypass: 'AzureServices'
    }
  }
}
```

---

## 2. Application Security (SAST)

### 2.1 Python Security Scanning

**Tool:** Bandit
**Configuration:** `.github/workflows/01-ci.yml`
**Scan Frequency:** On every PR and push

**Bandit Configuration:**
```bash
uv run bandit -c .tools/.bandit.yml -r .
```

**Suppressions:**
- `B101`: Assert statements (allowed in test code)

**Common Findings & Mitigations:**

| Finding | Severity | Mitigation |
|---------|----------|------------|
| Use of `assert` | Low | Suppressed for tests (B101) |
| Hardcoded passwords | High | None found (using bcrypt + env vars) |
| SQL injection | High | Not applicable (no SQL) |
| Shell injection | Medium | Avoided, using safe APIs |

**Validation:**
```bash
cd src
uv run bandit -x .venv -s B101 -r .
```

### 2.2 Code Quality & Static Analysis

**Tool:** CodeQL (GitHub Advanced Security)
**Configuration:** `.github/workflows/codeql.yml`
**Scan Frequency:** Weekly + on PRs

**Languages Analyzed:**
- Python (primary application code)
- JavaScript/TypeScript (Chainlit frontend)
- GitHub Actions (workflow security)

**Security Queries:**
- CWE-22: Path traversal
- CWE-79: Cross-site scripting (XSS)
- CWE-89: SQL injection
- CWE-327: Use of broken crypto
- CWE-798: Hardcoded credentials

**Configuration:**
```yaml
- name: Initialize CodeQL
  uses: github/codeql-action/init@v3
  with:
    languages: ${{ matrix.language }}
    queries: security-extended  # Can enable security-and-quality
```

### 2.3 Pre-commit Security Hooks

**Configuration:** `.tools/.pre-commit-config.yaml`

**Hooks:**
- `check-yaml`: Validate YAML files
- `end-of-file-fixer`: Ensure proper file endings
- `trailing-whitespace`: Remove trailing whitespace
- `detect-private-key`: Prevent committing private keys
- `black`: Python code formatting
- `ruff`: Python linting and security checks

**Validation:**
```bash
pre-commit run --all-files
```

---

## 3. Dependency Security

### 3.1 Dependabot Configuration

**Configuration:** `.github/dependabot.yml`

```yaml
version: 2
updates:
  - package-ecosystem: "uv"
    directory: "/src"
    schedule:
      interval: daily
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule:
      interval: daily
```

**Security Features:**
- ✅ Daily vulnerability scans
- ✅ Automatic PR creation for updates
- ✅ GitHub Advisory Database integration
- ✅ Transitive dependency scanning

### 3.2 Python Dependencies

**Package Manager:** uv
**Lock File:** `src/uv.lock`

**Security Practices:**
- ✅ Pinned versions in lockfile
- ✅ Regular updates via Dependabot
- ✅ Pre-commit hooks for validation

**High-Risk Dependencies (monitored):**
- `openai`: Azure OpenAI SDK
- `chainlit`: Web framework
- `fastapi`: API framework
- `bcrypt`: Password hashing

**Validation:**
```bash
cd src
uv pip check  # Check for dependency conflicts
uv pip list --outdated  # Check for updates
```

---

## 4. Secrets Management

### 4.1 Secret Storage

**Current Implementation:**

| Secret Type | Storage Method | Rotation | Status |
|-------------|---------------|----------|--------|
| Azure OpenAI API Key | Not used (managed identity) | N/A | ✅ Best practice |
| Storage Account Key | Not used (managed identity) | N/A | ✅ Best practice |
| Chainlit Auth Secret | Environment variable (auto-generated) | Per environment | ✅ Acceptable |
| OAuth Client Secrets | Environment variable (manual) | Manual | ⚠️ Migrate to Key Vault |

**Recommendations:**
- [ ] Migrate OAuth secrets to Azure Key Vault
- [ ] Implement automatic secret rotation
- [ ] Use Key Vault references in App Service

### 4.2 Secret Scanning

**GitHub Secret Scanning:**
- ✅ Enabled for repository
- ✅ Alerts for leaked secrets
- ✅ Push protection (if enabled)

**Pre-commit Hook:**
```yaml
- id: detect-private-key
  name: Detect Private Keys
```

**Validation:**
```bash
git secrets --scan  # If installed
pre-commit run detect-private-key --all-files
```

---

## 5. CI/CD Security

### 5.1 GitHub Actions Security

**Authentication Method:** OIDC Federation (Workload Identity)

**Benefits:**
- ✅ No stored secrets in GitHub
- ✅ Short-lived tokens
- ✅ Scoped to specific workflows
- ✅ Azure AD audit trail

**Federated Credentials:**
```bicep
federatedCredentials: [
  {
    name: 'github-actions-dev-${resourceToken}'
    issuer: 'https://token.actions.githubusercontent.com'
    subject: 'repo:${repository}:environment:dev'
    audiences: ['api://AzureADTokenExchange']
  }
  // ... additional environments
]
```

### 5.2 Workflow Security

**Permissions Model:**
```yaml
permissions:
  contents: read      # Checkout code
  security-events: write  # Upload SARIF results
  checks: write       # Publish test results
  pull-requests: write  # Comment on PRs
```

**Security Best Practices:**
- ✅ Least privilege permissions per workflow
- ✅ Pinned action versions (by SHA recommended)
- ✅ Concurrency controls to prevent race conditions
- ✅ Protected branches with required checks

### 5.3 Deployment Security

**Staging Slot Strategy:**
1. Deploy to staging slot
2. Run smoke tests
3. Manual validation
4. Slot swap to production

**Benefits:**
- ✅ Zero-downtime deployments
- ✅ Rollback capability
- ✅ Production validation before release

---

## 6. Monitoring & Logging

### 6.1 Application Insights

**Telemetry Collection:**
- Request telemetry (HTTP requests)
- Dependency telemetry (Azure OpenAI calls)
- Exception telemetry
- Custom events (user actions)
- Performance metrics

**Configuration:**
```python
APPLICATIONINSIGHTS_CONNECTION_STRING = os.getenv("APPLICATIONINSIGHTS_CONNECTION_STRING")
```

**Retention:** 30 days (configurable)

### 6.2 App Service Diagnostics

**Log Types:**
- Application logs (Verbose level)
- HTTP logs (enabled)
- Detailed error messages (enabled)
- Failed request tracing (enabled)

**Configuration:**
```bicep
resource logs 'config' = {
  name: 'logs'
  properties: {
    applicationLogs: {
      fileSystem: { level: 'Verbose' }
    }
    httpLogs: {
      fileSystem: {
        enabled: true
        retentionInDays: 1
        retentionInMb: 35
      }
    }
  }
}
```

### 6.3 Azure Monitor

**Log Analytics Workspace:**
- Centralized log collection
- KQL query capabilities
- Alert rules (to be configured)

**Recommended Alerts:**
- [ ] Failed authentication attempts (rate-based)
- [ ] Azure OpenAI throttling events
- [ ] Storage access failures
- [ ] Application exceptions
- [ ] Role assignment changes

---

## 7. Security Testing

### 7.1 Current Test Coverage

**Unit Tests:** `src/tests/unit/`
- Authentication logic
- Agent configuration
- Utility functions

**Integration Tests:** `src/tests/integration/`
- Authentication flows
- Agent management
- Chat handling

**Test Execution:**
```bash
cd src
uv run pytest --junit-xml pytest.xml
```

**Coverage:** Run `pytest --cov` for coverage report

### 7.2 Security-Specific Tests

**Recommended Test Additions:**

1. **Authentication Security:**
   - [ ] Brute force protection
   - [ ] Session fixation prevention
   - [ ] Token expiration validation

2. **Input Validation:**
   - [ ] Prompt injection detection
   - [ ] XSS prevention in chat messages
   - [ ] File upload validation

3. **Authorization:**
   - [ ] Role-based access control
   - [ ] Resource ownership validation
   - [ ] Privilege escalation prevention

4. **API Security:**
   - [ ] Rate limiting effectiveness
   - [ ] Request size limits
   - [ ] CORS policy validation

---

## 8. Compliance & Governance

### 8.1 Security Frameworks

**Microsoft SFI (Security Future Initiative):**
- ✅ Secure by Default
- ✅ Secure by Design
- ⚠️ Secure Operations (in progress)

**OWASP ASVS (Application Security Verification Standard):**
- Level 1: Partially implemented
- Level 2: In progress
- Level 3: Not applicable (standard web app)

### 8.2 Data Privacy

**GDPR Considerations:**
- [ ] Data minimization
- [ ] Right to erasure (delete conversations)
- [ ] Data portability (export conversations)
- [ ] Consent management
- [ ] Privacy by design

**PII Handling:**
- ⚠️ PII detection not implemented
- ⚠️ PII redaction not implemented
- [ ] Implement Azure Cognitive Services PII detection

### 8.3 Responsible AI

**Azure OpenAI Responsible AI:**
- ✅ Content filtering available
- ✅ Abuse monitoring enabled
- ✅ Data residency controls
- ⚠️ Transparency features (in progress)

**Recommendations:**
- [ ] Document AI system card
- [ ] Implement fairness evaluation
- [ ] Add explainability features
- [ ] Create responsible AI governance

---

## 9. Incident Response

### 9.1 Security Incident Procedures

**Detection:**
1. Azure Monitor alerts
2. Application Insights anomalies
3. GitHub security alerts
4. User reports

**Response:**
1. Assess severity and impact
2. Isolate affected resources
3. Collect evidence (logs, metrics)
4. Remediate vulnerability
5. Post-incident review

**Contacts:**
- Security Team: [Configure]
- On-call Engineer: [Configure]
- Microsoft Security Response: security@microsoft.com

### 9.2 Disaster Recovery

**Backup Strategy:**
- ⚠️ Storage backup not implemented
- ✅ Infrastructure as Code (rebuild capability)
- ✅ Staging slot (quick rollback)

**Recommendations:**
- [ ] Enable Azure Storage soft delete (30 days)
- [ ] Implement Azure Backup for Storage
- [ ] Document DR procedures
- [ ] Test recovery procedures quarterly

---

## 10. Security Validation Checklist

### Pre-deployment Validation

- [ ] Checkov scan passes (or findings documented)
- [ ] CodeQL scan passes
- [ ] Bandit scan passes
- [ ] Dependency vulnerabilities addressed
- [ ] Pre-commit hooks enabled
- [ ] Unit and integration tests pass
- [ ] Secrets not in code or logs

### Post-deployment Validation

- [ ] Private endpoints in "Approved" state
- [ ] Storage firewall rules correct
- [ ] Role assignments verified
- [ ] Application Insights collecting telemetry
- [ ] Health check endpoint responding
- [ ] Authentication working (password & OAuth)
- [ ] HTTPS enforced
- [ ] TLS version validated

### Periodic Reviews (Quarterly)

- [ ] STRIDE threat model review
- [ ] RBAC role assignments audit
- [ ] Dependency updates applied
- [ ] Security findings triaged
- [ ] Incident response plan tested
- [ ] DR procedures validated

---

## References

1. [Azure Security Baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/)
2. [OWASP ASVS](https://owasp.org/www-project-application-security-verification-standard/)
3. [Microsoft SDL](https://www.microsoft.com/en-us/securityengineering/sdl)
4. [CIS Azure Foundations Benchmark](https://www.cisecurity.org/benchmark/azure)

---

**Document Owner:** Platform Engineering Team
**Last Security Audit:** October 2025
**Next Audit:** January 2026
