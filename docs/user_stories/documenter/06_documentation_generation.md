# User Story 06 – Documentation Generation

## Story

As a facilitator, I want to generate comprehensive workshop documentation (initially in Markdown, later in Word/PowerPoint) so that I can deliver standardized outputs efficiently.

## Description

Generates structured outputs mapping collected data to required sections. Initial MVP: Markdown bundle (single file or segmented). Future: .docx using official report template; .pptx using master deck template. Supports download, regeneration, and version tagging.

## Acceptance Criteria

1. Pre-Generation Validation
   - Given required fields are incomplete, when I request generation, then the process is blocked with a list of unmet items.
2. Markdown Output (MVP)
   - Given validation passes, when generation completes, then I can download a Markdown file containing all workshop sections in defined order.
3. Section Ordering
   - Given output is generated, when I inspect it, then sections appear in the canonical order listed in the specification (Business & Challenge → Impact Assessment).
4. Attachments Inclusion
   - Given uploads are selected for inclusion, when output is generated, then image references are embedded and documents listed in an appendix.
5. Transcript Inclusion
   - Given audio transcripts are approved, when output generates, then transcripts appear in a dedicated section or appendix.
6. Regeneration
   - Given I modify content, when I click regenerate, then a new version is produced without deleting prior versions (up to retention limit).
7. Export Metadata
   - Given generation completes, when I view export details, then I see timestamp, version number, and generator model identity.
8. Future Format Placeholders
   - Given the system hasn’t implemented Word/PPT yet, when I request those formats, then I’m informed of roadmap and receive Markdown alternative.
9. Word Export (Post-MVP Behavior Definition)
   - Given Word export is enabled, when I request it, then placeholders map to template styles (Heading 1/2, tables, bullet lists) preserving semantic structure.
10. PowerPoint Export (Post-MVP Behavior Definition)

- Given PPT export is enabled, when I request it, then each major section maps to predefined slide layouts, truncating or splitting content reasonably.

## Non-Functional Notes

- Generation time target < 10s for typical dataset; progress updates every ≤2s if longer.
- Template changes versioned with compatibility flags.

## Edge Cases

- Extremely large ideation lists (>200 items) → summarization fallback with full list in appendix.
- Missing alt text on images → warning injected into output QA report.
