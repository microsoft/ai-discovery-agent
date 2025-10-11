# User Story 01 – Chat-Based Guidance

## Story

As a facilitator, I want the assistant to guide me conversationally through each workshop phase with helpful prompts and examples so that I can efficiently capture all required information with flexibility.

## Description

The system presents structured phases (Business & Challenge, Focus Area, Ideation, etc.) as a dialogue. It provides contextual prompts, examples, summaries, and reminders about gaps. It supports rich text (lists, tables) and produces an in-session draft summary the facilitator can refine.

## Acceptance Criteria

1. Phase Presentation
   - Given I start a new workshop, when the session begins, then I see Phase 1 introduced with a concise objective and prompt.
   - Given I'm at any phase, when I request "next", then the next defined phase is introduced unless blocked by unmet required fields (see validation story).
2. Contextual Prompts & Examples
   - Given a phase requires specific structured inputs, when the assistant prompts me, then it includes at least one example or formatting suggestion.
3. Rich Text Input
   - Given I enter Markdown with lists or tables, when I send it, then formatting is preserved in the stored structured representation and summary rendering.
4. Draft Summary On Demand
   - Given I have entered content in a phase, when I request a summary (e.g., "summary"), then a compiled current draft of that phase appears within 2 seconds for simple content or a progress indicator within 2 seconds for longer compilation.
5. Gap Reminders
   - Given a required field in the current phase is missing, when I attempt to move forward, then the assistant lists missing items with human-friendly labels.
6. Flexible Acknowledgements
   - Given I provide adequate content, when the assistant evaluates it, then it confirms acceptance or suggests specific improvements (not generic feedback).
7. Re-ask Capability
   - Given I request clarification ("help", "examples"), when the assistant responds, then it provides tailored examples for the current phase context.
8. Session Continuity
   - Given I refresh the UI mid-phase, when the session restores, then the assistant re-renders the last active phase header and pending guidance.

## Non-Functional Notes

- Average prompt response < 2s (simple) with streaming enabled for longer reasoning.
- All assistant messages follow accessibility guidelines (semantic headings, list markers).

## Open Questions

- Should facilitator be able to toggle minimal vs. verbose prompting mode?
- Should phases be collapsible in a side navigation panel (future enhancement)?
