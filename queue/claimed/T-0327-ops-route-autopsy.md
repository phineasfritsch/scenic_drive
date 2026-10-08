---
id: T-0327
title: ops/route-autopsy - one command dumps a bad drive's per-edge GATE / M / E terms and the lambda trace, so a reported rat-run or dull route becomes a pinned negative fixture before any weight changes (the plan's gate-failure playbook)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T17:16:10Z
lease_expires_at: 2026-10-09T03:16:10Z
worktree: .worktrees/T-0327
branch: task/T-0327
exclusive: []
touches: [ops/route-autopsy, ops/lib/, Sources/ScenicPlanCLI/, Sources/ScenicKit/, Tests/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: what ops/plan / scenic-plan already print (the per-edge term table, the bisection trace), what a 'plan id' can be when the server keeps no plans (T-0319's plan_token lives 12 h in KV and holds pins + lambda, not edges; a recorded fixture dir; or O/D/budget/departs-at re-planned against a recorded router) - rule the input honestly, never invent a server-side plan store; and where the per-edge GATE, M and E terms come from (ScenicKit scoring over the corpus segment ids, or GraphHopper path details)"
  - "ops/route-autopsy prints, for a recorded plan, every edge with its gate verdict (and which safety rule), M and E terms, scenic_score and length, plus the lambda trace (each bisection step's lambda and duration) and the RouteScore terms - full-equality golden over one recorded fixture; a --fixture flag writes the plan as a pinned NEGATIVE fixture under Tests/ (the playbook's 'a bad drive becomes a pinned negative fixture before any weight changes')"
  - "Wrapper discipline as ops/plan: no decision in bash, the engine is the Swift CLI; committed executable (P-OPS-01); usage on no args; seen red (a golden row changed) then green; a mutation population for any new Swift numeric code"
---
## Brief

Plan: Runtime lifecycles, Gate-failure playbook (`ops/route-autopsy <plan-id>` dumps per-edge GATE/M/E terms + lambda
trace; a bad drive becomes a pinned negative fixture before any weight changes) and M3's list. Owner intent (memory
owner-route-intent): one residential rat-run ends the relationship - this is the tool that turns that report into a
fixture. Measured 2026-10-08: ops/ has plan, score-review and etl-* but no route-autopsy; no task named it.

## Log
- 2026-10-08T17:15:53Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M3 ops/route-autopsy).
- 2026-10-08T17:16:10Z claimed by agent/claude-opus-5; lease until 2026-10-09T03:16:10Z
