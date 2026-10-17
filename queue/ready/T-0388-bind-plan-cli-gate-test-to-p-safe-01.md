---
id: T-0388
title: Bind T-0385's PlanCLIGateValuesTests to P-SAFE-01 by name, and give P-SAFE-01 a check-named-table digest
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml, ops/lib/named-tests.json]
pins_affected: [P-SAFE-01]
reviewer: null
depends_on: [T-0385, T-0382]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

P-SAFE-01's named-tests entry binds the Worker's refusal tests (T-0382: 26 names) but not the CLI body gate's ScenicPlanCLITests.PlanCLIGateValuesTests (T-0385), and P-SAFE-01 carries no check-named-table.py digest, so a test deleted together with its row is green. Bind the CLI suite by name (widen the swift filter only if needed), add check-named-table.py P-SAFE-01 <sha> <count> and its --prove-red before the run-named-tests call (the P-STORE-02/P-PRIV-05 shape), append one dated sentence to why_no_test_catches_it, and show RED (row dropped / test deleted) then green.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0385 stillOpen 1.
