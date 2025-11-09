# Use Case — Damage Report at a Car Manufacturer Call Center

## Provider Overview
**Automaker Customer Helpdesk** handles inbound calls for vehicle damage incidents, guiding customers through triage, evidence capture, coverage checks, and claim initiation with the insurer and repair network.

---

## Objectives
- **Customer satisfaction:** Reduce effort, provide clarity and speed
- **Business efficiency:** Standardize intake, minimize rework, accelerate time‑to‑decision
- **Cost reduction:** Lower average handle time (AHT), reduce repeat contacts, prevent leakage/fraud

---

## Example Workflow (As‑Is → baseline from description)
1. **Answer the call**
2. **Identify the contact person** (verify identity & relationship to policy/vehicle)
3. **Record the customer’s inquiry** (free‑text summary)
4. **Check customer information/data** (account, policy, warranty/assistance eligibility)
5. **Identify the car type** (VIN, model, year, trim)
6. **Capture incident details** (what happened, when/where, drivable?)
7. **Get photographic evidence** (request images/video)
8. **Check damage** (initial triage; safety concerns)
9. **Organize insurance claim** (open/route; provide claim number and next steps)

---

## Key Challenges (Current State)
- **Repetition & handoffs** → customers re‑share details; agents chase missing info
- **Unstructured data** (free‑text calls, inconsistent photo capture) → slow assessment
- **Evidence friction** (no guided photos; failed uploads; no secure link)
- **Eligibility & coverage ambiguity** (policy vs. manufacturer programs)
- **Limited visibility** into claim status after handoff → repeat calls

---

## Requirements (To‑Be)
### Functional
- **Guided intake** with mandatory fields (who/what/when/where), VIN capture, and geolocation (optional/consented)
- **Photo capture workflow** (SMS/web link) with **capture hints** (angles, damage close‑ups, license plate, context)
- **Eligibility checks** (policy status, deductibles, assistance coverage)
- **Claim creation** with case ID; secure data and image storage; repair referral
- **Status notifications** (SMS/email) and self‑service tracking

### Non‑Functional
- **Security & privacy by design**; audit trail; least‑privilege access
- **Scalability** for peak events (e.g., storms/hail)
- **Resilience** (retry & offline handling for photo uploads)
- **Observability** (AHT, first‑contact resolution, photo success rate)

---

## To‑Be Journey (Solution Blueprint)
**1) Smart Triage & Identity**
- Caller ID + case search; confirm identity & consent; capture preferred channel for follow‑ups

**2) Structured Incident Intake**
- Form with required fields; dynamic questions based on incident type (collision, vandalism, weather, glass, tire)
- Real‑time validation (date/time, location format, VIN checksum)

**3) Evidence Capture (Mobile‑first)**
- Send **secure SMS link** to a web capture page (no app install)
- Guided photo checklist (front/left/right/rear, close‑ups, VIN plate, odometer; optional short video)
- Instant **upload confirmation** and case ID display

**4) Automated Assessment & Safety Gate**
- Basic rules: drivable? fluids leaking? airbags deployed? If unsafe → roadside assistance escalation
- Optional **computer vision pre‑screen** to detect panel/bumper/glass damage and flag severity bucket
- Fraud heuristics (duplicate images, metadata anomalies)

**5) Coverage & Claim Orchestration**
- Verify policy/assistance eligibility, deductibles, and preferred insurer
- Create claim; share **claim number**; book inspection/repair (in‑network shop or mobile repair)
- Payment options & courtesy vehicle guidance

**6) Customer Recap & Tracking**
- Send **visit recap** (incident summary, claim ID, next steps, contact details)
- Self‑service portal link to track status and upload additional documents

---

## Roles & Responsibilities
- **Customer (Jordan):** Provides incident details and images; chooses repair options
- **Call Center Agent:** Verifies identity; guides intake; ensures evidence completeness; opens claim; sets expectations
- **Claims Adjuster/Insurer:** Validates coverage; estimates cost; authorizes repair
- **Repair Network Coordinator:** Schedules inspection/repair; manages courtesy vehicle

---

## Data Model (High Level)
- **Customer:** name, contact, consent flags
- **Vehicle:** VIN, model, year, trim, warranty/assistance
- **Policy:** insurer, policy ID, coverage type, deductible, status
- **Incident:** timestamp, location, description, weather, drivable flag
- **Evidence:** images/video (URI, hashes, capture checklist status)
- **Claim:** claim ID, status, assigned adjuster, SLAs, repair shop

---

## Sample Agent Script (Condensed)
1. **Greeting & Safety:**
   “Thanks for calling [Brand] Helpdesk. Is everyone safe? Is the vehicle drivable?”
2. **Verify & Consent:**
   “Can I verify your name and relationship to the vehicle? May I send you a secure link to upload photos?”
3. **Intake Essentials:**
   “When and where did this happen? Please describe what occurred.”
4. **VIN & Photos:**
   “Please capture front, both sides, rear, and a close‑up of the damage. Then VIN plate and license plate.”
5. **Set Expectations:**
   “Your case number is **[CASE‑####]**. You’ll receive a summary with next steps, repair options, and claim details.”

---

## Metrics & Targets
- **AHT:** ↓ 20–30% via structured intake and guided evidence capture
- **First‑contact resolution:** ↑ (claim opened with complete evidence)
- **Photo capture success rate:** >95% within 15 minutes of link sent
- **Repeat contact rate:** ↓ 25% (clear recaps + self‑service tracking)
- **CSAT/NPS:** measurable uplift vs. baseline

---

## Risks & Mitigations
- **Incomplete evidence:** enforce capture checklist; allow later upload; proactive reminders
- **Privacy concerns:** clear consent and data‑use notice; secure links; access controls
- **AI misclassification:** human‑in‑the‑loop for assessment; explainable outputs; ongoing QA
- **Peak event overload:** autoscaling capture service; priority queues for non‑drivable vehicles

---

## Edge Cases
- Third‑party driver reporting; fleet vehicles; leased vehicles
- Police report numbers; injuries (handoff to emergency services as needed)
- Stolen vehicle vs. damage (route to theft workflow)
- Multi‑incident scenarios (hail + vandalism) and disputed liability

---

## Implementation Hints (platform‑agnostic)
- **Channels:** Phone + SMS/Web capture page; email recap
- **Integrations:** CRM/Case mgmt, policy systems, repair network, payments
- **Automation:** Event‑driven updates, SLA timers, customer notifications
