---
id: T-0360
title: On regionUnsupported the app offers "Notify me" and posts /waitlist once - a WaitlistClient, the PlanFailureAction gains the waitlist action, and the screen says what it sent
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M6 "region waitlist"): the Worker has /waitlist (T-0293, T-0296);
Sources/ScenicKit/PlanSheet/PlanFailureAction.swift says there is no waitlist screen, and apps/ios has no waitlist
code.

MEASURE FIRST: /waitlist's request and answers (quote the Worker; what it stores - at most one 2-dp cell), how
regionUnsupported reaches the plan sheet today. RULE the action, what is sent (never more than one coordinate at
2 decimals), idempotence (once per region per install), and the copy for each answer. Tests through the shipping
client (exact body equality, every answer) and the failure-action table. Every apps/ios Swift edit needs the
P-SAFE-03 digest re-approval; if refused, ship the Linux slice and say so.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-6).
