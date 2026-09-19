---
id: T-0176
title: ops/mutate/geometry - a committed mutation population with a floor for the ETL geometry terms (sinuosity.py, proximity.py); EQUIVALENT rulings carry a witness
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T01:59:25Z
lease_expires_at: 2026-09-19T09:59:25Z
worktree: .worktrees/T-0176
branch: task/T-0176
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
- 2026-09-19T01:59:25Z claimed by agent/claude-opus-5; lease until 2026-09-19T09:59:25Z
- 2026-09-19T02:14Z RULINGS FIRST, before any code, on every disagreement between CLAUDE.md, the Brief, the
  acceptance block and what is in the tree (author rule):
  1. FIVE CLASSES OR SIX. The `acceptance:` block names five classes; the Log entry above adds a sixth
     (banded / diagonal-window) from agent/rv4-pr94's PASS entry. Read as a FLOOR, not a ceiling:
     `REQUIRED_CLASSES` carries six and every one of them must be populated. A population that satisfies
     the acceptance block's five and is empty on the sixth is exactly the state PR #94 was in four times.
  2. NO EXEC BIT. CLAUDE.md says new scripts under `ops/` must be committed executable; every
     `ops/mutate/*.py` is 100644 and `ops/lib/check-exec-bits` classifies `.py` under `ops/` as data,
     because every call site invokes it as an argument to an interpreter. `git update-index --chmod=+x`
     is therefore NOT run here; the five new files are staged 100644 and quoted below.
  3. NO RESTORE, SO NO SLEEP. The harness framing carries budget.py's protocol - mutate, run, restore,
     sleep 1.1 s before the restore so a .pyc is not keyed on a stale mtime. budget.py must write into
     `Sources/` because `swift test` builds the package in place; pytest does not, so this runner copies
     `services/etl` into the gitignored `.build-mutate-geometry/` and mutates the COPY. There is no
     restore step to race with and `git status` over services/etl is untouched by a full sweep. What the
     sleep was for is real and stays: CPython keys a .pyc on mtime+size at one-second granularity, so
     `purge_pycache` removes every `__pycache__` under the copy before EVERY pytest run. A purge does not
     depend on a clock; a sleep does.
  4. THE SPLIT. The runner passed the 300-line cap at 313 lines. Split along budget.py's boundary of
     meaning rather than at a line number: `geometry_tree.py` is what the run does to the filesystem (copy,
     mutant, purge, pytest, probe), exactly as `budget_tree.py` is for budget.py. Four files plus the
     probe, all under the cap; counts quoted in the acceptance block.
  5. THE SIXTH CLASS NEEDS A FIXTURE, NOT ONLY AN ENTRY. rv4-pr94's window keeps the first and last
     segments AND the interior-interior pairs, so no case in either fixture could see it: the
     interior-interior case's minimum sits at (1,1) and (2,1), on the diagonal and one cell off it. The
     new case is a seven-node way against a ONE-SEGMENT motorway stub, so `j` is 0 throughout and the band
     can select nothing but `i`; the minimum is at (3,0), three cells off the diagonal. Added to
     `geometry_bends_fixture.json`, which subjects it to that file's `TestFixtureShape` collinearity guard
     - satisfied: its node n3 stands 0.0109 x 110540 = 1204.8860 m off its own chord.
  6. THE WITNESS IS COMPUTED, NOT WRITTEN DOWN. CLAUDE.md: an equivalent-mutant ruling is an EQUIVALENT
     entry with a witness, never prose. `budget_arms.py` states its witnesses as prose about a sweep
     nobody can re-run. Here `geometry_probe.py` IS the sweep: the runner digests every answer
     `sinuosity` and `proximity` give over every fixture case, pristine and mutated, and an entry passes
     only on a byte-identical digest AND no named test red. Round 3's retracted ruling is the worked
     NON-example and `--non-example` refutes it on demand, quoted below.
  7. TEST_FILES IS THE SIX GEOMETRY SUITES, not the whole ETL suite. A mutation killed by, say,
     `test_score_contract.py` would be killed by a neighbour tripping over the same edit rather than by
     the check its label claims exists. The run requires the NAMED killers to go red and reports
     `CAUGHT, BUT NOT BY THE TEST THAT NAMES IT` otherwise - which is how finding 8 below was found.
  8. A KILLER THE FIRST RUN FALSIFIED. The chord-for-path entry for `tunnel_meters` named
     `test_a_multi_segment_tunnel_is_measured_end_to_end` as one of its killers. That test's bore is one
     of the three `COLLINEAR_BY_DESIGN` geometries - drawn on one meridian - so its path and its chord are
     the same number and it stayed GREEN under the mutant. The killer is removed, with the reason written
     next to the entry. It remains a correct killer for the segment-subset `snap.length_m` mutation, where
     it does go red.
  9. PIN ID. `P-PROC-05` is free on origin/main and on every one of the 30 open PR heads (each head's
     `pins/PINS.yaml` fetched and grepped; the union is P-ATTR-02, P-COST-02, P-DATA-02, P-GIT-01..04,
     P-HUMAN-01, P-OPS-01..03, P-OPS-05, P-OPS-06, P-PROC-01..04, P-PROD-01, P-ROUTE-01, P-SAFE-03,
     P-SAFE-05, P-SAFE-06, P-SEC-01, P-SRC-01, P-SRC-02, P-TEST-01, P-TEST-02). `anchor: process`,
     `runs_on: [linux]`, P-GIT-02's interpreter style, and the assertion is `--prove-floor`, which costs
     no pytest run - the full sweep is 17 of them and does not belong in a per-push gate.
