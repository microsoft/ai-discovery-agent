
# Use Case — Streamlined Talent Acquisition

**Problem statement:** The HR team needs a more efficient and attractive recruitment process to attract and retain top talent.

---

## As-Is (Current Process)
1. Reqs opened; job description circulated via email/Docs
2. Sourcing via mixed channels; limited employer brand reach
3. Manual resume triage; variable screening criteria
4. Scheduling ping-pong across calendars; frequent reschedules
5. Interviews happen; notes scattered; slow decision cycles
6. Offer prep via email back-and-forth; candidate communication delays
7. Onboarding handoff not standardized → slow ramp

> Observed challenges: lengthy process, candidate drop-off, and brand not well-known in target pools.

## To-Be Journey (Solution Blueprint)
**1) Employer Brand & Sourcing**
- Consistent recruitment campaigns across channels
- Curated career content hub; role pages with authentic team stories
- Targeted campaigns; track click-throughs and conversions

**2) Intake & Requisition Quality**
- Standardized Job Description templates with hiring-manager prompts
- Automated approval flows with SLA timers

**3) Application & Screening**
- Resume parsing and structured profiles
- Summaries per candidate (skills match, risk flags, open questions)
- Auto-triage rules to tag/route candidates

**4) Scheduling & Coordination**
- Self-scheduling and time-zone handling
- Automated reminders and reschedule links

**5) Interviews**
- Structured interview guides
- Automated interview summaries mapped to competencies
- Feedback captured and written back to system

**6) Evaluation & Decision**
- Shortlist views (side-by-side candidate comparisons, scorecards)
- Pipeline dashboard: SLA breaches, stage conversion, DEI lens

**7) Offer & Onboarding Handoff**
- Offer letter templates and approval workflow
- Handoff package to onboarding with tasks pre-created

---

## Controls & Compliance
- Guardrails for responsible AI (transparency in AI-assisted summaries; human-in-the-loop decisions)
- Data retention labels on resumes/interview notes
- Role-based access and environment strategy for Dev/Test/Prod

## KPI Tree (Measurement Plan)
- Efficiency: time-to-fill, time-to-slate, scheduling lead time
- Experience: candidate drop-off, candidate NPS, hiring manager CSAT
- Quality: pass-through rates per stage, on-the-job 90-day success proxy, offer acceptance
- Ops: recruiter throughput (#reqs, time saved), SLA adherence

## Phased Rollout
- Week 0–2: Discovery & data mapping; pilot roles picked; baseline KPIs captured
- Week 3–6: Build “Hiring Hub” app, screening automations, and scheduling; limited pilot
- Week 7–10: Expand interview kits, recap, and feedback loops; dashboards live
- Week 11–12: Harden integrations, publish playbooks; go-live across functions

## Risks & Mitigations
- Change fatigue: run enablement clinics; job-aids; “champion” network
- AI bias: standardize question banks & rubric; monitor score distributions; periodic audits
- Integration drift: define RACI; versioned APIs; automated tests on key flows
