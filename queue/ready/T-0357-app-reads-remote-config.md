---
id: T-0357
title: The app reads /config - a ConfigClient fetches the Worker's remote config with cached defaults, and the kill switch and min build degrade the UI to the typed PlanError copy instead of failing
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M6 exit: "kill switch by hand -> typed degrade, no 500s"): the Worker serves /config
(services/api/src index.ts, T-0288), but no client in Sources or apps/ios reads it.

MEASURE FIRST: /config's body and every field (quote the Worker), what the app already does on planningPaused
(503 from /plan under KILL=1), and which fields the app could act on. RULE the fields read (fail-closed decoding:
unknown or malformed -> cached defaults, never a crash), the cache (last good answer, bundled defaults), and what the
UI does per field (kill -> planningPaused copy before the user taps Plan; min build above ours -> an update prompt).
Tests through the shipping client: whole-answer equality over every field and bound, decode-failure rows, and the
degrade mapping as a table. Every apps/ios Swift edit needs the P-SAFE-03 digest re-approval; if refused, ship the
Linux slice and say so.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-3).
