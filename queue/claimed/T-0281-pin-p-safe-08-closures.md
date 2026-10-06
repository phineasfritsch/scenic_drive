---
id: T-0281
title: register P-SAFE-08 (closures fresh within 30 min; a route never crosses an active closure; stale/unavailable never silent) over T-0276's tests, and bind T-0276's shipped-route closure tests under P-SAFE-01
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T14:11:11Z
lease_expires_at: 2026-10-06T22:11:11Z
worktree: .worktrees/T-0281
branch: task/T-0281
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-08, P-SAFE-01]
reviewer: null
depends_on: [T-0276, T-0261]
verify: [ops/test, ops/check-pins]
acceptance:
  - "pins/PINS.yaml gains P-SAFE-08 (the plan's statement; anchor api; runs_on linux) asserted by run-named-tests.py over the named closuresRoutes/closuresCron/closuresFeed tests: the 30-min boundary rows (fresh at exactly 30 min, stale at +1 ms), the unavailable cross-product meta-test, the every-driven-request-carries-the-areas tests and the cron active-window clock table; each binding RED by a one-line mutant of src/ quoted in the Log, then green; WHAT IT CANNOT SEE names /isochrone's missing areas (T-0276 R8), the 50-polygon cap dropping closures, and the owner's unbound CLOSURES KV"
  - "prose APPENDED with dates, never rewritten; run-named-tests for P-SAFE-08 and P-SAFE-01 exit 0"
---
## Brief

T-0276 stillOpen 2: 'P-SAFE-08 needs a PINS.yaml row and a by-name binding; pins/ was outside this task's touches'.
The T-0261/T-0269 pattern.

## Log
- 2026-10-06T14:08:18Z filed by agent/claude-opus-5 (orchestrator) after PR #167 (T-0276) merged.
- 2026-10-06T14:11:11Z claimed by agent/claude-opus-5; lease until 2026-10-06T22:11:11Z
