# User Story 07 – Session Management & Persistence

## Story

As a facilitator, I want my workshop progress auto-saved and resumable so that I can pause or recover from interruptions without data loss.

## Description

Workshops are uniquely identified. All interactions (inputs, uploads, transcripts, navigation state) persist automatically. Users can explicitly save, rename sessions, and resume from a dashboard or link. Session isolation prevents data leakage across users.

## Acceptance Criteria

1. Autosave
   - Given I submit new content, when ≤1s passes, then the change is persisted (confirmed by silent success or optional debug log).
2. Manual Save
   - Given I issue a "save" command, when executed, then I receive confirmation with session name and timestamp.
3. Session Naming
   - Given a new session starts, when the system auto-generates a title, then it reflects business context (e.g., client name + focus) if provided.
4. Resume Session
   - Given I have prior sessions, when I choose one, then all structured data, transcripts, uploads, and phase statuses restore.
5. Concurrency Protection
   - Given the system doesn’t yet support multi-user editing, when a second browser attempts to open the same session, then a warning about unsupported concurrent editing is shown.
6. Version Snapshots
   - Given I request a snapshot ("snapshot"), when executed, then a point-in-time label is created for rollback reference.
7. Rollback
   - Given snapshots exist, when I roll back to a snapshot, then subsequent changes after that point are not deleted but a forked version is created (or rollback disallowed with explanation if forks unsupported).
8. Secure Storage
   - Given data is persisted, when examined at rest, then it's scoped to the facilitator identity (logical isolation metadata recorded).
9. Expiration Policy
   - Given a session exceeds retention period (configurable), when a facilitator returns, then they receive either an expiration notice or option to restore from cold archive (if enabled).

## Non-Functional Notes

- Persistence operations idempotent and retried on transient store errors (up to 3 attempts).
- Session identifier format: ULID or UUIDv7 for temporal ordering.

## Edge Cases

- Network loss mid-submit → local queue and retry on reconnect.
- Large batch restore performance target < 3s (95th percentile typical session).
