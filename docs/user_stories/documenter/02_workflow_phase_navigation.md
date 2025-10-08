# User Story 02 – Workflow Phase Navigation & Reordering

## Story

As a facilitator, I want to skip, revisit, or reorder workshop phases so that I can adapt the flow to participant needs without losing structure.

## Description

The system maintains an ordered canonical list of phases but allows non-linear navigation. Navigation requests ("go to ideation", "skip this", "back to workflow mapping") are interpreted robustly. Progress indicators reflect completion state (Not Started / In Progress / Complete / Blocked).

## Acceptance Criteria

1. View Phase List
   - Given I request "phases" or open the phase panel, when displayed, then all defined phases appear with status indicators.
2. Direct Navigation
   - Given I am in any phase, when I enter a command like "go to feasibility" (case-insensitive), then the assistant switches context and announces the target phase header.
3. Skip Phase
   - Given a phase is skippable, when I enter "skip" or "skip this phase", then its status becomes Skipped and the next phase is introduced.
4. Prevent Skip If Blocking
   - Given a phase is marked non-skippable (e.g., Business & Challenge), when I attempt to skip, then I receive a refusal with rationale and required items listed.
5. Back Navigation
   - Given I enter "back" while not in the first phase, then the assistant moves to the previously visited phase and displays its latest saved content summary.
6. Reordering (Deferred Execution)
   - Given I request a reordering ("move impact assessment before feasibility"), when processed, then I receive confirmation and the re-indexed list (only if reordering is permitted by governance rules—else a rationale is shown).
7. Status Updates
   - Given I complete required inputs for a phase, when validation passes, then the phase status updates to Complete automatically.
8. Progress Percent
   - Given at least one phase is Complete, when progress is displayed, then a percentage is shown based on required phases completed / total required phases.
9. Session Restore
   - Given I resume a saved session, when phases are shown, then statuses reflect last persisted state accurately.

## Non-Functional Notes

- Navigation commands parsed with fuzzy intent resolution (edit distance ≤2 for phase names).
- All changes persisted within 1s (see autosave story).

## Edge Cases

- Attempt to jump to unknown phase name → graceful suggestion list.
- Reordering conflicting with dependency chain → explanatory error.
