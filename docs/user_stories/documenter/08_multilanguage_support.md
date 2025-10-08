# User Story 08 – Multilanguage Support

## Story

As a facilitator, I want the assistant to operate and generate documentation in my chosen language so that workshops can run natively for any supported locale.

## Description

Language is auto-detected from initial facilitator input with ability to override manually. All prompts, summaries, validations, and exports match session language. Mixed-language content (e.g., names, terms) is preserved without forced translation unless explicitly requested.

## Acceptance Criteria

1. Auto Detection
   - Given I begin a session in Spanish, when the assistant replies, then it continues in Spanish unless I override.
2. Manual Override
   - Given I enter a command ("/language de"), when processed, then subsequent prompts and generation switch to German while existing content remains unaltered.
3. Supported Locale Validation
   - Given I request an unsupported locale, when processed, then I receive a list of supported codes.
4. Documentation Language Consistency
   - Given I generate the output, when I inspect sections, then headings and boilerplate reflect the active language.
5. Per-Item Translation (Optional)
   - Given I highlight or reference a specific text and request translation ("translate that to English"), when performed, then the translation is appended without overwriting original.
6. Mixed Content Preservation
   - Given domain-specific English terms appear in a German session, when output generates, then terms remain intact unless a glossary translation mode is enabled.
7. Language Metadata
   - Given a session summary, when displayed, then the active language code (e.g., `es-ES`) is present in metadata.
8. Accent & Character Handling
   - Given I input characters with diacritics or non-Latin scripts, when stored, then retrieval returns exact Unicode without loss.

## Non-Functional Notes

- Automatic detection confidence threshold; fallback to English if below threshold.
- Language packs loaded lazily to reduce initial latency.

## Edge Cases

- Rapid language switching mid-phase → confirm dialog to prevent accidental toggle.
- Pasted multi-language block → no forced normalization; detection logs ambiguous state.
