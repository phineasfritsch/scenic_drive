---
id: T-0074
title: the oracle funnel's exclusion conditions are deletable with the ETL suite green
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/tests/test_oracle_build.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Follow-up to [[T-0069]], which added `services/etl/tests/test_oracle_build.py` — six tests that finally call
`oracle_select.build()` instead of comparing two committed literals. A second agent executed twelve evasions
against it. **Five went red, seven did not**, every one with the suite green at `177 passed`. Full report in
T-0069's `## Log`.

**What the fix genuinely achieved, and it is real:** both halves named in T-0069's title are now
mutation-covered. Restoring the hardcoded digest gives `3 failed / 174 passed`; `if False:` gives
`2 failed / 175 passed`. The verifier also tried the three standard dodges around those two mutations —
emptying the population (`published = {}`), typing the pin lookup so it silently misses (`kmz.name` ->
`kmz.stem`), and nulling an operand (`want = digest`) — and the guard caught all three. **The place this repo
usually fails, the fixer got right:** the test's `sha256_of()` is its own `hashlib` call, not `sel._sha256`,
so the two sides of the comparison do not come from the same code.

**FINDING 1 — the funnel claim is over-stated.** `test_build_runs_the_funnel_rather_than_copying_the_kmz`
claims `build()` runs the funnel, but exercises exactly ONE negative path: a `junction=roundabout` way. Every
other exclusion in `eligible()` deletes green:

- delete `or near_tagged_node(ours, grid)` — the test's export carries zero node features, so the grid is
  always empty and the call is a no-op in the only test that reaches it. Probe: a way with a
  `highway=traffic_signals` node 10 m away goes from excluded to written into the fixture. `177 passed`.
- delete `if not same_geometry(ours, theirs): continue` while leaving the counter the test asserts on. That
  is the condition the module says excludes 726 of 3297 ways which agree only 29.6% of the time. `177 passed`.
- delete BOTH copies of `if len(rows) != 1: continue` (`etl/oracle.py:single_way_collections` and
  `kml_geometry`). Probe: a two-way collection's first way lands in the fixture carrying a collection-level
  curvature value — which is the entire justification for the oracle being comparable at all. `177 passed`.
  Deleting only the first copy is green but corrupts just the counter; the second copy is what stops the way
  reaching `ways`. Measured, not assumed.

No test references `single_way_collections`, `oracle.collections` or `kml_geometry` by name.

**FINDING 2 — the guard runs only at synthetic scale.** Every KMZ the tests build is a few hundred bytes in
`tmp_path`; the real `inputs/vermont-curvature.kmz` is 2 557 952 bytes.

- `if want and digest != want and kmz.stat().st_size < (1 << 20):` — a 2.5 MB KMZ with the pinned basename and
  a non-matching digest goes from REFUSED to ACCEPTED, one way written. **The refusal is dead for the only
  file it exists to protect.** `177 passed`.
- collapse `_sha256`'s streaming loop to a single `fh.read(1 << 20)` — two different 2.5 MB files sharing
  their first megabyte hash to the same value, and neither digest is the file's, while
  `test_the_digest_moves_when_the_bytes_move` — the test written for exactly that property — stays green.
  `177 passed`.

**The correction is narrow and belongs on `task/T-0069`:** give the funnel test an export containing a tagged
node, a case where geometry differs by more than `GEOMETRY_TOL_M`, and a KMZ with a two-way Placemark, so each
condition has a negative case driven through `build()`; and build one KMZ larger than 1 MB in the refusal test
so the digest path is exercised at a size where a partial read differs from a whole-file read. Neither needs
the 2.5 MB oracle or osmium, so both keep the "runs everywhere the suite runs" property.

**FINDING 3 is separate and is NOT a defect in this fix** — filed here only so it is not lost. The provenance
chain is still two co-editable literals one level out: rewriting `inputs/manifest.yaml`'s `sha256:` AND
`tests/fixtures/curvature_oracle.json`'s `source_sha256` to the same fabricated value leaves `177 passed`.
Round 5 replaced "one hand-editable field compared with itself" with "two hand-editable fields compared with
each other". Nothing in the suite can close it, because the real oracle is gitignored and a pytest suite
cannot hash a file that is not in the tree. The containment is `ops/etl-fetch-inputs` failing at fetch time,
which is outside `ops/test`. **File that as its own task against `ops/sane` or the fetch path; do not attempt
it here.**

- Demonstrate each deletion red then green.
- The verifier ran the ETL tier only. Re-run the Swift tiers before signing anything off.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the adversarial verification of T-0069. Every mutation above
  was executed and reverted; the verifier's tree ended clean.
