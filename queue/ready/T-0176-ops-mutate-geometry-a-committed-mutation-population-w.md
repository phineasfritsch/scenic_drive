---
id: T-0176
title: ops/mutate/geometry - a committed mutation population with a floor for the ETL geometry terms (sinuosity.py, proximity.py); EQUIVALENT rulings carry a witness
state: ready
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
depends_on: [T-0161]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/mutate/geometry.py (runner) + geometry_mutations.py + geometry_arms.py, all 100644 like every ops/mutate/*.py, modelled on budget.py / budget_arms.py: MUTATIONS enumerates the five classes PR #94 bought one round each - segment subset, chord-for-path, candidate order/ties, interior-interior pair cell, earth model/normalisation - with at least one case each; MIN_MUTATIONS and MIN_EQUIVALENT are literal floors; RED by name: the runner refuses when a class is missing, then green"
  - "every EQUIVALENT entry carries a REASON and a witness (a byte-identical fingerprint over the fixture population), never prose; the round-3 'interior-interior is equivalent' claim is the worked NON-example in the docstring"
  - "the runner prints a table (mutant -> named red tests) and exits non-zero on any survivor; run bare at the final commit and quoted; a pin in pins/PINS.yaml (anchor: process, runs_on: [linux]) in the P-GIT-02 style"
---
## Brief

From the 2026-09-18 17:13 panel (PROCESS lens, grounded). PR #94 (T-0161) went four review rounds on ONE shape -
"the fixture's geometry population is degenerate on axis X, so a mutant restricted to a subset of the
segment-pair matrix survives with nothing red" - refiled each round with a new X (single segment; collinear;
interior-interior). The repository already owns the mechanism it lacked: `ops/mutate/budget.py` refuses when
`len(MUTATIONS) < MIN_MUTATIONS` or `len(EQUIVALENT) < MIN_EQUIVALENT`, and `budget_arms.py`'s EQUIVALENT
entries each carry a reason plus a fingerprint. T-0161's mutation table lives only as prose in its task file,
and the round-3 "equivalent in the plane" ruling was falsified at five nodes against four. This population is
simultaneously the fixer's brief and the reviewer's must-enumerate list. It lands before T-0168 imports
proximity.py; today nothing outside the two test files does. CLAUDE.md's Verification now carries the rule.

## Log
- 2026-09-19T00:40:47Z filed by agent/claude-fable-5-1 from the 17:13 panel's grounded synthesis; ready/ with its acceptance block. Not started.
- 2026-09-19T01:58:22Z SIXTH CLASS, from agent/rv4-pr94's PASS entry on PR #94 (recorded there, not bought as a round, per the
  17:13 ruling), by agent/claude-fable-5-1: "banded / diagonal-window subset of the segment-pair matrix" -
  `line_distance_m` keeping only pairs with `abs(i - j) <= 1` (the shape a monotone-sweep pruning would have)
  survives all 608 tests: it KEEPS the interior-interior pairs (the 5-vs-4 case's minimum sits at (1,1) and
  (2,1), on or next to the diagonal), the first and last segments, and is neither the chord, the candidate
  order nor a normalisation, and it lets a wrong motorway distance reach score.py. The population this task
  builds carries it as its sixth class with a fixture whose minimum sits far off the diagonal (a long way
  against a short motorway, or the reverse), red by name.

