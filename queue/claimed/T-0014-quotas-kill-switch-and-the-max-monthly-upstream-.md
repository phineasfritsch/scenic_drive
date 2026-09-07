---
id: T-0014
title: Quotas, kill switch and the MAX_MONTHLY_UPSTREAM_CALLS compile-time constant (P-COST-01, P-COST-02)
state: claimed
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T14:48:38Z
lease_expires_at: 2026-09-07T18:48:38Z
worktree: ../wt/T-0014
branch: task/T-0014
exclusive: []
touches: [services/api/, pins/PINS.yaml]
pins_affected: [P-COST-01, P-COST-02]
reviewer: null
depends_on: [T-0005]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

(what, why, and the exact demonstration that proves it — including the red run)

## Log
- 2026-09-07T14:50:00Z promoted backlog -> ready: its dependency (the Worker skeleton, T-0005) is merged, so quotas/kill switch is unblocked. Also the only remaining task whose files (services/api/) are not held by an open PR, which makes it the one thing that can proceed in parallel without two branches editing one file.
- 2026-09-07T14:48:38Z claimed by agent/claude-opus-5; lease until 2026-09-07T18:48:38Z
