# User Story 11 – Usability & Accessibility

## Story

As a facilitator, I want an intuitive, accessible interface so that I can efficiently conduct workshops regardless of device or accessibility needs.

## Description

Implements WCAG 2.1 AA principles: keyboard navigation, ARIA roles, color contrast, focus management, semantic structure. Provides clear, concise prompts with optional expanded help. Supports screen readers and accessible labeling for controls (mic, upload, generate, navigate).

## Acceptance Criteria

1. Keyboard Navigation
   - Given I tab through the interface, when navigating, then all interactive elements receive visible focus in logical order.
2. Screen Reader Labels
   - Given I use a screen reader, when focusing on microphone or upload buttons, then descriptive labels (not just icons) are announced.
3. Color Contrast
   - Given UI text or icons, when measured, then contrast ratio meets WCAG 2.1 AA (≥ 4.5:1 normal text / 3:1 large text).
4. Error Announcements
   - Given a validation error occurs, when using assistive tech, then the error message region is announced automatically.
5. Responsive Layout
   - Given I resize the window or use a tablet width (≥768px), when viewing, then layout adapts without horizontal scroll for core content.
6. Help Expansion
   - Given I request more detail ("help"), when displayed, then supplemental guidance appears in a collapsible section to reduce clutter.
7. Focus Retention
   - Given an operation triggers a re-render (e.g., phase switch), when complete, then keyboard focus returns to a predictable container (e.g., input area).
8. Alt Text Prompt
   - Given I upload an image, when stored, then I’m prompted to optionally add alt text which is preserved in exports.
9. Timeouts
   - Given inactivity for a configured period, when session warning appears, then keyboard and screen reader users receive a clear countdown with option to extend.

## Non-Functional Notes

- Accessibility checks integrated into CI (linting / automated audits where feasible).
- Uses semantic HTML structure for headings and lists.

## Edge Cases

- High contrast OS mode → UI respects system preferences.
- Reduced motion preference → animation durations minimized or disabled.
