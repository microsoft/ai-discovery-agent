# STRIDE Threat Model Analysis

> **Last Updated:** October 2025
> **Scope:** AI Discovery Workshop Facilitator Infrastructure
> **Reference:** [Microsoft STRIDE Threat Modeling](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)

## Executive Summary

This document provides a comprehensive STRIDE threat model analysis for the AI Discovery Workshop Facilitator system. It identifies potential security threats across six categories and documents existing mitigations and recommended controls.

## System Architecture Overview

The AI Discovery Workshop Facilitator is a multi-agent AI system built on:
- **Frontend:** Chainlit web application (Python/FastAPI)
- **Compute:** Azure App Service (Linux, Python 3.12)
- **AI Services:** Azure OpenAI (GPT-4o, GPT-4o-mini, embeddings)
- **Storage:** Azure Blob Storage (conversation persistence)
- **Networking:** Azure Virtual Network with private endpoints
- **Identity:** System-assigned managed identities
- **Monitoring:** Azure Application Insights & Log Analytics

## STRIDE Analysis

### S - Spoofing (Identity Threats)

#### Threat 1.1: Unauthorized User Access
**Description:** Attacker attempts to impersonate a legitimate user to access workshop sessions.

**Attack Vectors:**
- Weak password authentication
- Stolen OAuth tokens
- Session hijacking
- Missing multi-factor authentication

**Current Mitigations:**
- ✅ Password authentication with bcrypt hashing (`auth.py`)
- ✅ OAuth integration (GitHub, Microsoft)
- ✅ HTTPS enforced (TLS 1.2 minimum)
- ✅ Chainlit session management
- ✅ Session secrets generated per environment

**Risk Level:** MEDIUM
**Residual Risk:** LOW (with OAuth enabled)

**Recommendations:**
- [ ] Enforce MFA for production environments
- [ ] Implement session timeout policies
- [ ] Add rate limiting for authentication attempts
- [ ] Enable Azure AD Conditional Access policies

---

#### Threat 1.2: Service Identity Spoofing
**Description:** Attacker attempts to impersonate the App Service to access Azure resources.

**Attack Vectors:**
- Stolen managed identity tokens
- Compromised application code
- Token replay attacks

**Current Mitigations:**
- ✅ System-assigned managed identity (no stored credentials)
- ✅ Scoped RBAC roles (Cognitive Services OpenAI User, Storage Blob Data Contributor)
- ✅ disableLocalAuth on Azure OpenAI
- ✅ Private endpoints for data plane isolation

**Risk Level:** LOW

**Recommendations:**
- [x] Already using best practices
- [ ] Enable Azure AD PIM for administrative access
- [ ] Implement workload identity rotation monitoring

---

### T - Tampering (Data Integrity Threats)

#### Threat 2.1: Infrastructure Configuration Tampering
**Description:** Attacker modifies Bicep templates or deployment configurations.

**Attack Vectors:**
- Compromised CI/CD pipeline
- Insider threat with repository access
- Supply chain attack on dependencies

**Current Mitigations:**
- ✅ GitHub OIDC federation (no static secrets)
- ✅ Protected branches (main, dev)
- ✅ PR review requirements
- ✅ Checkov infrastructure scanning
- ✅ CodeQL for code analysis
- ✅ Dependabot for dependency updates

**Risk Level:** MEDIUM

**Recommendations:**
- [ ] Enable branch protection rules requiring signed commits
- [ ] Implement infrastructure drift detection
- [ ] Add Azure Policy for runtime compliance
- [ ] Regular security audits of GitHub Actions workflows

---

#### Threat 2.2: Conversation Data Tampering
**Description:** Attacker modifies stored workshop conversations in Azure Blob Storage.

**Attack Vectors:**
- Direct blob access with stolen credentials
- Application vulnerability allowing unauthorized writes
- Container-level permission escalation

**Current Mitigations:**
- ✅ Storage account network ACLs (default deny)
- ✅ Private endpoint for storage
- ✅ System-assigned managed identity (least privilege)
- ✅ Role-based access (Storage Blob Data Contributor)
- ✅ HTTPS enforced
- ✅ Encryption at rest enabled

**Risk Level:** LOW

**Recommendations:**
- [ ] Enable Azure Storage versioning/soft delete
- [ ] Implement blob immutability policies for compliance
- [ ] Add storage access logging and alerting
- [ ] Consider Azure Storage firewall IP restrictions

---

#### Threat 2.3: AI Model Output Manipulation
**Description:** Attacker manipulates prompt templates or model configurations.

**Attack Vectors:**
- Code injection through configuration files
- Prompt injection attacks
- Template file tampering

**Current Mitigations:**
- ✅ Persona files stored in source control
- ✅ Configuration validation in YAML
- ✅ Bandit SAST scanning for code vulnerabilities
- ✅ Content Safety features in Azure OpenAI