- 2026-09-19T02:41Z RED BY NAME, FIRST. Every check here was seen red before it was seen green.
  (a) THE SIXTH CLASS, with its fixture case present and the entry in the population but its two killers
  not yet written - `python ops/mutate/geometry.py`, exit 1:

        banded-subset      keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class
            exit=1   1 red  fingerprint b20c733880da77b5 (differs)  named red: []
            NAMED TEST DID NOT GO RED: ['test_the_minimum_can_sit_far_off_the_diagonal_of_the_segment_pair_matrix', 'test_the_banded_window_answers_inf_where_the_whole_matrix_answers_99_metres']
            (red instead: ['test_the_metres_to_the_nearest_motorway_match_the_fixture[minimum_far_off_the_diagonal_of_the_segment_pair_matrix]'])

        POPULATION 12 mutations over 6 classes (floor 12), 4 equivalent (floor 4)
        CAUGHT, BUT NOT BY THE TEST THAT NAMES IT:
            tunnel_meters measures the bore's chord, not its path
            keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class

  The same run is what falsified the tunnel killer (ruling 8): five tests red, and
  `test_a_multi_segment_tunnel_is_measured_end_to_end` not among them.
  (b) THE RUNNER REFUSES WHEN A CLASS IS MISSING - the banded entry deleted from `geometry_mutations.py`,
  `python ops/mutate/geometry.py`, exit 2, no pytest run at all:

        POPULATION FLOOR: MUTATIONS has 11, floor is 12. A shrunken population must never read as a clean sheet.
        POPULATION FLOOR: no mutation left in class 'banded-subset' - that whole axis is unmeasured. A shrunken population must never read as a clean sheet.

  (c) THE PIN'S OWN ASSERTION, red in the same state - `python ops/mutate/geometry.py --prove-floor`, exit 1:

        FLOOR PROOF FAILED: emptied -> refused=True, one deleted -> refused=True, class 'banded-subset' deleted -> refused=True, real -> accepted=False

  (d) THE CLASS ARM REFUSES WHAT THE COUNT ARM CANNOT, on the restored population: `--prove-floor` trades
  the last class for copies of a surviving one, leaving the count AT the floor, and it still refuses -
  `with class 'banded-subset' traded for copies of 'segment-subset', population still 12:` followed by the
  same `no mutation left in class` line. That arm is the whole reason a count is not enough here.
  (e) The two new tests then pass on the pristine module (`python -m pytest tests/test_proximity_banded.py
  -q` -> `4 passed`), and the banded mutant is killed by the two tests that name it - the green table is in
  the acceptance block below.
