---
id: T-0198
title: ops/test's python tier discovers every services/*/pyproject.toml (tiles, routing) instead of services/etl alone, and the floor counts them; red first on a services/tiles test made to fail
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [pins/floor_linux.txt]
touches: [ops/test, ops/lib/, pins/]
pins_affected: []
reviewer: null
depends_on: [T-0165]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/test Tier 1c runs pytest --junitxml for every services/*/pyproject.toml it finds (etl, tiles, routing - the routing suite's routed tests skip without docker and still count), the count line names each; RED first: a services/tiles test forced red makes ops/test exit non-zero, today it stays green"
  - "pins/floor_linux.txt ratcheted by the reviewer to include the new suites' counts (the floor file is serial - exclusive: declared); TESTS linux=N/F line quoted before and after"
  - "bash ops/test bare at the final commit with its count line; bash ops/check-pins --source-only"
---
## Brief

From T-0165's STILL OPEN 1 and rv2-pr105's recordable: ops/test's python tier is gated on services/etl/pyproject.toml,
so the 28 services/tiles tests and services/routing's static profile tests run in no CI job - green means core +
pins-source-only. A regression in either directory is invisible to the one command the harness rests on.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 1 (PR #109) and rv2-pr105's recordable on PR #105. Not started.
