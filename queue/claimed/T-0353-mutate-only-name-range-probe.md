---
id: T-0353
title: check-mutate-only probes a range of two REAL ids for name-keyed populations (mjs drivers, substring drivers, plansheet E-ids), so an `A-B` name-range expansion in onlyIds.mjs / mutate_only is refused
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T23:39:59Z
lease_expires_at: 2026-10-10T03:39:59Z
worktree: .worktrees/T-0353
branch: task/T-0353
exclusive: []
touches: [ops/lib/check-mutate-only.py, ops/mutate/mutate_only.py, services/api/test/mutate/onlyIds.mjs]
pins_affected: [P-PROC-06]
reviewer: null
depends_on: [T-0347]
verify: [ops/check-pins]
acceptance:
  - "A1 GREEN: `python ops/lib/check-mutate-only.py` exits 0 and prints `MUTATE-ONLY OK: 203 of 203 driver runs refused with exit 64 (55 drivers, 93 range probes: 19 digit, 38 name, 36 N-(N+1))` - the counts measured on 2026-10-09 (19 drivers with two all-digit ids, 38 with at least one non-digit id, 36 with no digit range); the tree is unchanged after the run"
  - "A2 RED (a): mutant D in services/api/test/mutate/onlyIds.mjs (a token `A-B` whose halves are both known ids selects ids[A..B]) makes the check exit 1 with a `NOT REFUSED:` line for each of the 17 *Mutants.mjs drivers naming its name-range token, e.g. `services/api/test/mutate/tierMutants.mjs --only tier-case-sensitive-tier-any-token-read`; restored byte-identical (sha256 + git diff --quiet HEAD) and A1 green again"
  - "A3 RED (b): an E-id range expansion in ops/mutate/mutate_only.py select_only (`E<a>-E<b>` with both halves known selects E<a>..E<b>) makes the check exit 1 with a `NOT REFUSED:` line naming `--only E1-E2` (or `E1-E1` for a driver with one E-id) for each of the 17 Python drivers that carry an E-id, e.g. `ops/mutate/plansheet.py --only E1-E2`; restored byte-identical and A1 green again"
  - "A4 RED (c): mutate_only.select_only with its `ONLY IDS:` line removed makes the check exit 1 with `NOT REFUSED: ops/mutate/plansheet.py --only 999999 ... the refusal lists no ONLY IDS: line` (one per Python driver with --only) and the name-range floor line `NAME-RANGE PROBES <n> below floor 38`; restored byte-identical and A1 green again"
  - "A5 gates on the merged head, each run bare: check-mutate-only, check-mutate-population, check-exec-bits, check-pins-yaml, queue-check exit 0; ops/lib/check-mutate-only.py stays under the 300-line cap"
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
- 2026-10-09T23:40:00Z claimed by agent/claude-opus-5; lease until 2026-10-10T03:39:59Z
- 2026-10-09T23:43:50Z MEASURED (.build-t0353/measure.py: every driver run with `--only 999999`, its `ONLY IDS:`
  line parsed, the current range_token() applied; tree unchanged after). 55 drivers:
  - A-B over two all-digit ids (token `1-2`): 19 - accounttoken corpusfetch corpusota drive hazardcopy ledger
    loopsheet onboarding plansheet saveddrive savedlist segmentgeometry session shownhistory straightline surprise
    telemetry traffic tripsheet. 17 of them ALSO list E-ids no probe touches (two or more: drive ledger plansheet
    saveddrive segmentgeometry session surprise; exactly one E1: accounttoken corpusfetch corpusota hazardcopy
    loopsheet onboarding savedlist shownhistory traffic tripsheet); straightline and telemetry list digits only.
  - N-(N+1) branch WITH ids (token `1-2`, matches no real id): 21 - ops/mutate autopsy fallback placeallow plan and
    all 17 services/api/test/mutate *Mutants.mjs (asn assert attest closures config crossing isochrone ledger loop
    plan quota region siwa telemetry tier trip vehicle). First two ids e.g. tier: `tier-case-sensitive`,
    `tier-any-token-read`.
  - N-(N+1) branch with NO ids (no --only, refusal lists none): 15 - budget extractadapter gates geometry guidance
    handoff hazards menu normalise retrace roadtrip routescore scenic_tags segmentscore surfacecoverage.
- 2026-10-09T23:43:50Z RULINGS (before code):
  - R1 Brief vs reality - E-ids: the Brief's rule ("when a driver has no two all-digit ids, also probe
    `<id0>-<id1>`") never fires on plansheet (55 digit ids), so an E-range expansion stays green under it. Ruled:
    the id population splits into two classes, all-digit and the rest. The digit class keeps its `A-B` of the two
    smallest. The non-digit class gets its own probe `<x0>-<x1>` from its first two listed ids, whatever the digit
    class holds - this is the Brief's name probe and the E-id probe in one rule.
  - R2 a class with ONE non-digit id (10 drivers, E1 only) probes `<x>-<x>`: a degenerate range whose halves are
    both real ids, which any `A-B` expansion selects. Not in the Brief; it costs ten runs and covers ten drivers.
  - R3 the Brief's "confirm no id equals or contains the token": consecutive pairs are tried in listed order until
    one forms a token no id equals or contains; a driver with non-digit ids where no pair does is a failure by
    name, never a silent skip (fail closed).
  - R4 the N-(N+1) probe is kept for every driver with no digit range (the Brief says "also"): 21 + 15 = 36.
  - R5 a literal NAME_RANGE_FLOOR = 38 (the measured count of drivers with a non-digit id): fewer name probes than
    that is printed by name; exit 2 if nothing else failed, else 1 with the floor line beside the driver lines.
  - R6 mutants (a) and (b) let a driver get past its selection and run. mjs drivers: services/api has no
    node_modules in this worktree, so their baseline refuses with 2 before any src/ write. Python drivers: their
    dirty check covers MUTATED_FILES + HARNESS, which does not include mutate_only.py, so they reach build(); a
    run killed at TIMEOUT_S is reported (KILLED) and anything it left is restored by `git checkout` of the named
    paths before the restore check. The red runs use the shipping command with its shipping timeout.
  - R7 PINS.yaml is not in touches and its P-PROC-06 assertion already runs ops/lib/check-mutate-only.py; it is
    not edited. mutate_only.py and onlyIds.mjs are touched only by the mutants, and end byte-identical to HEAD.
