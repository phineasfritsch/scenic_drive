---
id: T-0252
title: the Worker serves POST /loop - "just drive 45 minutes and come back": one round_trip request (lambda 2, seeded by user+date), the anti-retrace check ported from ScenicKit RetraceDetector, at most 2 retries, quota first, kill switch honoured
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-05T09:05:18Z
lease_expires_at: 2026-10-05T19:05:18Z
worktree: .worktrees/T-0252
branch: task/T-0252
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01, P-COST-04, P-PRIV-05, P-SAFE-01]
reviewer: null
depends_on: [T-0248]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RULED in the Log before code from the plan's Problem B: request shape (start as one coordinate at <= 2 dp, minutes), round_trip.distance = v_eff * T_loop, the seed from (user, date), lambda 2, the custom model from buildCustomModel; the retrace check is a byte-faithful port of Sources/ScenicKit/Loop (25 m cells, heading delta > 150 deg, < 15% of length) - a shared fixture proves the TS port and the Swift original give the SAME verdict and fraction on at least 5 recorded loops (exact equality)"
  - "quota decremented before any upstream call; KILL=1 -> 503 with zero upstream calls; at most 3 upstream requests per loop (P-COST-04) - reseed then areas on retraced edges, max 2 retries - each by a counting-fake test by name"
  - "the response carries geometry, duration, the retrace fraction and the Apple Maps URL; vitest count quoted; the new module's mutation population with a literal floor (the same vitest-driven form T-0248 ruled)"
---
## Brief

Milestone survey 2026-10-04: M5 loop has the engine (ScenicKit Loop/RetraceDetector) but no endpoint. Same shape as /plan (T-0248).

## Log
- 2026-10-05T09:04:49Z filed by agent/claude-opus-5 (orchestrator) after PR #139 (T-0248) merged.
- 2026-10-05T09:05:18Z claimed by agent/claude-opus-5; lease until 2026-10-05T19:05:18Z
