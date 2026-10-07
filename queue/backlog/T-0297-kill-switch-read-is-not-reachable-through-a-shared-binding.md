---
id: T-0297
title: The kill decision cannot be bent by a handler writing to a shared binding object - KILL_SWITCH is read through a per-request wrapper, and a handler that patches a binding method is refused or harmless
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/api/src/, services/api/test/]
pins_affected: [P-COST-01]
reviewer: null
depends_on: [T-0292]
verify: [ops/check-pins]
acceptance:
  - "RULE FIRST: which binding methods the kill decision reads (KILL_SWITCH.get, the KILL string) and how a per-request read path is made independent of mutations to the shared binding object (e.g. capture the binding's prototype method at module load and call it with the binding as this, or wrap bindings in a per-request read-only facade)"
  - "Through worker.fetch on one shared env: a handler that assigns env.KILL_SWITCH.get = async () => null on its first call does not unpause any later request under KV KILL=1 - full equality over the shared-env kill table"
  - "Population entry for the binding-method patch, MISSED before and CAUGHT by name after"
---
## Brief

T-0292 residual R-A (PR #183, owner and rv2-t0292): the per-request env copy is frozen shallowly; a handler that writes to
a shared binding object (env.KILL_SWITCH.get) still reaches later requests. fm-t0292 showed the shared-env tables
DETECT it for KILL_SWITCH; this task REFUSES it.

## Log
- 2026-10-07T11:09:18Z filed by agent/claude-opus-5 (orchestrator) from T-0292 residual R-A.
