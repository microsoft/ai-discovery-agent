# Infrastructure & Development Configuration

> For a quick start, see the main [README.md](README.md). This document provides the in-depth architecture, guardrails, and operational practices.

## 1. High-Level Architecture

````mermaid
graph TD
  User[Browser / Chainlit UI] --> App[Azure App Service - Prod Slot]
  User --> Staging[Azure App Service - Staging Slot]
  App --> OpenAI[(Azure OpenAI Deployments)]
  App --> Storage[(Azure Storage - Conversations Container)]
  App --- VNet[VNet Integration]
  Storage --- PE[Private Endpoint]
  subgraph GitHub CI/CD
    Workflow[GitHub Actions Workflow]
  end
  Workflow --> FederatedOIDC[(OIDC Federated Identity)] --> Azure[Azure AD]
  Azure --> App
````

## 2. Module Layout (Bicep)
| Module | Purpose | Key Outputs |
| ------ | ------- | ----------- |
| `vnet.bicep` | Virtual network & subnets (app + private). | Subnet IDs, VNet ID |
| `privateendpoint.bicep` | Generic private endpoint builder for data plane isolation. | Private endpoint resource ID |
| `storage.bicep` | Storage account, conversations container, network ACL/IP rules, role assignments, optional private endpoint. | Blob endpoint URL, storage name |
| (root) `resources.bicep` | Orchestrates modules + App Service (prod/staging), Azure OpenAI, identity, outputs. | App URIs, model endpoints, storage URL |

## 3. Security Guardrails
| Layer | Guardrail | Rationale |
| ----- | --------- | --------- |
| Transport | HTTPS enforced for App & Storage; TLS1_2 minimum | Prevent downgrade / insecure channels |
| Identity | System-assigned managed identity only; scoped blob data contributor | Least privilege & secretless access |
| Network | Default deny on storage; optional IP allow rule + private endpoint | Reduce data exfiltration vectors |
| Data | No public blob access; encrypted services (blob/file) | Confidentiality & integrity by default |
| Deployment | Staging slot then manual swap | Safer rollouts & rollback path |
| CI/CD | GitHub OIDC federation (no static secrets) | Eliminates credential leakage risk |

## 4. Conversation Persistence
- Container: `default/conversations`
- Stored artifacts: message history (role, content) + metadata/workshop title.
- Write path: App Service -> Managed Identity -> Blob Data Contributor -> Storage.
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
  AZD->>Bicep: Deploy modules
  Bicep->>AZD: Emit outputs
  Dev->>scripts/map-env-vars: Map outputs -> .env
  App->>Storage: Persist conversations (Managed Identity)
  App->>OpenAI: Model invocations
````

## 7. Parameters & Their Intent
| Parameter | Location | Purpose | Defaults |
| --------- | -------- | ------- | -------- |
| `private` | `resources.bicep` | Toggle network hardening + private endpoints | (set via `azd config set AZURE_PRIVATE`) |
| `clientIpAddress` | `resources.bicep` → `storage` | Temporary dev IP allow rule | empty (disabled) |
| `namePrefix` / `resourceToken` | root | Deterministic naming & collision avoidance | Provided by `azd` |
| `storageSku` | storage module | Replication & durability choice | `Standard_LRS` |
| `principalId` / `principalType` | root & storage | Additional authorized principal besides Web App | Supplied by env |

## 8. Identity & Role Assignment Details
- Roles granted:
  - Storage: `Storage Blob Data Contributor` to App Service MI + specified principal.
  - OpenAI: proper role (from template) to App & user principal for model access.
- No broad subscription-level roles assigned inline.
- Extend by adding minimal additional role resources referencing module outputs.

## 9. Networking Patterns
| Pattern | When to Use | Notes |
| ------- | ----------- | ----- |
| Public + IP Rule | Early dev / quick start | Set `CLIENT_IP_ADDRESS` via preprovision script |
| Private Endpoint Only | Secure baseline / prod | Ensure DNS integration (App Service VNet) |
| Hybrid (PE + IP) | Transitional debugging | Remove IP before prod cutover |

## 10. Deployment Workflow (CI/CD)
1. Push / PR triggers GitHub Actions.
2. OIDC federated credential obtains temporary token.
3. `azd provision` ensures infra drift reconciled.
4. Code deployed to staging slot.
5. Manual validation.
6. Optional slot swap for zero-downtime release.

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
| App env vars | Portal Config | `AZURE_STORAGE_ACCOUNT_URL` present |

## 14. Troubleshooting
| Symptom | Probable Cause | Mitigation |
| ------- | ------------- | ---------- |
| 403 writing blobs | Missing role assignment or wrong endpoint | Re-run provision; check identity & URL |
| Timeout to Storage | Private endpoint active but DNS unresolved | Ensure VNet integration & private DNS zone linkage |
| Model not found | Deployment name mismatch | Verify `deployments` array & redeploy |
| Staging works, prod stale | Slot swap not performed | Perform manual swap in portal |

## 15. Future Enhancements (Backlog Ideas)
- Key Vault integration for central secret management.
- Vector store + embedding ingestion pipeline.
- Automated slot swap after health probes.
- Cost dashboard (daily model + storage metrics).
- Policy as Code (Azure Policy/Bicep) for guardrail enforcement.

---

**Maintainers:** Update this document whenever infrastructure semantics, security posture, or operational workflows change. Keep the main `README` concise by linking here.