**Risk Level:** MEDIUM

**Recommendations:**
- [ ] Implement prompt injection detection
- [ ] Add input validation for user messages
- [ ] Enable Azure OpenAI content filtering
- [ ] Implement output validation rules
- [ ] Add LLM security testing (prompt injection resilience)

---

### R - Repudiation (Non-Repudiation Threats)

#### Threat 3.1: User Action Repudiation
**Description:** User denies performing sensitive actions (data export, session deletion).

**Attack Vectors:**
- Lack of audit logging
- Insufficient activity tracking
- Shared accounts

**Current Mitigations:**
- ✅ Application Insights telemetry
- ✅ App Service diagnostic logs
- ✅ Azure Activity Logs for infrastructure changes
- ✅ User authentication required

**Risk Level:** MEDIUM

**Recommendations:**
- [ ] Implement detailed audit logging for user actions
- [ ] Enable Azure Monitor alerts for sensitive operations
- [ ] Add structured logging with user context
- [ ] Implement log retention policies (90+ days for compliance)
- [ ] Create audit trail for data access and modifications

---

### I - Information Disclosure (Confidentiality Threats)

#### Threat 4.1: Unauthorized Data Access
**Description:** Attacker gains access to sensitive workshop data or AI model responses.

**Attack Vectors:**
- Storage account public exposure
- Weak network controls
- API key leakage
- Debug information in logs

**Current Mitigations:**
- ✅ Public blob access disabled
- ✅ Private endpoints for OpenAI and Storage
- ✅ Virtual Network integration
- ✅ Default deny network ACLs
- ✅ Managed identity (no secrets in code)
- ✅ TLS 1.2+ enforced
- ✅ Secret scanning in CI/CD

**Risk Level:** LOW

**Recommendations:**
- [ ] Enable Azure Key Vault for sensitive configuration
- [ ] Implement PII detection and redaction
- [ ] Add data classification labels
- [ ] Enable Azure Defender for Storage
- [ ] Regular penetration testing

---

#### Threat 4.2: Secrets Exposure
**Description:** API keys, connection strings, or tokens exposed in code or logs.

**Attack Vectors:**
- Hardcoded secrets
- Secrets in version control
- Verbose logging exposing tokens
- Environment variable leakage

**Current Mitigations:**
- ✅ No API keys in code (managed identity)
- ✅ Environment variables for configuration
- ✅ GitHub secret scanning enabled
- ✅ Pre-commit hooks for secret detection
- ✅ .gitignore for sensitive files

**Risk Level:** LOW

**Recommendations:**
- [ ] Migrate all secrets to Azure Key Vault
- [ ] Implement secret rotation policies
- [ ] Add runtime secret scanning
- [ ] Enable Azure Policy to prevent credential exposure

---

#### Threat 4.3: Model Data Leakage
**Description:** Sensitive workshop data leaked through AI model training or logging.

**Attack Vectors:**
- Azure OpenAI training on customer data (if opt-in enabled)
- Verbose telemetry exposing PII
- Model prompt/response logging

**Current Mitigations:**
- ✅ Azure OpenAI data privacy guarantees (no training on customer data by default)
- ✅ Private deployment (publicNetworkAccess: Disabled)
- ✅ Selective logging configuration

**Risk Level:** LOW

**Recommendations:**
- [ ] Implement PII scrubbing for telemetry
- [ ] Document data residency policies
- [ ] Enable Azure OpenAI abuse monitoring
- [ ] Add content filtering rules

---

### D - Denial of Service (Availability Threats)

#### Threat 5.1: Application Layer DoS
**Description:** Attacker overwhelms the application with requests.

**Attack Vectors:**
- HTTP flood attacks
- Excessive API calls to Azure OpenAI
- Resource exhaustion (memory, CPU)
- Slowloris attacks

**Current Mitigations:**
- ✅ Azure App Service autoscaling (S1 tier)
- ✅ Azure OpenAI rate limiting (per-deployment quotas)
- ✅ Health check endpoint (/health)
- ✅ Application Insights monitoring

**Risk Level:** MEDIUM

**Recommendations:**
- [ ] Implement Azure Front Door with WAF
- [ ] Add rate limiting per user/session
- [ ] Enable Azure DDoS Protection Standard
- [ ] Configure resource limits (memory, request timeouts)
- [ ] Implement circuit breakers for Azure OpenAI calls

---

#### Threat 5.2: Resource Quota Exhaustion
**Description:** Attacker exhausts Azure OpenAI quotas or storage limits.

**Attack Vectors:**
- Excessive token consumption
- Large file uploads
- Conversation spam

**Current Mitigations:**
- ✅ Azure OpenAI deployment capacity limits (100 TPM)
- ✅ Storage account monitoring
- ✅ Application Insights metrics

**Risk Level:** MEDIUM

