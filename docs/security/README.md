# Security Documentation

This directory contains comprehensive security documentation for the AI Discovery Workshop Facilitator system.

## Documents Overview

### 📋 [STRIDE_THREAT_MODEL.md](STRIDE_THREAT_MODEL.md)
**Purpose:** Complete threat modeling using Microsoft STRIDE methodology

**Contents:**
- STRIDE analysis across all six threat categories:
  - **S**poofing (Identity threats)
  - **T**ampering (Data integrity threats)
  - **R**epudiation (Non-repudiation threats)
  - **I**nformation Disclosure (Confidentiality threats)
  - **D**enial of Service (Availability threats)
  - **E**levation of Privilege (Authorization threats)
- Current mitigations and risk assessments
- Recommendations and implementation roadmap
- Risk summary and security posture assessment

**When to Use:**
- Before major architectural changes
- During security assessments
- When evaluating new features
- For security training and awareness

---

### 🛡️ [SECURITY_BASELINE.md](SECURITY_BASELINE.md)
**Purpose:** Document baseline security controls and configurations

**Contents:**
- Infrastructure security (Bicep/IaC)
- Application security (SAST with Bandit, CodeQL)
- Network security controls
- Identity and access management
- Data protection measures
- Dependency security (Dependabot)
- Secrets management
- CI/CD security
- Monitoring and logging
- Security testing practices
- Compliance and governance

**When to Use:**
- Setting up new environments
- Configuration audits
- Onboarding new team members
- Security compliance checks
- During deployments

---

### 🔍 [DAST_GUIDE.md](DAST_GUIDE.md)
**Purpose:** Dynamic Application Security Testing guide and recommendations

**Contents:**
- DAST tools recommendations (OWASP ZAP, Burp Suite, Nuclei)
- Testing categories:
  - Authentication & session management
  - Input validation & injection testing
  - **Prompt injection testing** (AI-specific)
  - API security testing
  - WebSocket security
- CI/CD integration strategies
- Azure-specific DAST considerations
- AI-specific security testing
- Implementation roadmap

**When to Use:**
- Before production deployments
- Regular security testing (weekly/quarterly)
- Penetration testing preparation
- Security incident investigation

---

### ✅ [SECURITY_REVIEW_CHECKLIST.md](SECURITY_REVIEW_CHECKLIST.md)
**Purpose:** Comprehensive checklist for security reviews

**Contents:**
- Code changes review criteria
- Infrastructure changes review
- AI-specific security review
- Testing requirements
- Documentation requirements
- Deployment review process
- Compliance sign-off procedures
- Risk assessment framework
- STRIDE analysis quick reference
- Security incident readiness

**When to Use:**
- Every pull request review
- Pre-deployment verification
- Change approval process
- Security audits
- Incident response

---

## Quick Start

### For Developers

**Before Submitting a PR:**
1. Review [SECURITY_REVIEW_CHECKLIST.md](SECURITY_REVIEW_CHECKLIST.md)
2. Run security scans:
   ```bash
   # Python SAST
   cd src && uv run bandit -x .venv -s B101 -r .
   
   # Run tests
   cd src && uv run pytest
   ```
3. Ensure no secrets in code
4. Update security documentation if needed

**For New Features:**
1. Review [STRIDE_THREAT_MODEL.md](STRIDE_THREAT_MODEL.md) for relevant threats
2. Consult [SECURITY_BASELINE.md](SECURITY_BASELINE.md) for required controls
3. Update threat model if architecture changes

---

### For Security Engineers

**Security Assessment:**
1. Start with [STRIDE_THREAT_MODEL.md](STRIDE_THREAT_MODEL.md)
2. Verify controls in [SECURITY_BASELINE.md](SECURITY_BASELINE.md)
3. Conduct DAST using [DAST_GUIDE.md](DAST_GUIDE.md)
4. Use [SECURITY_REVIEW_CHECKLIST.md](SECURITY_REVIEW_CHECKLIST.md) for findings

**Regular Reviews:**
- **Weekly:** Review Dependabot alerts, security scan results
- **Monthly:** DAST scans, vulnerability management
- **Quarterly:** Full threat model review, penetration testing
- **Annually:** Comprehensive security audit

---

### For Operations/DevOps

**Infrastructure Changes:**
1. Review [SECURITY_BASELINE.md](SECURITY_BASELINE.md) - Section 1 (Infrastructure)
2. Run Checkov scan:
   ```bash
   cd infra && checkov -d . --framework bicep --config-file .checkov.yaml
   ```
3. Complete [SECURITY_REVIEW_CHECKLIST.md](SECURITY_REVIEW_CHECKLIST.md) - Section 2

**Incident Response:**
1. Consult [STRIDE_THREAT_MODEL.md](STRIDE_THREAT_MODEL.md) for attack scenarios
2. Review [SECURITY_BASELINE.md](SECURITY_BASELINE.md) - Section 9 (Incident Response)
3. Check logs and monitoring (Application Insights, Log Analytics)

---

## Security Scanning Tools

### Infrastructure Security (Bicep)
```bash
# Run Checkov on Bicep templates
cd infra
checkov -d . --framework bicep --config-file .checkov.yaml
```

