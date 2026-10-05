---
id: T-0250
title: store and legal copy drafts - privacy policy, support page, terms of use, App Store description (with the 3.1.2 subscription text), App Review notes - committed as reviewable Markdown under docs/store/, true to what the app does today
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T07:15:22Z
lease_expires_at: 2026-10-05T13:15:22Z
worktree: .worktrees/T-0250
branch: task/T-0250
exclusive: []
touches: [docs/store/]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "docs/store/{privacy,support,terms,app-store-description,review-notes}.md exist; every factual claim about data handling is traceable to the code or the plan's invariants and cited inline by path (the server never receives more than one coordinate per user action, never more than 2 decimal places; learned speeds never leave the device; no account required; telemetry is H3-5 cells and durations only; OpenStreetMap ODbL attribution) - a claim the code does not yet implement is marked PLANNED, never stated as fact"
  - "the App Store description uses the owner's positioning and tagline verbatim ('calm adventure', 'Take the long way. Unwind.'), no thrill words, US-only, and the Apple 3.1.2 auto-renewing subscription disclosure for the plan's $29.99/yr with 7-day trial; review notes explain the safety disclaimer, the location-denied path and how to reach the paid features - each marked DRAFT FOR THE OWNER (a lawyer reviews privacy/terms; plan M0)"
---
## Brief

Milestone survey 2026-10-04: M0's privacy/support/terms pages and M6/M8's listing copy are MISSING and need no device or
account to draft. The owner hosts them on their domain later.

## Log
- 2026-10-05T07:12:33Z filed by agent/claude-opus-5 (orchestrator) from the milestone survey.
- 2026-10-05T07:15:22Z claimed by agent/claude-opus-5; lease until 2026-10-05T13:15:22Z
