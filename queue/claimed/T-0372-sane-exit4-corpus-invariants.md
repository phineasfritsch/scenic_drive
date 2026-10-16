---
id: T-0372
title: ops/sane exit 4 checks the corpus invariants it can see without the graph - no motorway/trunk/private/unpaved way scores above 0, no NULL scores, viewpoints >= the measured floor, surface coverage per class >= baseline - over a corpus.sqlite, local fixture first
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T04:52:58Z
lease_expires_at: 2026-10-17T04:52:58Z
worktree: .worktrees/T-0372
branch: task/T-0372
exclusive: []
touches: [ops/sane, ops/lib/, services/etl/tests/, pins/PINS.yaml]
pins_affected: [P-OPS-08, P-PROD-04]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance: []
---
## Brief

Milestone survey 2026-10-10: `ops/sane` exit 4 checks only the region meta.json counts (ops/sane ~L121-137); the
plan's exit 4 also asks for "no NULL scores; no motorway/trunk/private/unpaved way with score > 0; viewpoints >= 400;
surface-coverage per class >= baseline". The graph-hash half needs the R2 graph (T-0008, owner-gated); the
corpus-only invariants are buildable now against a corpus.sqlite.

MEASURE FIRST: the corpus.sqlite schema (tables/columns for ways, scores, highway class, access, surface, viewpoints,
meta surface coverage) from services/etl, and the LA corpus's actual counts if a built corpus is on disk (quote them;
a predicate over a population nobody measured is a measurement task, CLAUDE.md). RULE each predicate and its literal
threshold from the measurement (viewpoints >= 400 is the plan's Bay Area number - LA's may differ), where the corpus
path comes from (ops/sane is read-only, never mutates), and the skip line when no corpus is present. Then: the checks
in a sane_corpus module (300-line cap), a fixture corpus per predicate side (a violating row per predicate, red by
name; a clean fixture green), exit 4 ordering unchanged (check-sane-exit-order), cases in the sane test table.

## Log
- 2026-10-16T02:30:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (ids checked
  on main and task/T-0361, task/T-0365: highest T-0371).
- 2026-10-16T04:52:58Z claimed by agent/claude-opus-5; lease until 2026-10-17T04:52:58Z
