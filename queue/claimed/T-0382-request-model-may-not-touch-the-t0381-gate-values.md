---
id: T-0382
title: The request custom model may not touch the T-0381 gate values - FORBIDDEN_ENCODED_VALUES gains track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T23:03:37Z
lease_expires_at: 2026-10-17T23:03:37Z
worktree: .worktrees/T-0382
branch: task/T-0382
exclusive: []
touches: [services/api/src/customModel.ts, services/api/test/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0381]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 FORBIDDEN_ENCODED_VALUES in services/api/src/customModel.ts names every encoded value a hard-gate clause of the SHIPPED services/routing/profiles/car_scenic_base.json reads (road_access, surface, track_type, smoothness, gate_locked_barrier, gate_ford, gate_service_way), and a test derives that set FROM the shipped profile json (the identifiers in each `multiply_by: 0` priority clause) and compares it to the exported constant by full equality - never a restated list"
  - "A2 for each of the seven names, a request model whose priority or speed clause reads it is refused through the shipping entry point (the Worker's custom-model builder production calls), table-tested per name, and a near miss (a name that merely contains one, e.g. track_type_x if the reader tokenises) is answered as the code rules it, quoted"
  - "A3 RED first by name: on the pre-change constant the five new names' refusal rows fail (quoted), then green"
  - "A4 bare gates: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check"
---
## Brief

T-0381 (PR #273) gave the base routing profile five new hard gates: `track_type` GRADE3-5, `smoothness` BAD and
worse, and three boolean encoded values from the scenic-score-parser plugin, `gate_locked_barrier`, `gate_ford`,
`gate_service_way`. The Worker lets a request carry its own custom model, and refuses one that reads a safety
gate's encoded value: `FORBIDDEN_ENCODED_VALUES = ["road_access", "surface"]` (customModel.ts, measured on main
325c2cd3, line 34). A request model that multiplies by a clause over `gate_ford` or `track_type` is therefore not
refused today. Whether such a clause can UNDO a base `multiply_by: 0` is GraphHopper's merge rule, so measure it
first (GraphHopper 11 multiplies priority factors; a request `multiply_by` above 1 is capped) and rule it in the
Log - the refusal stays the fail-closed answer either way, as it is for road_access and surface.

Filed by agent/claude-opus-5 from T-0381 rv1 (R10 stillOpen). Depends on T-0381 merging: the five names exist in
the profile only on task/T-0381 until then.

## Log
- 2026-10-16 filed by agent/claude-opus-5 from T-0381 stillOpen (R10); ids checked on origin/main and every
  origin/task/* branch: max T-0381 (T-9901 is the T-0128 demo fixture), no task names FORBIDDEN_ENCODED_VALUES
  beyond T-0182 (done) and T-0381 itself.
- 2026-10-16T23:03:37Z claimed by agent/claude-opus-5; lease until 2026-10-17T23:03:37Z