- 2026-09-19T03:30Z ACCEPTANCE, RE-RUN AND RE-QUOTED AT THE FINAL COMMIT. Every gate below ran bare on the
  tree of this commit; the only file edited after them is this task file.
  A1 - the runner, the populations, the modes, the six classes, the literal floors, red then green.
  `git ls-files -s ops/mutate/geometry*.py`:

        100644 a84a3951e278960e5b83c1baa033c3c4523cd4da 0	ops/mutate/geometry.py
        100644 409b7c5889cdb5cba70b7b67bd54708bc24ad041 0	ops/mutate/geometry_arms.py
        100644 dceae10f0aa21cd689b2194aaf8c94a85112bd6e 0	ops/mutate/geometry_mutations.py
        100644 6798ee70fb9716d83fee339dfa741a26b533493c 0	ops/mutate/geometry_probe.py
        100644 17532ae4aed1c9de1599dac394c735789439a225 0	ops/mutate/geometry_tree.py

  `wc -l`: geometry.py 237, geometry_arms.py 75, geometry_mutations.py 145, geometry_probe.py 88,
  geometry_tree.py 110, services/etl/tests/test_proximity_banded.py 190 - every file under the 300-line
  cap. MIN_MUTATIONS = 12 and MIN_EQUIVALENT = 4 are literals and the exact lengths of the two lists;
  REQUIRED_CLASSES is six literal names, one more than the acceptance block asks for (ruling 1). The
  refusal when a class is missing is quoted red at (b) above and green at A3.
  A2 - every EQUIVALENT entry carries a reason and a COMPUTED witness, and round 3 is the NON-example.
  The four entries go MISSED with the pristine digest (A3's table); `python ops/mutate/geometry.py
  --non-example`, exit 0:

        THE NON-EXAMPLE: round 3: drop the pairs interior to both polylines - 'equivalent in the plane'
          etl/proximity.py
          pristine digest e92225a056e1d2b1 over 175 values
          mutant   digest 942bdff5a54b8a84 over 175 values
          pristine  ...:nearest_approach_interior_to_both_polylines meters_to_nearest_motorway   99.48600000003353
          mutant    ...:nearest_approach_interior_to_both_polylines meters_to_nearest_motorway   406.4842081198996
          2 of 175 fingerprint values differ; 3 named test(s) red
            RED  test_the_metres_to_the_nearest_motorway_match_the_fixture[nearest_approach_interior_to_both_polylines]
            RED  test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines
            RED  test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold
        NON-EXAMPLE OK: the round-3 ruling is REFUTED by this arm's own test - it is a
          mutation (interior-interior class), not an equivalent mutant.

  A3 - the table, and the pin. `python ops/mutate/geometry.py`, exit 0, whole output:

        BASELINE  6 test files, pytest exit=0, 0 failed; fingerprint e92225a056e1d2b1 over 175 values

        MUTATIONS - each must be killed BY THE TEST THAT NAMES IT
        segment-subset     line_distance_m walks only the WAY's first segment
            exit=1  10 red  fingerprint f11747994489634e (differs)  named red: ['test_the_nearest_approach_may_be_on_a_later_segment_of_the_way', 'test_the_way_may_bend_toward_the_motorway_between_its_end_nodes']
        segment-subset     line_distance_m walks only the WAY's last segment
            exit=1   8 red  fingerprint da046cd05fdda916 (differs)  named red: ['test_the_way_may_bend_toward_the_motorway_between_its_end_nodes']
        segment-subset     snap.length_m drops the way's LAST segment (every-but-last)
            exit=1  38 red  fingerprint 5d4d8d12ea91e7eb (differs)  named red: ['test_a_multi_segment_tunnel_is_measured_end_to_end', 'test_the_sinuosity_matches_the_fixture']
        chord-for-path     tunnel_meters measures the bore's chord, not its path
            exit=1   5 red  fingerprint ff7eb02d94054031 (differs)  named red: ['test_the_bore_measures_its_path_and_not_its_chord', 'test_a_bent_bore_crosses_the_threshold_only_along_its_path']
        chord-for-path     the CANDIDATE motorway is reduced to its chord before it is measured
            exit=1   4 red  fingerprint 0ac8881abc28374f (differs)  named red: ['test_the_metres_to_the_nearest_motorway_match_the_fixture']
        chord-for-path     way_sinuosity's NUMERATOR becomes the chord, so every way reads 1.0
            exit=1   7 red  fingerprint 344128369921058e (differs)  named red: ['test_the_sinuosity_matches_the_fixture', 'test_the_term_is_raw_and_unbounded_not_a_0_to_1_score']
        candidate-order    the LAST candidate wins instead of the nearest one
            exit=1   2 red  fingerprint 5bf165e53bbf3e6d (differs)  named red: ['test_the_candidate_order_cannot_change_the_answer']
        candidate-order    the reporting radius becomes exclusive - a tie at the radius reads inf
            exit=1   1 red  fingerprint e92225a056e1d2b1 (IDENTICAL)  named red: ['test_the_radius_is_inclusive']
        interior-interior  drop the pairs interior to BOTH lines - round 3's retracted 'equivalent'
            exit=1   3 red  fingerprint 942bdff5a54b8a84 (differs)  named red: ['test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines', 'test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold']
        earth-model        metres per degree of latitude becomes the equatorial 111234.7
            exit=1  13 red  fingerprint c2ebe6b71d1384bf (differs)  named red: ['test_the_way_may_bend_toward_the_motorway_between_its_end_nodes', 'test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines']
        earth-model        is_tunnel consults the allowlist without stripping or lowercasing
            exit=1   2 red  fingerprint 73bde87b4ada37f0 (differs)  named red: ['test_the_tunnel_metres_match_the_fixture', 'test_is_tunnel_agrees_with_the_metres']
        banded-subset      keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class
            exit=1   3 red  fingerprint b20c733880da77b5 (differs)  named red: ['test_the_minimum_can_sit_far_off_the_diagonal_of_the_segment_pair_matrix', 'test_the_banded_window_answers_inf_where_the_whole_matrix_answers_99_metres']

        EQUIVALENT - must go MISSED, with a digest identical to the pristine one
        equivalent         measure the candidate against the way instead of the way against the candidate
            exit=0   0 red  fingerprint e92225a056e1d2b1 over 175 values (IDENTICAL)
        equivalent         snap.length_m pairs the coordinates with an explicit slice instead of relying on zip
            exit=0   0 red  fingerprint e92225a056e1d2b1 over 175 values (IDENTICAL)
        equivalent         the candidate distance is the first argument of min rather than the second
            exit=0   0 red  fingerprint e92225a056e1d2b1 over 175 values (IDENTICAL)
        equivalent         _crosses tests the degeneracies before the sides rather than after
            exit=0   0 red  fingerprint e92225a056e1d2b1 over 175 values (IDENTICAL)

        POPULATION 12 mutations over 6 classes (floor 12), 4 equivalent (floor 4)
        every one of the 12 mutations was killed by the test that names it, and every one of
        the 4 equivalent mutants went MISSED with a byte-identical fingerprint

  The pin is P-PROC-05, `anchor: process`, `runs_on: [linux]`, P-GIT-02's interpreter style, assertion
  `"${PYTHON:-$(command -v python3 || command -v python)}" ops/mutate/geometry.py --prove-floor`; it parses
  (26 ids, all unique) and passes through check-pins' own runner, and is quoted red at (c) above.
  THE REST OF THE BATTERY, bare, on the same tree:
  * `cd services/etl && python -m pytest tests -rs` -> `976 passed in 126.06s (0:02:06)`, exit 0, zero
    skips (`grep -c SKIPPED` -> 0). 972 before this branch, plus the four in test_proximity_banded.py.
  * `bash ops/check-pins --source-only` -> `PINS ok=11 skipped=14 pending=1 expired=0 failed=0 tier=linux
    source-only`, exit 0 (P-PROC-05 is anchor: process, so --source-only skips it by design).
  * `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8),
    none over 300 lines`, exit 0.
  * `bash ops/lib/check-exec-bits` -> `P-OPS-01: 67 files, 23 required present, all modes correct`, exit 0.
  * `bash ops/queue-check` -> `QUEUE OK (175 tasks)`, exit 0.
- 2026-09-19T03:35Z STILL OPEN, and none of it is claimed as done.
  1. THE WITNESS POPULATION HAS A HOLE AND THE TABLE SHOWS IT: the `radius becomes exclusive` mutation
     prints `fingerprint e92225a056e1d2b1 (IDENTICAL)`. No fixture case sits exactly at
     MOTORWAY_SEARCH_RADIUS_M, so the probe cannot see that edit at all; it is caught by
     `test_the_radius_is_inclusive`, which supplies its own radius. The consequence is for the EQUIVALENT
     arm, not for this mutation: a false equivalence claim that is wrong ONLY at the reporting boundary
     would pass its witness today. A fixture case at exactly the radius would close it.
  2. NOTHING RUNS THE FULL SWEEP ON A SCHEDULE. P-PROC-05 asserts `--prove-floor`, which costs no pytest
     run; the 17-run sweep is run by hand, here and by the reviewer. T-0184 (CI runs every --prove-red
     table) is where that changes, and this harness is one more table for it.
  3. `test_the_metres_to_the_nearest_motorway_match_the_fixture` exists in BOTH test_proximity.py and
     test_proximity_bends.py, and `red_by_name` matches on the bare name, so either file's copy satisfies
     that killer. Recorded rather than renamed: renaming a test in a file this task does not own is a
     bigger edit than the ambiguity is worth, and every other killer name is unique across TEST_FILES.
  4. The probe measures `sinuosity` and `proximity` over `geometry_*.json` only. It never calls
     `score.score`, so every product cost in this population - the x0.7, the 1/0.7 - is argued from
     score.py's constants and the fixture's metres, not measured end to end. Nothing under `etl/` imports
     proximity.py yet; T-0168 is what makes that measurable.
  5. `snap.py` is a subject of this harness (two mutations, one equivalent) and `tests/test_snap.py` is in
     TEST_FILES, but snap.py has no class of its own in REQUIRED_CLASSES: its mutations sit in
     segment-subset and earth-model, which are about the matrix, not about overlap. If T-0161's successor
     grows snap.py, that is a seventh class and not a thirteenth entry.
- 2026-09-19T04:05Z PR #107 opened on 5eb3df6 (`gh pr checks 107` -> `no checks reported on the
  'task/T-0176' branch`), and GitHub reported it CONFLICTING: origin/main had moved four commits past the
  29f2a06 this worktree branched from. ONE conflict, textual and positional - main's P-PROD-05 (T-0173,
  PR #103) and this branch's P-PROC-05 were both appended at the tail of pins/PINS.yaml. Merged
  origin/main (dcaf3bd) in rather than leaving the reviewer a branch that cannot be merged; resolved by
  keeping BOTH pins, and the ids are still unique (27 parsed, no duplicate). P-PROC-05 is still free on
  the new main - P-PROD-05 is a different id.
  RE-MEASURED, because the merge touches services/etl (T-0173 landed surface.py, terms.py, schema.py,
  contentdigest.py and two suites there) and pins/PINS.yaml, and a correction commit that touches a
  measured file re-measures it:
  * `python ops/mutate/geometry.py` -> exit 0, the same table, baseline fingerprint UNCHANGED
    (`e92225a056e1d2b1 over 175 values`) - T-0173's work does not touch the three subjects or the
    geometry fixtures - and the same closing two lines: *every one of the 12 mutations was killed by the
    test that names it, and every one of the 4 equivalent mutants went MISSED with a byte-identical
    fingerprint*.
  * `cd services/etl && python -m pytest tests -rs` -> `1040 passed in 79.94s (0:01:19)`, exit 0, zero
    skips. 976 at 5eb3df6; the 64 new tests are main's, not this branch's.
  * `bash ops/check-pins --source-only` -> `PINS ok=12 skipped=14 pending=1 expired=0 failed=0
    tier=linux source-only`, exit 0. ok went 11 -> 12 because main's P-PROD-05 is `anchor: source` and
    now runs; skipped is unchanged at 14, which is where P-PROC-05 sits (`anchor: process`).
  * `bash ops/lib/check-line-cap` -> `71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none
    over 300 lines`; `bash ops/lib/check-exec-bits` -> `68 files, 23 required present, all modes
    correct` (67 -> 68: main's ops/lib/check-schema-version.py); `bash ops/queue-check` -> `QUEUE OK
    (182 tasks)` (175 -> 182: main's seven new task files).
  * `wc -l` unchanged: geometry.py 237, geometry_arms.py 75, geometry_mutations.py 145,
    geometry_probe.py 88, geometry_tree.py 110, test_proximity_banded.py 190.
