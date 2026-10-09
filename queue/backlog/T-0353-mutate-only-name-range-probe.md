---
id: T-0353
title: check-mutate-only probes a range of two REAL ids for name-keyed populations (mjs drivers, substring drivers, plansheet E-ids), so an `A-B` name-range expansion in onlyIds.mjs / mutate_only is refused
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-mutate-only.py, ops/mutate/mutate_only.py, services/api/test/mutate/onlyIds.mjs]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0347]
verify: [ops/check-pins]
acceptance: []
---
## Brief

rv2-t0347 recordable 2 (PR #233, last harness round, filed per the two-round rule). T-0347 R3 says ranges are refused
everywhere, but check-mutate-only's range probe builds `A-B` from two all-digit ids only; otherwise it uses an
`N-(N+1)` that matches no real id. Mutant D - a name-range expansion in onlyIds.mjs (a token `A-B` whose halves are
both known ids selects ids[A..B]; onlyIds(['--only','tier-case-sensitive-tier-inactive-paid']) returned 3 ids) -
left the check at `MUTATE-ONLY OK: 165 of 165`. E-prefixed ids (plansheet) are uncovered the same way.

Fix as the reviewer suggested: when a driver has no two all-digit ids, also probe `<id0>-<id1>` from its first two
listed ids (after confirming no id equals or contains that token) and require exit 64. Demonstrate red with mutant D
and with an E-id range expansion in mutate_only, then green. Also show the "names no entry, no ONLY IDS line" failure
branch red with its own mutant (T-0347 owner stillOpen 2).

## Log
- 2026-10-09T23:40:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0347 recordable 2.
