# Security Review Checklist

> **Purpose:** Ensure all changes undergo appropriate security review
> **Use:** Reference this checklist for PRs, releases, and architecture changes

## 1. Code Changes Review

### General Security
- [ ] No hardcoded secrets, passwords, or API keys in code
- [ ] Environment variables used for sensitive configuration
- [ ] Input validation implemented for all user inputs
- [ ] Output encoding/sanitization applied where needed
- [ ] Error messages don't reveal sensitive information
- [ ] Logging doesn't capture PII or secrets

### Authentication & Authorization
- [ ] Authentication required for all protected endpoints
- [ ] Authorization checks enforce least privilege
- [ ] Session management is secure (secure cookies, timeouts)
- [ ] Password policies meet security standards (if applicable)
- [ ] OAuth flows validate redirect URIs
- [ ] No authentication bypass vulnerabilities

### Data Handling
- [ ] Data encrypted in transit (TLS 1.2+)
- [ ] Data encrypted at rest (where applicable)
- [ ] PII identified and properly handled
- [ ] Data retention policies followed
- [ ] Secure data deletion implemented
- [ ] No data leakage in logs or error messages

### Dependencies
- [ ] All dependencies up to date (or exceptions documented)
- [ ] Dependabot alerts reviewed and addressed
- [ ] No known vulnerabilities in dependencies
- [ ] Package sources are trusted and verified
- [ ] Lock files committed and up to date

---

## 2. Infrastructure Changes Review

### Network Security
- [ ] Private endpoints configured for data services
- [ ] VNet integration enabled for App Service
- [ ] Network security groups properly configured
- [ ] Default deny rules in place
- [ ] Public access disabled unless required
- [ ] TLS 1.2+ enforced on all services

### Identity & Access Management
- [ ] Managed identities used (no stored credentials)
- [ ] RBAC roles follow least privilege
- [ ] No Owner or Contributor roles assigned unnecessarily
- [ ] Service principals scoped appropriately
- [ ] Role assignments documented and justified

### Resource Configuration
- [ ] HTTPS enforced on web services
- [ ] FTP/FTPS disabled on App Service
- [ ] Diagnostic logging enabled
- [ ] Monitoring and alerting configured
- [ ] Backup and disaster recovery planned
- [ ] Resource tags applied consistently

### Compliance
- [ ] Checkov scan passes (or exceptions documented)
- [ ] Azure Policy compliance verified
- [ ] Security baseline requirements met
- [ ] Audit logging enabled
- [ ] Data residency requirements satisfied

---

## 3. AI-Specific Security Review

### Prompt Security
- [ ] System prompts protected from injection
- [ ] Input validation prevents prompt manipulation
- [ ] Output filtering prevents information leakage
- [ ] Content safety features enabled (Azure OpenAI)
- [ ] Prompt Shield integrated (if applicable)

### Model Security
- [ ] Model access properly restricted (RBAC)
- [ ] Rate limiting configured
- [ ] Token usage monitored
- [ ] Model outputs logged appropriately
- [ ] PII redaction considered for sensitive data

### Data Privacy
- [ ] User conversations isolated per user
- [ ] No cross-user data access possible
- [ ] Azure OpenAI data privacy guarantees understood
- [ ] Customer data not used for training
- [ ] Data export/deletion capabilities implemented

---

## 4. Testing Requirements

### Security Testing
- [ ] Unit tests include security scenarios
- [ ] Integration tests cover authentication flows
- [ ] SAST scan (Bandit) passes
- [ ] CodeQL scan passes (no new findings)
- [ ] Dependency scan passes (Dependabot)
- [ ] Manual security testing performed (if major changes)

### Functional Testing
- [ ] All existing tests pass
- [ ] New tests added for new features
- [ ] Edge cases covered
- [ ] Error handling tested
- [ ] Performance testing completed (if applicable)

---

## 5. Documentation Requirements

### Security Documentation
- [ ] Security implications documented
- [ ] Threat model updated (if architecture changed)
- [ ] Security baseline updated (if controls changed)
- [ ] Runbook updated (if operational changes)

### Code Documentation
- [ ] Security-sensitive code commented
- [ ] API documentation updated
- [ ] Configuration examples updated
- [ ] README updated (if user-facing changes)

---

## 6. Deployment Review

