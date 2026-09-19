---
id: T-0187
title: ops/mutate/assemble - the committed mutation population for assemble.py: the producer swap, the distance-default drift, the motor_vehicle=no gate, in the budget_arms.py style with a literal floor
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, services/etl/tests/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0146, T-0176, T-0191]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/mutate/assemble.py (runner) + assemble_mutations.py + assemble_arms.py (populations; 100644): at least the three classes rv1-pr102 found - a RANKED term read off the wrong producer (elevation_gain/relief swap, curvature scaled, furniture fed the count), a restated default drifting (DEFAULT_MOTORWAY_DISTANCE_M = 0.0), a gate half-ported (motor_vehicle=no) - each caught BY NAME by the runner's table; MIN_MUTATIONS and MIN_EQUIVALENT literal floors; EQUIVALENT entries carry a reason and a fingerprint witness"
  - "the runner run bare at the final commit and its table quoted; the pin in pins/PINS.yaml (anchor: process, runs_on: [linux], P-GIT-02 style); whole ETL suite count line and zero skips"
---
## Brief

From the 21:13 panel (PROCESS ruling 6, grounded): a fixer's own mutants become a committed table, not a Log
paragraph. PR #102's round-2 fix pass recorded three classes in prose (the fixer prompt asked for "three
neighbouring mutants"); this task moves them, and the reviewer's three, into ops/mutate/ in the house style so the
next reviewer's must-enumerate list is the file. The fixer prompt no longer asks for prose mutants (memory
pre-review-mutant-pass); the reviewer's three own mutants stay - they found five of today's six blocking findings.

## Log
- 2026-09-19T03:29:43Z filed by agent/claude-fable-5-1 from the 21:13 panel's grounded synthesis. Not started; after #102 merges.
- 2026-09-19T04:34:10Z depends_on += T-0191 by agent/claude-fable-5-1 (22:13 panel, grounded): assemble's population consumes the shared Python protocol module rather than re-deriving geometry_tree.py's COPY tree and JUnit verdict; the divergence cost grows per ETL module, so the extraction lands first.
