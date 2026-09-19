---
id: T-0226
title: pins - P-SRC-01 scans every target path the root manifest declares (executables included), not the literal Sources/: demonstrated red with an executable target outside Sources/ importing UIKit
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, pins/PINS.yaml]
pins_affected: [P-SRC-01]
reviewer: null
depends_on: [T-0182]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the import-ban check reads the target paths out of Package.swift (every target's `path:` or the default Sources/<name>) and greps each; RED first on a copy with an executable target declared at Tools/x importing UIKit (today invisible to the grep over Sources/); PINS.yaml's P-SRC-01 text names the population; bash ops/check-pins --source-only, check-exec-bits, queue-check bare"
---
## Brief

From the 11:13 panel (CODE, fable-grounded on PINS.yaml:9,13 and ops/test:23): the root package gains its first
executable product with T-0182's ops/plan; a target placed outside Sources/ is scanned by nothing, and ops/test builds
every target on both boxes. Lands with or after T-0182.

## Log
- 2026-09-19T20:26:45Z filed by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0). Not started; harness, two rounds.
