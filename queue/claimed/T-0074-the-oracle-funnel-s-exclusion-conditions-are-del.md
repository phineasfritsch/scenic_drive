---
id: T-0074
title: the oracle funnel's exclusion conditions are deletable with the ETL suite green
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:03:32Z
lease_expires_at: 2026-09-08T06:03:32Z
worktree: wt/T-0069
branch: task/T-0069
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
- 2026-09-08T02:03:32Z claimed by agent/claude-opus-5; lease until 2026-09-08T06:03:32Z
- 2026-09-08 agent/claude-opus-5 fixed by giving every exclusion in the funnel a negative case driven
  through `build()`, and by building two KMZs over a megabyte so the provenance path is exercised at a size
  where a partial read differs from a whole-file read. `services/etl/tests/test_oracle_build.py` only; no
  production code changed, because none of the seven mutations was a bug in `oracle.py` or `oracle_select.py`
  - they were seven properties nothing asserted. 6 tests -> 15 (9 new cases); suite 177 -> 186.

### Harness

Both scratch drivers are in the gitignored `services/etl/work/`: `mutate.py` (the seven from the brief) and
`adjacent.py` (the neighbouring routes). Each applies its edit, runs the whole suite from `services/etl`,
restores the file and asserts `git diff --quiet -- etl` before printing. Every run below ends
`REVERTED, tree clean`, and `git status --short` after all of them shows one modified path.

Baseline, host CPython 3.10.11 / pytest 9.1.1, `cd services/etl`:

```
$ python -m pytest
........................................................................ [ 40%]
........................................................................ [ 81%]
.................................                                        [100%]
177 passed in 4.59s
```

### RED - the seven routes, against round one's six tests

```
$ for m in M1-near-tagged-node M2-same-geometry M3-single-way-collections M4-kml-geometry \
           M5-both-single-way-gates M6-size-gated-refusal M7-partial-read-sha256; do
      python work/mutate.py "$m"; done
--- M1-near-tagged-node APPLIED to oracle_select.py ---
177 passed in 4.66s
--- pytest exit 0 ---
REVERTED, tree clean
--- M2-same-geometry APPLIED to oracle_select.py ---
177 passed in 4.72s
--- pytest exit 0 ---
REVERTED, tree clean
--- M3-single-way-collections APPLIED to oracle.py ---
177 passed in 4.79s
--- pytest exit 0 ---
REVERTED, tree clean
--- M4-kml-geometry APPLIED to oracle.py ---
177 passed in 4.71s
--- pytest exit 0 ---
REVERTED, tree clean
--- M5-both-single-way-gates APPLIED to oracle.py ---
177 passed in 4.89s
--- pytest exit 0 ---
REVERTED, tree clean
--- M6-size-gated-refusal APPLIED to oracle_select.py ---
177 passed in 4.91s
--- pytest exit 0 ---
REVERTED, tree clean
--- M7-partial-read-sha256 APPLIED to oracle_select.py ---
177 passed in 4.98s
--- pytest exit 0 ---
REVERTED, tree clean
```

Seven for seven, exit 0, nothing red - the brief's finding reproduced exactly. The mutations are the
brief's, verbatim, with one deliberate difference: deleting `kml_geometry`'s `if len(rows) != 1: continue`
outright makes `rows[0]` raise on a rowless Placemark, so M4/M5 substitute `if not rows: continue` there.
That is the honest form of the mutation - it removes the single-way gate and nothing else.

### GREEN - the same seven, against the corrected tests

