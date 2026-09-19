---
id: T-0215
title: ops/mutate - populations with literal floors for services/etl/etl/score.py and curvature.py, and the gate's DEBT table printed ranked by downstream reach, not flat
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, ops/lib/, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0207, T-0191]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/mutate/score.py and ops/mutate/curvature.py in the shared-protocol shape (T-0191), each mutation killed BY NAME, EQUIVALENT entries with a witness, floors literal, registered in DRIVERS/COVERED_FLOOR; the gate's DEBT print ordered by how many shipped numbers each module reaches (score.py first), with the ordering rule stated in the gate"
  - "python ops/lib/check-mutate-population.py, both runners + --prove-vacuity, the ETL suite count line, check-line-cap, check-exec-bits, queue-check bare"
---
## Brief

From the 04:13 panel (CODE, grounded): the gate lists 24 numeric modules with no population, flat. score.py is the
composition every scenic_score is quantised from and the gate's own docstring names it as the entry that would buy
a dishonest allowlist line; curvature.py's oracle runs only at fixture scale. normalise.py's population rides T-0208.

## Log
- 2026-09-19T11:43:44Z filed by agent/claude-fable-5-1 (04:13 panel; grounded 8 of 14 - only the grounded items applied). Not started; after T-0207 (which edits score.py) and T-0191.
