---
id: T-0330
title: A reroute answer says whether it continued the drive - /plan marks an answer built from a recalled plan_token apart from the fresh plan it falls back to, and the app rules on a fresh one; the drive screen's ETA line follows the line it draws
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-NAV-01]
reviewer: null
depends_on: [T-0328]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: how often a reroute token is unusable in practice (12 h TTL, device / place mismatch, PLANS unbound), what field marks a continued answer (a boolean on the 200 or the echoed first_pin) without a second coordinate or more than 2 dp, and whether the app takes a fresh answer or rejoins"
  - "The Worker's marker and the app's ruling on it are full-equality tested on both sides (recalled / expired / mismatched device / mismatched place / first_pin past the pins); the drive screen's ETA line is the taken answer's, Linux-tested through DriveDisplay or its successor"
---
## Brief

T-0328 R5 (PR for T-0328): with a token present the device cannot tell a reroute answer from the fresh plan /plan
falls back to when it no longer remembers the token (plan.ts recalls, reroutePlanner.ts recomputes decision points,
both answers have one shape), so the app takes either. T-0328 R6: the drive screen's ETA line stays the preview's
after a reroute is taken.

## Log
- 2026-10-08T18:25:31Z filed by agent/claude-opus-5 from T-0328 R5 and R6.
