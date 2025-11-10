# Use Case — Specialized Medical Check‑up (Contoso Specialist Clinic)

## Provider Overview
**Contoso Specialist Clinic** is a specialty outpatient provider focused on efficient, patient‑friendly check‑ups that balance clinical rigor with a modern, digital front door.

---

## Scenario Summary
A patient books a specialist check‑up. The journey spans appointment request/confirmation, on‑site intake, clinical consultation, documentation, and follow‑up tasks (prescriptions and admin). (Source: workshop slide.)

### Current Workflow (As‑Is)
1. Patient requests an appointment and waits for confirmation.
2. Patient arrives at the clinic.
3. Reception provides forms; patient fills them out.
4. Receptionist creates the patient in the system and enters the data.
5. Consultation with the doctor.
6. Documentation and treatment plan.
7. Follow‑up and next steps (prescriptions and administrative tasks).

---

## Key Challenges
- **Intake friction:** Repetitive paper forms; manual re‑entry into clinical systems.
- **Communication & comprehension:** Patients struggle with medical jargon and leave uncertain about next steps.
- **Documentation burden:** Clinicians spend significant time on notes and coding during/after visits.
- **Follow‑up coordination:** Reminders, prescription management, and admin steps are inconsistently orchestrated.
- **Transparency & billing clarity:** Patients report surprise bills and limited visibility into costs.
- **Privacy & compliance:** Handling sensitive health data demands strict adherence to GDPR (where applicable), Swiss **nFADP**, and **EPDG**/EPD practices. [1](https://commission.europa.eu/law/law-topic/data-protection/legal-framework-eu-data-protection_en)[2](https://www.kmu.admin.ch/kmu/en/home/facts-and-trends/digitization/data-protection/new-federal-act-on-data-protection-nfadp.html)[3](https://www.bag.admin.ch/de/elektronisches-patientendossier)

---

## Requirements

### Regulatory & Privacy
- **Data Privacy:** Comply with EU **GDPR** principles (lawfulness, transparency, data minimization, security, rights such as access/erasure) and Swiss **nFADP** (privacy by design/default; breach notification; profiling) as applicable. [1](https://commission.europa.eu/law/law-topic/data-protection/legal-framework-eu-data-protection_en)[2](https://www.kmu.admin.ch/kmu/en/home/facts-and-trends/digitization/data-protection/new-federal-act-on-data-protection-nfadp.html)
- **Swiss Healthcare Context:** Align with the **Electronic Patient Dossier (EPD/EPDG)** framework for secure access and interoperability across actors. [3](https://www.bag.admin.ch/de/elektronisches-patientendossier)

### Technical (Art of the Possible from workshop slide)
- **Virtual assistants & chatbots** to greet patients, provide forms, and guide intake (e.g., Azure Health Bot concept).
- **Automated data entry** from forms using document processing (e.g., AI Builder‑style forms processing).
- **Clinical documentation support** via speech‑to‑text/NLP to draft visit notes and plan.
- **Predictive analytics** to flag risks and suggest follow‑up actions.
- **Patient engagement** (personalized reminders, follow‑ups, satisfaction prompts).

### Integration & Access
- Integrate with scheduling, EHR/EMR, billing, patient communications, and (where adopted) the Swiss **EPD**. Ensure role‑based access control and strong audit logging. [3](https://www.bag.admin.ch/de/elektronisches-patientendossier)

---

## Personas

### Emily (Patient Persona)
- **Profile:** Busy professional, mid‑30s; values clarity, time savings, privacy.
- **Top needs:** Plain‑language explanations, a concise visit summary, transparent costs, and clear next steps.

### Receptionist (Front Desk)
- **Goals:** Fast, error‑free intake; minimal data re‑entry; smooth queue management. (Derived from workflow.)

### Specialist Doctor
- **Goals:** Spend time with the patient, not screens; accurate, complete documentation; clear follow‑ups. (Derived from workflow.)

---

## Example Processes (Detailed)

### 1) Check‑in & Intake
**As‑Is:** Paper forms → manual re‑entry by staff.
**To‑Be (capabilities):** Guided digital intake; automated extraction/validation; identity checks; handoff to EHR.

### 2) Consultation & Documentation
**As‑Is:** Clinician toggles between conversation and typing notes.
**To‑Be (capabilities):** Ambient transcription; structured note drafting; coding suggestions; clinician review/sign‑off.

### 3) Follow‑up & Next Steps
**As‑Is:** Manual reminders and ad‑hoc education materials.
**To‑Be (capabilities):** Personalized summaries, medication guidance, reminders, and surveys routed via preferred channel.

---

## Success Metrics
- **Intake time** (minutes from arrival to “ready for clinician”).
- **Data accuracy** (intake errors per 100 visits).
- **Documentation time** (minutes per note; after‑hours charting).
- **Time to follow‑up** (avg. hours to first reminder or result notification).
- **Patient‑reported clarity** (post‑visit survey: “I understood my next steps”).
- **Billing transparency** (rate of “surprise bill” complaints).

---

## Risks & Mitigations
- **Privacy & consent:** Implement privacy‑by‑design/default; clear consent flows; encryption and RBAC; audit trails. [2](https://www.kmu.admin.ch/kmu/en/home/facts-and-trends/digitization/data-protection/new-federal-act-on-data-protection-nfadp.html)
- **Data integration:** Use standards‑based exchange and align to EPD/EPDG goals for interoperability. [3](https://www.bag.admin.ch/de/elektronisches-patientendossier)
- **Bias & fairness:** Measure model performance on diverse cohorts; clinician‑in‑the‑loop verification.

---

## Out of Scope (Initial Phase)
- Complex disease‑specific pathways (e.g., oncology MDT orchestration).
- Cross‑border data exchange beyond the clinic’s current legal remit.

---

## References (Source Material)
- **GDPR (EU legal framework overview):** European Commission page. [1](https://commission.europa.eu/law/law-topic/data-protection/legal-framework-eu-data-protection_en)
- **Swiss data protection (nFADP) overview:** SECO SME portal summary. [2](https://www.kmu.admin.ch/kmu/en/home/facts-and-trends/digitization/data-protection/new-federal-act-on-data-protection-nfadp.html)
- **Swiss EPD/EPDG (official overview):** Federal Office of Public Health (BAG). [3](https://www.bag.admin.ch/de/elektronisches-patientendossier)