**Configuration:** `infra/.checkov.yaml`  
**CI/CD:** `.github/workflows/03-bicep-security.yml`

### Application Security (Python SAST)
```bash
# Run Bandit security scanner
cd src
uv run bandit -x .venv -s B101 -r . -f xml -o bandit_test.xml
```

**CI/CD:** `.github/workflows/01-ci.yml`

### Code Quality (CodeQL)
```bash
# Runs automatically via GitHub Actions
# View results: GitHub Security tab
```

**CI/CD:** `.github/workflows/codeql.yml`  
**Frequency:** Weekly + on PRs

### Dependency Security
```bash
# Check for outdated packages
cd src
uv pip list --outdated

# Check for security vulnerabilities (manual)
uv pip check
```

**Automation:** GitHub Dependabot (`.github/dependabot.yml`)

### Dynamic Testing (DAST)
```bash
# Using OWASP ZAP (example)
docker run -v $(pwd):/zap/wrk:rw \
  -t ghcr.io/zaproxy/zaproxy:stable \
  zap-baseline.py -t https://staging-url.azurewebsites.net \
  -r zap-report.html
```

**Guide:** [DAST_GUIDE.md](DAST_GUIDE.md)

---

## Security Architecture Principles

### 1. Defense in Depth
Multiple layers of security controls:
- Network isolation (Private endpoints, VNet)
- Identity controls (Managed identities, RBAC)
- Application security (Input validation, authentication)
- Data protection (Encryption at rest and in transit)

### 2. Least Privilege
- Scoped RBAC roles (no Owner/Contributor)
- System-assigned managed identities
- Just-in-time access for administrators
- Minimal permissions for service principals

### 3. Zero Trust
- No local authentication (disableLocalAuth: true)
- All access authenticated and authorized
- Network segmentation with private endpoints
- Continuous monitoring and validation

### 4. Secure by Default
- HTTPS enforced (TLS 1.2+)
- Public access disabled
- Default deny network policies
- Encryption enabled by default

### 5. Security Automation
- Automated security scanning (SAST, dependency checks)
- Infrastructure as Code with validation
- CI/CD security gates
- Continuous monitoring and alerting

---

## Security Contacts

### Reporting Security Vulnerabilities
**Do not report security vulnerabilities through public GitHub issues.**

For security reporting information, see: [/SECURITY.md](../../SECURITY.md)

Microsoft Security Response Center: https://aka.ms/SECURITY.md

### Internal Contacts
- **Security Team:** [Configure for your organization]
- **On-Call Engineer:** [Configure for your organization]
- **Compliance Officer:** [Configure for your organization]

---

## Compliance & Standards

### Standards Alignment
- ✅ **Microsoft SFI** (Security Future Initiative)
- ✅ **OWASP ASVS** (Application Security Verification Standard) - Level 1
- ✅ **Azure Security Baseline**
- ✅ **STRIDE Threat Modeling**

### Responsible AI
- Azure OpenAI content safety features
- Data privacy guarantees
- Transparency and accountability measures
- [Learn more](https://www.microsoft.com/ai/responsible-ai)

### Data Privacy
- GDPR considerations documented
- Data retention policies defined
- User data deletion capabilities
- Privacy by design principles

---

## Document Maintenance

### Review Schedule
- **Monthly:** Update security scan configurations
- **Quarterly:** Review threat model and baseline
- **Semi-annually:** DAST guide updates
- **Annually:** Comprehensive documentation review

### Ownership
- **STRIDE Threat Model:** Security Team
- **Security Baseline:** Platform Engineering Team
- **DAST Guide:** Security Team
- **Security Review Checklist:** All teams (collaborative)

### Version History
All documents include:
- Last updated date
- Next review date
- Document owner
- Version/change history

---

## Additional Resources

### Microsoft Resources
- [Azure Security Documentation](https://learn.microsoft.com/en-us/azure/security/)
- [Microsoft SDL](https://www.microsoft.com/en-us/securityengineering/sdl)
- [STRIDE Threat Modeling](https://learn.microsoft.com/en-us/azure/security/develop/threat-modeling-tool-threats)
- [Azure OpenAI Security](https://learn.microsoft.com/en-us/azure/ai-services/openai/security)

### Security Communities
- [OWASP](https://owasp.org/)
- [Azure Security Community](https://techcommunity.microsoft.com/t5/azure-security/ct-p/AzureSecurity)
- [GitHub Security Lab](https://securitylab.github.com/)

### Training
- [Microsoft Learn - Security](https://learn.microsoft.com/en-us/training/browse/?products=azure&terms=security)
- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [PortSwigger Academy](https://portswigger.net/web-security)

---

## Contributing

To contribute to security documentation:

1. **Fork and Branch:** Create a feature branch
2. **Make Changes:** Update relevant documents
3. **Test:** Validate commands and procedures
4. **Review:** Use security review checklist
5. **Submit:** Create PR with clear description
6. **Approval:** Requires security team review

**All security-related changes require security team approval.**

---

**Last Updated:** October 2025  
**Next Review:** January 2026