```
$ for m in M1-near-tagged-node M2-same-geometry M3-single-way-collections M4-kml-geometry; do
      python work/mutate.py "$m"; done
--- M1-near-tagged-node APPLIED to oracle_select.py ---
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_a_tagged_node_inside_the_squash_radius_excludes_the_way
1 failed, 185 passed in 5.27s
--- pytest exit 1 ---
REVERTED, tree clean
--- M2-same-geometry APPLIED to oracle_select.py ---
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_geometry_that_is_not_the_kmls_is_excluded[coords0-a vertex ~11 m from the KML's]
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_geometry_that_is_not_the_kmls_is_excluded[coords1-the KML's vertices plus a fourth]
2 failed, 184 passed in 5.01s
--- pytest exit 1 ---
REVERTED, tree clean
--- M3-single-way-collections APPLIED to oracle.py ---
FAILED tests/test_oracle_build.py::TestOnlySingleWayCollectionsAreComparable::test_a_two_way_placemark_reaches_neither_the_index_nor_the_geometry
FAILED tests/test_oracle_build.py::TestOnlySingleWayCollectionsAreComparable::test_build_writes_no_way_from_a_two_way_collection
2 failed, 184 passed in 5.23s
--- pytest exit 1 ---
REVERTED, tree clean
--- M4-kml-geometry APPLIED to oracle.py ---
FAILED tests/test_oracle_build.py::TestOnlySingleWayCollectionsAreComparable::test_a_two_way_placemark_reaches_neither_the_index_nor_the_geometry
1 failed, 185 passed in 5.43s
--- pytest exit 1 ---
REVERTED, tree clean

$ for m in M5-both-single-way-gates M6-size-gated-refusal M7-partial-read-sha256; do
      python work/mutate.py "$m"; done
--- M5-both-single-way-gates APPLIED to oracle.py ---
FAILED tests/test_oracle_build.py::TestOnlySingleWayCollectionsAreComparable::test_a_two_way_placemark_reaches_neither_the_index_nor_the_geometry
FAILED tests/test_oracle_build.py::TestOnlySingleWayCollectionsAreComparable::test_build_writes_no_way_from_a_two_way_collection
2 failed, 184 passed in 5.52s
--- pytest exit 1 ---
REVERTED, tree clean
--- M6-size-gated-refusal APPLIED to oracle_select.py ---
FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_fires_at_the_size_of_the_file_it_protects
1 failed, 185 passed in 4.90s
--- pytest exit 1 ---
REVERTED, tree clean
--- M7-partial-read-sha256 APPLIED to oracle_select.py ---
FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_two_large_kmzs_sharing_a_first_block_still_get_different_digests
FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_fires_at_the_size_of_the_file_it_protects
2 failed, 184 passed in 4.79s
--- pytest exit 1 ---
REVERTED, tree clean
```

M4 alone fails only the direct assertion, and that is the point the brief made: with `single_way_collections`
still filtering, `published` is empty, so `build()` writes nothing either way and NO test driven only through
`build()` can see that copy at all. It needs its own named assertion, which is why
`test_a_two_way_placemark_reaches_neither_the_index_nor_the_geometry` asserts `single_way_collections(kmz)`
and `kml_geometry(kmz)` separately rather than together.

M5 is the one that does concrete damage, and the failure states it in numbers rather than in prose:

```
$ python -m pytest -x tests/test_oracle_build.py::TestOnlySingleWayCollectionsAreComparable::test_build_writes_no_way_from_a_two_way_collection   # both gates removed
        n, stages = sel.build(fixture, export, kmz)
>       assert (n, stages["single_way"]) == (0, 0)
E       assert (1, 1) == (0, 0)
E         At index 0 diff: 1 != 0
tests\test_oracle_build.py:235: AssertionError
1 failed in 0.19s
```

One way written, from a Placemark holding two - carrying geometry and a curvature computed over both ways
joined end to end. That is the comparison condition 1 exists to refuse.

### The adjacent routes, since round one's whole lesson was that they are what survives

Each of these reaches the same effect as one of the seven by a different field, scale or entry point. Six
probes, in `work/adjacent.py`, applied and reverted the same way:

