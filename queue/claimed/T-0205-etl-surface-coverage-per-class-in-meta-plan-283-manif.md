---
id: T-0205
title: ETL - surface-coverage per class in meta (plan:283): the corpus manifest carries surface known/unknown/unpaved counts per highway class over the region clip, with the pytest and a pin; nothing writes it today
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T10:49:25Z
lease_expires_at: 2026-09-19T15:49:25Z
worktree: .worktrees/T-0205
branch: task/T-0205
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0168, T-0173]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the corpus meta (manifest.py / corpus.py - rule which owns it) carries, per highway class, the count of ways with a positive surface tag, with surface unknown (the three-state column T-0173 shipped), and gated unpaved; written by the assembly over the scored table - RED BY NAME first: a test that reads meta from a fixture corpus and asserts the per-class table, red until the writer exists; the ops/sane check-4 'surface-coverage per class >= baseline' clause becomes a number printed by a check that refuses below a literal baseline per class (the baseline recorded from the LA window's real counts, quoted)"
  - "a pin in pins/PINS.yaml (P-DATA-01's neighbour or its own id - rule it) whose assertion runs the check over the committed fixture; cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips"
---
## Brief

From the 01:13 panel (STRATEGY, grounded): plan:283's M2 exit names 'surface-coverage per class in meta' and
nothing in services/etl/etl/manifest.py, corpus.py or schema.py writes a coverage key - T-0024 is per-class
COUNTS, T-0173 is the three-state surface column. The plan's own rationale: the absent-surface rule (primary/
secondary/tertiary assumed paved, residential x0.8 with a surface_unknown flag) is only honest if the per-class
coverage is measured and watched.

## Log
- 2026-09-19T07:35:14Z filed by agent/claude-fable-5-1 from the 01:13 panel's grounded synthesis. Not started; after #111 merges.
- 2026-09-19T10:46:00Z PROMOTED to ready/ by agent/claude-fable-5-1 (03:13 panel, grounded): its dependencies (T-0168, T-0173) are in done/, no lock; an unmet M2 exit clause (plan:283); the fallback START while #113 holds the scenic-index lock.
- 2026-09-19T10:49:25Z claimed by agent/claude-opus-5; lease until 2026-09-19T15:49:25Z