### Pre-Deployment
- [ ] Changes tested in staging environment
- [ ] Security scans completed successfully
- [ ] Rollback plan documented
- [ ] Monitoring dashboards prepared
- [ ] Incident response plan reviewed

### Post-Deployment
- [ ] Health checks passing
- [ ] Security configuration verified
- [ ] Monitoring alerts configured
- [ ] Logs being captured correctly
- [ ] Performance metrics normal

---

## 7. Compliance Sign-off

### Required Approvals

**For Code Changes:**
- [ ] Code review by team member (required)
- [ ] Security review by security champion (for security-sensitive changes)
- [ ] Architecture review (for architectural changes)

**For Infrastructure Changes:**
- [ ] Infrastructure review by platform team (required)
- [ ] Security review by security team (required for networking/IAM changes)
- [ ] Compliance review (for regulated data or major changes)

**For Production Deployments:**
- [ ] Change advisory board approval (if applicable)
- [ ] Security sign-off
- [ ] Business stakeholder approval

---

## 8. Risk Assessment

### Change Risk Level

**Low Risk** (Examples):
- Documentation updates
- UI text changes
- Bug fixes with no security impact
- Dependency updates (minor versions)

**Medium Risk** (Examples):
- New features with authentication
- Configuration changes
- Dependency updates (major versions)
- Database schema changes

**High Risk** (Examples):
- Authentication/authorization changes
- Network security changes
- IAM policy changes
- Major architectural changes
- New external integrations

### Risk Mitigation

For **Medium** or **High** risk changes:
- [ ] Additional testing performed
- [ ] Staged rollout planned (if applicable)
- [ ] Enhanced monitoring during deployment
- [ ] Rollback plan tested
- [ ] On-call engineer available during deployment

---

## 9. STRIDE Threat Analysis (for Major Changes)

### Spoofing
- [ ] Identity verification mechanisms reviewed
- [ ] Authentication flows secure
- [ ] No credential storage vulnerabilities

### Tampering
- [ ] Data integrity protections in place
- [ ] Configuration tampering prevented
- [ ] Audit logging for changes

### Repudiation
- [ ] Actions are logged with user context
- [ ] Audit trail cannot be modified
- [ ] Non-repudiation mechanisms in place

### Information Disclosure
- [ ] No sensitive data exposure
- [ ] Proper access controls
- [ ] Encryption properly configured

### Denial of Service
- [ ] Rate limiting implemented
- [ ] Resource limits configured
- [ ] DDoS protections in place

### Elevation of Privilege
- [ ] Authorization checks in place
- [ ] Least privilege enforced
- [ ] No privilege escalation paths

---

## 10. Security Incident Readiness

### Incident Response
- [ ] Security contacts updated
- [ ] Incident response plan accessible
- [ ] Logs retention configured properly
- [ ] Alerting configured for security events
- [ ] Runbook for common incidents updated

### Monitoring
- [ ] Security metrics defined
- [ ] Dashboards configured
- [ ] Alerts for anomalous behavior
- [ ] Log queries for threat hunting
- [ ] Compliance monitoring enabled

---

## Review Sign-off

**Reviewer Name:** ___________________________
**Date:** ___________________________
**Risk Level:** ⬜ Low  ⬜ Medium  ⬜ High
**Security Approved:** ⬜ Yes  ⬜ Yes with conditions  ⬜ No

**Notes/Conditions:**
```
[Add any conditions or notes here]
```

---

## Appendix: Quick Reference

### Security Scanning Commands
```bash
# Bicep security scan
cd infra && checkov -d . --framework bicep

# Python SAST scan
cd src && uv run bandit -x .venv -s B101 -r .

# Run all tests
cd src && uv run pytest

# Check dependencies
cd src && uv pip list --outdated
```

### Common Security Issues
- Hardcoded secrets → Use environment variables or Key Vault
- Missing authentication → Add authentication decorator/middleware
- SQL injection → Use parameterized queries (or N/A for NoSQL)
- XSS → Use output encoding/sanitization
- CSRF → Use anti-CSRF tokens
- Weak passwords → Enforce password policy

### Useful Links
- [STRIDE Threat Model](../security/STRIDE_THREAT_MODEL.md)
- [Security Baseline](../security/SECURITY_BASELINE.md)
- [DAST Guide](../security/DAST_GUIDE.md)
- [ARCHITECTURE.md](../../ARCHITECTURE.md)
- [Microsoft SDL](https://www.microsoft.com/en-us/securityengineering/sdl)