```
$ for p in A1-squash-radius-to-zero A2-drop-node-features-in-load-export A3-geometry-tolerance-to-1km \
           A4-drop-length-check-in-same-geometry A5-refusal-inverted-to-large-files-only \
           A6-sha256-single-whole-file-read; do python work/adjacent.py "$p"; done
--- A1-squash-radius-to-zero APPLIED ---
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_a_tagged_node_inside_the_squash_radius_excludes_the_way
FAILED tests/test_oracle_select.py::test_the_selection_constants_are_pinned_against_literals
FAILED tests/test_oracle_select.py::test_a_tagged_node_within_thirty_metres_excludes_the_way
FAILED tests/test_oracle_select.py::test_the_thirty_metre_radius_is_a_circle_and_not_an_ellipse
FAILED tests/test_oracle_select.py::test_the_proximity_grid_finds_a_node_across_a_cell_boundary
5 failed, 181 passed in 5.15s
--- A2-drop-node-features-in-load-export APPLIED ---
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_a_tagged_node_inside_the_squash_radius_excludes_the_way
FAILED tests/test_oracle_select.py::test_load_export_collects_only_nodes_carrying_a_squash_tag
2 failed, 184 passed in 5.19s
--- A3-geometry-tolerance-to-1km APPLIED ---
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_geometry_that_is_not_the_kmls_is_excluded[coords0-a vertex ~11 m from the KML's]
FAILED tests/test_oracle_select.py::test_the_selection_constants_are_pinned_against_literals
FAILED tests/test_oracle_select.py::test_geometry_differing_by_more_than_a_metre_is_a_different_road
3 failed, 183 passed in 5.24s
--- A4-drop-length-check-in-same-geometry APPLIED ---
FAILED tests/test_oracle_build.py::TestTheFunnelExcludesRatherThanCopies::test_geometry_that_is_not_the_kmls_is_excluded[coords1-the KML's vertices plus a fourth]
FAILED tests/test_oracle_select.py::test_a_way_with_a_different_node_count_is_never_the_same_geometry
2 failed, 184 passed in 5.05s
--- A5-refusal-inverted-to-large-files-only APPLIED ---
FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_it_raises_and_names_both_digests
FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_is_keyed_on_the_basename_not_on_the_path
2 failed, 184 passed in 5.25s
--- A6-sha256-single-whole-file-read APPLIED ---
186 passed in 5.14s
--- pytest exit 0 ---
```

A1-A5 red. A6 green **and correctly so**: `fh.read()` with no argument returns the whole file, so it is a
refactor with the same output, not an evasion. Recorded rather than dropped, because "the mutation stayed
green" is only a finding when the mutation changes behaviour, and asserting otherwise would be exactly the
overstatement this task exists to correct.

Two things the adjacent sweep says about the fix. First, the size guard is now covered in BOTH directions:
`< (1 << 20)` (M6) is caught by the new megabyte-scale refusal, `> (1 << 20)` (A5) by the two existing
byte-scale ones, so narrowing the refusal to either side of the threshold is red. Second, A1-A4 also trip
`test_oracle_select.py`, which had unit tests for `near_tagged_node`, `same_geometry` and the constants all
along - the gap was never that the predicates were untested, it was that `eligible()` was reached with an
input where each predicate could only answer one way. Two of these mutations are therefore double-covered
now, and the new tests are the only cover for M1-M7.

### Deliberately NOT done

- FINDING 3 (the two co-editable literals in `inputs/manifest.yaml` and the committed fixture) is out of
  scope per the brief, and no test here touches it. It still stands open.
- `test_renaming_the_kmz_walks_straight_past_the_refusal` still documents the rename hole rather than
  closing it. Unchanged from round one; closing it is a production change, not a test change.
- The file is now exactly 300 lines - at the cap, not over it (`ops/lib/check-line-cap` fails at `-gt 300`).
  The first draft came out at 340; it was brought down by compressing docstring prose, NOT by dropping
  assertions and NOT by splitting the file, which would have meant either duplicating the KMZ/export
  builders or declaring a path outside this task's `touches:`. Every assertion in the 340-line draft is in
  the 300-line file. This is the ceiling: the next test added here needs a second module and a `touches:`
  that says so.

### Gates, in wt/T-0069

```
$ cd services/etl && python -m pytest        # 177 before, 186 after
186 passed in 4.99s
$ bash ops/queue-check
QUEUE OK (70 tasks)
$ bash ops/check-pins
PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
$ bash ops/check-pins --source-only
PINS ok=3 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
$ bash ops/test
TESTS linux=236/76 ios=skipped failed=0 skipped=0
OK
```

`ops/test` runs the ETL tier and the Swift/linux tier together (236 = 186 pytest + the SPM and vitest
suites). `ios=skipped` is the host, not the change: this is the Windows box, there is no Xcode here, so the
iOS tier has NOT been run for this branch and someone on a Mac still has to. Nothing in this task touches
Swift.
