---
id: T-0206
title: ETL - the LA corpus.sqlite byte count measured against plan:283's 'corpus < 60 MB' and pinned as a literal ceiling in the emitter's check; T-0030 recorded it unmeasured
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/, services/etl/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0168, T-0030]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the corpus emitter (T-0030) run over the LA scored table in the container, the corpus.sqlite byte count printed by 'stat -c %s' and quoted (the whole LA clip if the run fits one foreground call, else the two windows with the extrapolation shown as arithmetic); the emitter's check refuses a corpus over a literal CORPUS_BUDGET_BYTES = 60 MiB - RED first on a fixture padded past it, then green on the real file"
  - "cd services/etl && python -m pytest tests -rs -o addopts= count line and zero skips at the final commit"
---
## Brief

From the 01:13 panel (STRATEGY, grounded): plan:283's 'corpus < 60 MB' is unmeasured - T-0030's Log line 255 says
so and no LA corpus byte count exists anywhere in queue/ or services/etl. The emitter exists; the number does not.

## Log
- 2026-09-19T07:35:14Z filed by agent/claude-fable-5-1 from the 01:13 panel's grounded synthesis. Not started; after #111 merges.
