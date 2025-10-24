# Infrastructure & Development Configuration

> For a quick start, see the main [README.md](README.md). This document provides the in-depth architecture, guardrails, and operational practices.

## 1. High-Level Architecture

````mermaid
graph TD
  User[Browser / Chainlit UI] --> App[Azure Container App - Production]
  User --> Staging[Azure Container App - Staging]
  App --> OpenAI[(Azure OpenAI Deployments)]
  App --> Storage[(Azure Storage - Conversations Container)]
  App --> ACR[Azure Container Registry]
  Staging --> ACR
  App --- CAE[Container Apps Environment]
  Staging --- CAE
  CAE --- VNet[VNet Integration]
  Storage --- PE[Private Endpoint]
  subgraph GitHub CI/CD
    Workflow[GitHub Actions Workflow]
  end
  Workflow --> FederatedOIDC[(OIDC Federated Identity)] --> Azure[Azure AD]
  Azure --> App
  Azure --> ACR
````

## 2. Module Layout (Bicep)
| Module | Purpose | Key Outputs |
| ------ | ------- | ----------- |
| `vnet.bicep` | Virtual network & subnets (container apps + private). | Subnet IDs, VNet ID |
| `privateendpoint.bicep` | Generic private endpoint builder for data plane isolation. | Private endpoint resource ID |
| `acr.bicep` | Azure Container Registry for storing container images. | ACR name, login server |
| `containerapp.bicep` | Container Apps Environment and production/staging Container Apps. | App URLs, principal IDs |
| (root) `resources.bicep` | Orchestrates modules + Container Apps, Azure OpenAI, identity, outputs. | App URLs, model endpoints, storage URL |

## 3. Security Guardrails

> **Comprehensive Security Documentation:** See [docs/security/](docs/security/) for detailed security analysis, threat modeling, and testing guides.

| Layer | Guardrail | Rationale |
| ----- | --------- | --------- |
| Transport | HTTPS enforced for Container Apps & Storage; TLS1_2 minimum | Prevent downgrade / insecure channels |
| Identity | System-assigned managed identity only; scoped blob data contributor | Least privilege & secretless access |
| Network | Default deny on storage; private endpoint for production | Reduce data exfiltration vectors |
| Data | No public blob access; encrypted services (blob/file) | Confidentiality & integrity by default |
| Deployment | Separate staging Container App for testing | Safer rollouts & isolated testing |
| CI/CD | GitHub OIDC federation (no static secrets) | Eliminates credential leakage risk |
| Containers | Immutable container images with digest pinning | Reproducible, auditable deployments |

### Security Reviews & Documentation

**STRIDE Threat Model:** [docs/security/STRIDE_THREAT_MODEL.md](docs/security/STRIDE_THREAT_MODEL.md)
- Complete threat analysis across all six STRIDE categories
- Risk assessments and mitigations
- Implementation roadmap

**Security Baseline:** [docs/security/SECURITY_BASELINE.md](docs/security/SECURITY_BASELINE.md)
- Infrastructure security controls (Bicep, Checkov)
- Application security (SAST with Bandit, CodeQL)
- Dependency management (Dependabot)
- CI/CD security (OIDC, GitHub Actions)

**DAST Guide:** [docs/security/DAST_GUIDE.md](docs/security/DAST_GUIDE.md)
- Dynamic application security testing approach
- OWASP ZAP, Burp Suite, Nuclei configurations
- AI-specific testing (prompt injection)
- CI/CD integration strategies

**Security Review Checklist:** [docs/security/SECURITY_REVIEW_CHECKLIST.md](docs/security/SECURITY_REVIEW_CHECKLIST.md)
- PR review requirements
- Infrastructure change validation
- Deployment verification
- Compliance sign-off procedures

## 4. Conversation Persistence
- Container: `default/conversations`
- Stored artifacts: message history (role, content) + metadata/workshop title.
- Write path: Container App -> Managed Identity -> Blob Data Contributor -> Storage.
- Extensibility: add vector index or archival tier by introducing a new module (e.g. `search.bicep`).

## 5. Azure OpenAI Model Strategy
| Deployment | Role | Notes |
| ---------- | ---- | ----- |
| `gpt-4o` | Primary reasoning & facilitation | Higher quality, higher cost |
| `o4-mini` | Mid-tier reasoning / fallback | Balanced cost/perf |
| `gpt-4.1-nano` | Lightweight tasks (titles) | Exposed via `CONVERSATION_TITLE_MODEL_DEPLOYMENT` |
| `text-embedding-ada-002` | Embeddings / semantic similarity | Consider vector store later |