**Recommendations:**
- [ ] Implement per-user token budgets
- [ ] Add file upload size limits
- [ ] Enable quota alerts and throttling
- [ ] Implement conversation cleanup policies

---

### E - Elevation of Privilege (Authorization Threats)

#### Threat 6.1: Horizontal Privilege Escalation
**Description:** User accesses another user's workshop sessions or data.

**Attack Vectors:**
- Insecure direct object references
- Missing authorization checks
- Session fixation

**Current Mitigations:**
- ✅ User session isolation in Chainlit
- ✅ Role-based access control (admin vs regular users)
- ✅ Agent access control by user role

**Risk Level:** MEDIUM

**Recommendations:**
- [ ] Implement resource-level authorization checks
- [ ] Add unit tests for authorization logic
- [ ] Enable Azure RBAC at storage container level
- [ ] Audit all data access patterns

---

#### Threat 6.2: Infrastructure Privilege Escalation
**Description:** Attacker gains elevated permissions in Azure infrastructure.

**Attack Vectors:**
- Compromised service principal
- Overly permissive RBAC roles
- Azure AD privilege escalation

**Current Mitigations:**
- ✅ Least privilege managed identity roles
- ✅ No Owner/Contributor role assignments to app
- ✅ Scoped role assignments to specific resources
- ✅ GitHub OIDC federation (time-limited tokens)

**Risk Level:** LOW

**Recommendations:**
- [ ] Regular RBAC audit and review
- [ ] Enable Azure AD PIM for just-in-time access
- [ ] Implement Azure Policy guardrails
- [ ] Alert on role assignment changes

---

## Risk Summary

| Threat Category | High Risk | Medium Risk | Low Risk | Total |
|-----------------|-----------|-------------|----------|-------|
| Spoofing        | 0         | 1           | 1        | 2     |
| Tampering       | 0         | 2           | 1        | 3     |
| Repudiation     | 0         | 1           | 0        | 1     |
| Info Disclosure | 0         | 0           | 3        | 3     |
| Denial of Service | 0       | 2           | 0        | 2     |
| Elevation of Privilege | 0  | 1           | 1        | 2     |
| **TOTAL**       | **0**     | **7**       | **6**    | **13** |

## Security Posture Assessment

### Strengths
1. ✅ **Strong Identity Management:** System-assigned managed identities eliminate credential management risks
2. ✅ **Network Isolation:** Private endpoints and VNet integration provide defense in depth
3. ✅ **Secure CI/CD:** OIDC federation and automated security scanning
4. ✅ **Infrastructure as Code:** Bicep templates with Checkov validation
5. ✅ **Zero Local Auth:** Azure OpenAI disables key-based authentication

### Areas for Improvement
1. ⚠️ **Application-Layer Security:** Add WAF, rate limiting, and DDoS protection
2. ⚠️ **Audit & Monitoring:** Enhanced logging for compliance and incident response
3. ⚠️ **Prompt Security:** Implement prompt injection detection and validation
4. ⚠️ **Secret Management:** Migrate to Azure Key Vault for all secrets
5. ⚠️ **Testing:** Add security-specific tests (fuzzing, penetration testing)

## Implementation Roadmap

### Phase 1: Critical (0-30 days)
- [ ] Implement rate limiting and request throttling
- [ ] Add comprehensive audit logging with user context
- [ ] Enable Azure Storage soft delete and versioning
- [ ] Implement prompt injection detection

### Phase 2: Important (30-90 days)
- [ ] Deploy Azure Front Door with WAF
- [ ] Migrate secrets to Azure Key Vault
- [ ] Add security-specific integration tests
- [ ] Implement PII detection and redaction

### Phase 3: Enhancement (90+ days)
- [ ] Enable Azure DDoS Protection Standard
- [ ] Implement automated penetration testing
- [ ] Add advanced threat analytics
- [ ] Deploy runtime application security monitoring

## Compliance Considerations

### Microsoft SFI (Security Future Initiative)
- ✅ Secure by Default: Private endpoints, managed identities, HTTPS-only
- ✅ Secure by Design: STRIDE analysis, least privilege architecture
- ⚠️ Secure Operations: Enhance monitoring, audit logging, incident response

### Responsible AI
- ✅ Content Safety: Azure OpenAI content filtering available
- ⚠️ Transparency: Add audit trails for AI-generated content
- ⚠️ Accountability: Implement PII redaction and data governance

## References

1. [Microsoft STRIDE Threat Modeling Tool](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
2. [Azure Security Baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines)
3. [OWASP Top 10](https://owasp.org/www-project-top-ten/)
4. [Azure OpenAI Service Security](https://learn.microsoft.com/en-us/azure/ai-services/openai/security)
5. [Microsoft Security Development Lifecycle](https://www.microsoft.com/en-us/securityengineering/sdl)

---

**Document Ownership:** Security Team
**Review Cycle:** Quarterly or upon major architectural changes
**Next Review:** January 2026
