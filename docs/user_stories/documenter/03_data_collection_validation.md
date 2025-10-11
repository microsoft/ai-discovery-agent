# User Story 03 – Structured Data Collection & Validation

## Story

As a facilitator, I want the system to structure, store, and validate all captured workshop inputs so that final documentation is complete and consistent.

## Description

Each phase maps to a structured schema (fields, optional vs. required, multiplicity). Inputs are normalized and stored (e.g., Markdown to structured blocks). Validation occurs on-demand (e.g., attempting to progress) and pre-generation. Missing fields produce actionable guidance.

## Acceptance Criteria

1. Schema Mapping
   - Given a phase definition, when I supply inputs, then they are stored under canonical field keys (e.g., `business.overview`, `ideation.activities[]`).
2. Required Field Enforcement
   - Given a required field is empty, when I try to finalize documentation, then generation is blocked and a list of missing fields with friendly labels is shown.
3. Partial Save Allowed
   - Given incomplete data, when I save or the system autosaves, then no blocking error occurs (only generation is restricted).
4. Field-Level Validation
   - Given I supply an overlong entry (exceeding configured character limits if any), when stored, then I receive a warning and truncation does not occur silently.
5. Table & List Preservation
   - Given I enter a Markdown table or list, when stored, then re-rendering in summaries preserves structure.
6. Image Reference Linking
   - Given I upload an image and reference it ("see diagram 1"), when the summary renders, then the image is linked or previewed (if supported by platform).
7. Validation Summary Command
   - Given I request "validation status", when executed, then a checklist of phases with Missing / Complete status appears.
8. Metadata Integrity
   - Given I edit a previously entered field, when I view the structured export (developer mode or debug), then only that field’s version increments (no unintended changes to siblings).
9. Pre-Generation Gate
   - Given I request document generation, when validation runs, then either success proceeds or an ordered list of blockers is presented.

## Non-Functional Notes

- Validation completes < 500ms for typical workshop size.
- Schema definitions versioned to enable migrations.

## Edge Cases

- Large pasted content (>50k chars) → streaming chunk handling with feedback.
- Conflicting duplicate entries (e.g., same activity name) → deterministic disambiguation suffix or prompt.