## 6. Environment Configuration Flow
````mermaid
sequenceDiagram
  participant Dev
  participant Script as preprovision.sh
  participant AZD as azd env
  participant Bicep as azd provision
  participant App as Chainlit App
  Dev->>Script: Run preprovision.sh (optional)
  Script->>AZD: Set CLIENT_IP_ADDRESS
  Dev->>AZD: azd provision
  AZD->>Bicep: Deploy modules (Container Apps, ACR, etc.)
  Bicep->>AZD: Emit outputs
  Dev->>scripts/map-env-vars: Map outputs -> .env
  App->>Storage: Persist conversations (Managed Identity)
  App->>OpenAI: Model invocations
````

## 7. Parameters & Their Intent
| Parameter | Location | Purpose | Defaults |
| --------- | -------- | ------- | -------- |
| `environment` | `main.bicep` | Toggle between prod/dev for network hardening | prod/dev |
| `clientIpAddress` | `resources.bicep` | Temporary dev IP allow rule for storage | empty (disabled) |
| `namePrefix` / `resourceToken` | root | Deterministic naming & collision avoidance | Provided by `azd` |
| `principalId` / `principalType` | root | Additional authorized principal for OpenAI/Storage access | Supplied by env |

## 8. Identity & Role Assignment Details
- Roles granted:
  - Storage: `Storage Blob Data Contributor` to Container App MI + specified principal.
  - OpenAI: `Cognitive Services OpenAI User` to Container App MI & user principal for model access.
  - ACR: `AcrPull` role to Container App MI for pulling images.
- No broad subscription-level roles assigned inline.
- Extend by adding minimal additional role resources referencing module outputs.

## 9. Networking Patterns
| Pattern | When to Use | Notes |
| ------- | ----------- | ----- |
| Public + IP Rule | Early dev / quick start | Set `CLIENT_IP_ADDRESS` via preprovision script |
| Private Endpoint Only | Secure baseline / prod | Enabled in production environment |
| Hybrid (PE + IP) | Transitional debugging | Remove IP before prod cutover |

## 10. Deployment Workflow (CI/CD)
1. Push / PR triggers GitHub Actions.
2. OIDC federated credential obtains temporary token.
3. `azd provision` ensures infra drift reconciled.
4. Docker image built from application code.
5. Image pushed to Azure Container Registry.
6. Container deployed to staging Container App.
7. Manual validation.
8. Promote to production Container App when ready.

## 11. Local Development Checklist
| Step | Command / Action |
| ---- | ---------------- |
| (Optional) Capture IP | `./scripts/preprovision.sh` |
| Provision infra | `azd provision` |
| Map outputs | `./scripts/map-env-vars.sh` |
| Install deps | `uv sync` (run inside `src/`) |
| Run app | `uv run -m chainlit run -dhw chainlit_app.py` |

## 12. Extensibility Guidelines
1. Introduce new service via module (e.g., `keyvault.bicep`).
2. Limit outputs to required identifiers / endpoints.
3. Add least-privilege role assignments.
4. Wire output consumption into mapping script if needed.
5. Document in this file under a new section.

## 13. Verification / Health
| Check | Tool | Success Criteria |
| ----- | ---- | ---------------- |
| Private endpoint state | Azure Portal / CLI | `Approved` |
| Storage firewall | Portal | Only expected IP (if any) + PE |
| Role assignments | `az role assignment list` | Only defined principals |
| OpenAI deployments | Portal / CLI | All `Succeeded` with capacity |
| Container App env vars | Portal / CLI | `AZURE_STORAGE_ACCOUNT_URL` present |
| Container image | ACR | Latest image pushed successfully |

## 14. Troubleshooting
| Symptom | Probable Cause | Mitigation |
| ------- | ------------- | ---------- |
| 403 writing blobs | Missing role assignment or wrong endpoint | Re-run provision; check identity & URL |
| Timeout to Storage | Private endpoint active but DNS unresolved | Ensure VNet integration & private DNS zone linkage |
| Model not found | Deployment name mismatch | Verify `deployments` array & redeploy |
| Container App not starting | Image pull failure or configuration error | Check ACR role assignment; verify image exists |
| Staging works, prod stale | Manual promotion not performed | Update production Container App with new revision |

## 15. Future Enhancements (Backlog Ideas)
- Key Vault integration for central secret management.
- Vector store + embedding ingestion pipeline.
- Automated traffic splitting for canary deployments.
- Cost dashboard (daily model + storage metrics).
- Policy as Code (Azure Policy/Bicep) for guardrail enforcement.
- Blue-green deployment with traffic management.

---

**Maintainers:** Update this document whenever infrastructure semantics, security posture, or operational workflows change. Keep the main `README` concise by linking here.
