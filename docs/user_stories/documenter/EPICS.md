# Documenter Epics & Story Mapping

This document groups the 12 user stories into higher-level epics for planning, sequencing, and release management. Each epic lists included stories, business rationale, key dependencies, success metrics, and recommended milestone placement. Story IDs reference filenames (`01_...` etc.).

---

## Epic 1: Conversational Guidance & Phase Orchestration

**Stories:** 01 Chat-Based Guidance, 02 Workflow Phase Navigation & Reordering  
**Rationale:** Establishes the primary user interaction model and structural backbone of the workshop experience. Without this, downstream data capture and generation lack usable context flow.  
**Key Capabilities:** Phase presentation, navigation commands, contextual prompts, summaries, non-linear traversal.  
**Dependencies:** None (foundational).  
**Enables:** Data structuring (Epic 2), export readiness (Epic 3).  
**Success Metrics:**

- 90% of facilitator navigation actions succeed without fallback help.
- <2s median first-token latency for guidance prompts.  
  **Milestone:** MVP (Release 0.1).

---

## Epic 2: Structured Data, Media Capture & Validation

**Stories:** 03 Data Collection & Validation, 04 Audio Input & Transcription, 05 Document & Diagram Upload  
**Rationale:** Ensures comprehensive, multimodal capture of workshop knowledge with schema-backed integrity—critical for high-quality documentation.  
**Key Capabilities:** Schema mapping, validation gating, audio transcription lifecycle, file ingestion & metadata, rich text preservation.  
**Dependencies:** Epic 1 (contextual phase targeting).  
**Enables:** Accurate export (Epic 3), compliance enforcement (Epic 5).  
**Success Metrics:**

- <5% validation rework after first pass in feasibility workshops.
- ≥95% successful transcription availability within SLA (<5s for <60s clip).  
  **Milestone:** MVP (Release 0.1) for core schema + upload; transcription may be phased (Release 0.2) if needed.

---

## Epic 3: Documentation Generation & Export Pipeline

**Stories:** 06 Documentation Generation  
**Rationale:** Converts structured data into facilitator deliverables, the main value output of the workshop process.  
**Key Capabilities:** Markdown export (MVP), section ordering, regeneration versioning, attachment and transcript inclusion, future Word/PPT templating.  
**Dependencies:** Epics 1 & 2 (complete data & navigation state).  
**Enables:** Stakeholder sharing, archival, and review cycles (ties to compliance sign-off).  
**Success Metrics:**

- 100% mandatory sections populated or flagged before export.
- <10s p95 generation time for median dataset.  
  **Milestone:** MVP (Markdown in Release 0.1); Word/PPT in Release 0.3.

---

## Epic 4: Session Lifecycle, Resilience & Multilingual Experience

**Stories:** 07 Session Management, 08 Multilanguage Support  
**Rationale:** Facilitators need continuity across interruptions and language-appropriate guidance for global applicability.  
**Key Capabilities:** Autosave, resume, snapshots/rollback (optional), language detection & override, Unicode-preserving storage.  
**Dependencies:** Epics 1 & 2 (phases & structured content).  
**Enables:** Cross-region adoption, iterative session refinement.  
**Success Metrics:**

- <1% data loss incidents (autosave reliability).
- ≥90% correct initial language detection accuracy.  
  **Milestone:** Core session persistence in Release 0.1; snapshots & advanced language tooling in Release 0.2.

---

## Epic 5: Trust, Security, Privacy & Governance Controls

**Stories:** 09 Security & Privacy Governance, 12 Compliance Automation (SFI & RAI)  
**Rationale:** Protects sensitive client information and enforces mandatory organizational standards—prerequisite for production rollout.  
**Key Capabilities:** Access isolation, encryption assurances, deletion workflows, audit logging, automated infra/code scans, RAI guardrail tests, compliance artifact generation.  
**Dependencies:** Foundational data model (Epic 2) and session isolation (Epic 4).  
**Enables:** Production deployment sign-off, risk mitigation, external trust.  
**Success Metrics:**

- 0 unresolved critical vulnerabilities at release gates.
- 100% features with attached compliance artifact.  
  **Milestone:** Baseline security gating in Release 0.1; full automated RAI guardrail matrix in Release 0.2–0.3.

---

## Epic 6: Experience Quality (Performance, Usability & Accessibility)

**Stories:** 10 Performance & Responsiveness, 11 Usability & Accessibility  
**Rationale:** Ensures the tool is efficient, inclusive, and ergonomic—improving adoption and facilitator satisfaction.  
**Key Capabilities:** Latency instrumentation, streaming fallback, progress indicators, WCAG 2.1 AA compliance, focus management, keyboard coverage, alt text support.  
**Dependencies:** Rendering + interaction flows from Epic 1; content assets from Epics 2 & 4.  
**Enables:** Stable scale-up, compliance with accessibility standards.  
**Success Metrics:**

- p95 prompt first-token latency ≤2s under normal load.
- 0 critical accessibility blocker issues in audit.  
  **Milestone:** Incremental; baseline performance + basic accessibility in Release 0.1, full WCAG AA polish in Release 0.2.

