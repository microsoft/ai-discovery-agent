# User Story 05 – Document & Diagram Upload

## Story

As a facilitator, I want to upload supporting documents and diagrams so that referenced materials enrich the workshop outputs.

## Description

Supports upload of PDFs, Word documents, images (PNG/JPG), and hand-drawn photos. Extracted text (where feasible) is optionally incorporated as contextual references. Images can be embedded or linked in summaries and generated documentation.

## Acceptance Criteria

1. File Type Support
   - Given I attempt to upload a supported file type, when processed, then it is accepted and stored with metadata (name, size, MIME, hash).
2. Rejection Handling
   - Given I upload an unsupported file type, when processed, then I receive a clear error listing allowed types.
3. Virus / Security Scan Hook
   - Given a file is uploaded, when stored, then (if security scanner enabled) a pending status is shown until cleared; blocked files not incorporated.
4. Text Extraction (Optional)
   - Given I upload a PDF with selectable text, when processed, then extracted text is available on request ("show extracted text").
5. Image Preview
   - Given I upload an image, when stored, then a thumbnail or link preview is rendered in the phase summary.
6. Reference Linking
   - Given a file is uploaded, when I reference it by name (or index) in chat, then the assistant can confirm the reference and optionally summarize the content if under size limits.
7. Deletion
   - Given I delete an uploaded file, when confirmed, then it no longer appears in summaries nor in generated documentation.
8. Size Limits
   - Given I exceed file size threshold, when upload completes, then I receive a rejection with recommended remediation (compress / segment file).
9. Accessibility Metadata
   - Given an image is uploaded, when prompted, then I can add alt text stored with the asset.
10. Export Inclusion

- Given documentation is generated, when output is produced, then selected uploads are either embedded (images) or appended (documents) per template rules.

## Non-Functional Notes

- Large file upload progress every ≤1s.
- Storage uses secure container with unique session scoping.

## Edge Cases

- Duplicate file name → versioned suffix or hash-derived name.
- Corrupt PDF → extraction gracefully skipped, file still referenceable.
