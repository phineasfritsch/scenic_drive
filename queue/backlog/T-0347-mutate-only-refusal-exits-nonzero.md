---
id: T-0347
title: Every ops/mutate driver's `--only` refusal ("names no entry of this population") exits non-zero, so a typo'd range (`--only 49-55`) can never read as a pass
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/mutate/, ops/lib/]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: []
verify: [ops/check-pins]
acceptance:
  - "MEASURE first: every driver under ops/mutate/ (and services/api/test/mutate/*.mjs) and what each does on `--only` with an unparseable or empty selection (exit code, message); quote the table"
  - "Every driver exits non-zero (a distinct refusal code, ruled) when `--only` names no entry or does not parse; ranges either parse as ranges everywhere or are refused everywhere (ruled); one shared parser where the drivers already share code"
  - "A meta-check under ops/lib runs each driver with `--only 999999` and `--only 1-2x` and refuses unless every one exits non-zero, seen red (one driver reverted) then green"
---
## Brief

rv1-t0342 recordable 2 (PR #229): `ops/mutate/plansheet.py --only 49-55` prints "REFUSING TO RUN: --only names no
entry of this population" and still exits 0, so a range typo looks like a pass when only the exit code is read
(memory pipe-swallows-gate-exit-status is the same failure shape).

## Log
- 2026-10-09T17:29:06Z filed by agent/claude-opus-5 (orchestrator) from rv1-t0342 recordable 2.
