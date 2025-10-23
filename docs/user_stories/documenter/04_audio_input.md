# User Story 04 – Audio Input & Transcription

## Story

As a facilitator, I want to record spoken discussion and have it transcribed into structured, editable workshop content so that I can capture insights without manual typing.

## Description

The UI provides a microphone control (toggle). Audio segments are streamed or batch uploaded, transcribed, attributed (timestamped), and inserted into the relevant phase context. Facilitator can edit, approve, or discard transcripts before inclusion in summaries.

## Acceptance Criteria

1. Start/Stop Control
   - Given I click the microphone button, when recording begins, then visual state changes (e.g., animated icon) and a timer displays.
2. Abort Recording
   - Given I am recording, when I press cancel/stop, then partial audio is either discarded (cancel) or processed (stop) per action.
3. Transcription Latency
   - Given a recording < 60s, when stopped, then draft transcript appears within 5s or a progress indicator updates every ≤2s.
4. Edit Before Commit
   - Given a transcript is generated, when displayed, then I can edit text and accept or reject inclusion.
5. Phase Association
   - Given I record during a specific phase, when transcript is saved, then it’s tagged with that phase’s identifier.
6. Manual Reassignment
   - Given a transcript is mis-tagged, when I edit metadata, then reassignment to another phase is reflected in summaries.
7. Multi-Language Audio
   - Given session language is non-English, when I record, then transcription uses matching locale model and preserves language.
8. PII Safeguards
   - Given transcript includes detected PII (configurable patterns), when flagged, then I receive a warning with redact/keep options.
9. Timestamp Metadata
   - Given a transcript segment, when I view details, then start/end timestamps (relative to session) are available.
10. Deletion

- Given I delete a transcript, when confirmed, then it no longer appears in any summaries or exports.

## Non-Functional Notes

- Audio formats supported: WebM/Opus (primary), fallback WAV.
- Transcription accuracy target ≥ baseline model performance; retries on transient API errors.

## Edge Cases

- Very long continuous recording (>15m) → graceful segmentation.
- Network drop mid-upload → resumable chunk or user notification with retry.