---

## Cross-Epic Dependency Summary

| Dependent Epic       | Depends On | Notes                                                            |
| -------------------- | ---------- | ---------------------------------------------------------------- |
| 2 Structured Data    | 1 Guidance | Phase context tagging                                            |
| 3 Export Pipeline    | 1,2        | Needs validated structured content                               |
| 4 Session & Language | 1,2        | Stores + rehydrates state, localized prompts                     |
| 5 Trust & Compliance | 2,4        | Requires stable data stores + session isolation                  |
| 6 Experience Quality | 1,2,4      | Performance metrics & accessible flows rely on core interactions |

---

## Suggested Release Phasing (Illustrative)

- Release 0.1 (MVP): Epics 1, core of 2 (schema + uploads), 3 (Markdown only), 4 (basic persistence), 5 (baseline security), 6 (baseline perf + basic accessibility)
- Release 0.2: Remaining Audio (Epic 2), enhanced multilingual (Epic 4), advanced compliance automation & RAI guardrails (Epic 5), full accessibility & metrics dashboards (Epic 6)
- Release 0.3: Word/PPT export (Epic 3), snapshots/rollback (Epic 4), extended guardrail simulation & risk scoring (Epic 5)

---

## Risk & Mitigation Highlights

| Risk                                     | Impact                          | Mitigation                                                        |
| ---------------------------------------- | ------------------------------- | ----------------------------------------------------------------- |
| Late schema changes (Epic 2)             | Rework export mappings (Epic 3) | Versioned schema + migration layer                                |
| Transcription latency                    | User abandonment of audio       | Parallel chunk streaming + partial interim transcript             |
| Overly strict validation                 | Blocked progress & frustration  | Progressive validation + informational warnings before hard gate  |
| Compliance automation false positives    | Deployment delays               | Override mechanism w/ expiry & justification (Story 12)           |
| Multi-language hallucinated translations | Loss of fidelity                | Default no-auto-translate; explicit per-item translation requests |

---

## Backlog Candidates (Out of Scope Epics / Future)

- Multi-user real-time collaboration
- External system integrations (CRM, Teams)
- Analytics dashboards & KPI trend visualization
- AI-assisted summarization of very large ideation or transcript corpora

---

## Traceability Matrix

| Story | Epic | Primary Outcome                          |
| ----- | ---- | ---------------------------------------- |
| 01    | 1    | Conversational phased guidance           |
| 02    | 1    | Non-linear navigation & phase status     |
| 03    | 2    | Structured validation & schema integrity |
| 04    | 2    | Audio capture & transcription workflow   |
| 05    | 2    | File/diagram ingestion & referencing     |
| 06    | 3    | Export generation & versioning           |
| 07    | 4    | Persistence & session lifecycle          |
| 08    | 4    | Language detection & override            |
| 09    | 5    | Security, privacy controls               |
| 10    | 6    | Performance & responsiveness             |
| 11    | 6    | Accessibility & usability                |
| 12    | 5    | Automated compliance & guardrails        |

---

## Acceptance Metrics Dashboard (Initial Targets)

| Metric                             | Target               | Source                    |
| ---------------------------------- | -------------------- | ------------------------- |
| Prompt first-token latency p95     | ≤ 2s                 | Telemetry logs            |
| Export generation p95              | ≤ 10s                | Export service metrics    |
| Autosave failure rate              | < 0.5%               | Persistence retries log   |
| Accessibility critical issues      | 0                    | Automated + manual audits |
| Security critical vulns at release | 0                    | CI security scan          |
| RAI guardrail escape rate          | < Threshold (define) | Guardrail test harness    |

---

## Governance & RACI (Abbreviated)

| Activity                         | Responsible   | Accountable   | Consulted          | Informed     |
| -------------------------------- | ------------- | ------------- | ------------------ | ------------ |
| Schema evolution (Epic 2)        | Backend Eng   | Tech Lead     | Facilitators       | PM           |
| Export template updates (Epic 3) | Docs Engineer | PM            | Design, Compliance | Stakeholders |
| Compliance pipeline (Epic 5)     | DevOps        | Security Lead | Legal, RAI Council | PM           |
| Accessibility audit (Epic 6)     | UX / QA       | Design Lead   | Eng                | PM           |

---

## Implementation Sequencing Notes

1. Build navigation + phase registry (Epics 1) → define schema contracts (Epic 2) before UI polish.
2. Implement minimal validation hooks early to prevent rework of input handlers.
3. Stand up export service with placeholder sections; progressively enrich mapping.
4. Integrate telemetry from day one to capture baseline performance metrics for optimization.
5. Parallelize security/compliance pipeline scaffolding while core features emerge.

---

## Change Management

- Epics doc versioned; updates require referencing change ticket.
- Stories remain the atomic unit for acceptance. Epics provide planning abstraction only.

---

_Version: 1.0 (initial mapping). Maintain updates in this file with changelog below._

### Changelog

| Date       | Version | Changes                           |
| ---------- | ------- | --------------------------------- |
| 2025-10-02 | 1.0     | Initial epic grouping and mapping |
