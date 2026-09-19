---
id: T-0176
title: ops/mutate/geometry - a committed mutation population with a floor for the ETL geometry terms (sinuosity.py, proximity.py); EQUIVALENT rulings carry a witness
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T01:59:25Z
lease_expires_at: 2026-09-19T09:59:25Z
worktree: .worktrees/T-0176
branch: task/T-0176
exclusive: []
touches: [ops/mutate/, services/etl/tests/, pins/PINS.yaml]
pins_affected: []
reviewer: agent/rv2-pr107
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
- 2026-09-19T04:22:09Z **Record corrections from the fable verification of this build (aa540a8), closed before review -
  agent/claude-fable-5-1 (orchestrator), for the owner. The verifier re-ran the runner (output identical line for
  line to the A3 table, baseline e92225a056e1d2b1 over 175 values), `--prove-floor` and `--non-example` (exit 0,
  the same digests), the class refusal on a gitignored copy (exit 2, no pytest, both FLOOR lines), the whole ETL
  suite (`1040 passed`, zero skips), the four bare gates, every `wc -l` and every mode; CI's core job runs the
  FULL `bash ops/check-pins` and passed, so P-PROC-05's assertion has run green in CI. Four items are text.**
  (a) "P-PROC-05 verified free on origin/main and on all 30 open PR heads" - the count is 35 (`gh pr list
  --state open --limit 100 --json number,headRefName` -> 35 rows); each head's pins/PINS.yaml fetched via `gh api`
  and grepped for `id: P-PROC-05` hits only PR #107; `git show origin/main:pins/PINS.yaml | grep -c P-PROC-05`
  -> 0. The substance holds; the Log quotes no command for the 30. (b) "26 ids, all unique" (A3) and "27 parsed,
  no duplicate" (merge entry) are correct at HEAD (`grep -E '^\s*-\s*id:' pins/PINS.yaml | wc -l` -> 27;
  `| sort | uniq -d | wc -l` -> 0) but neither count is backed by a quoted command. (c) "976 at 5eb3df6; the 64
  new tests are main's" - no command quoted; consistent with `git diff --stat 5eb3df6..HEAD -- services/etl/tests`
  (main's test_surface_state.py +118, test_corpus_schema.py +102, corpus_extract_split.json) and with this
  branch's only test addition against merge-base dcaf3bd being test_proximity_banded.py (4 tests); 976 was not
  re-measured. (d) "Four of the six new files existed as untracked work-in-progress in the worktree when I
  started" is not verifiable from the committed tree and is not load-bearing.
- 2026-09-19T04:40Z RULING ON THE BOUNDARY HOLE (STILL OPEN 1 of the 03:35Z list), BEFORE ANY CODE, on the
  two shapes offered for closing it: (A) a fixture case in `geometry_bends_fixture.json` whose nearest
  approach is EXACTLY `MOTORWAY_SEARCH_RADIUS_M`, or (B) a boundary probe in `geometry_probe.py` - for every
  proximity case, after the unbounded answer, ask `meters_to_nearest_motorway` again with that answer as
  `radius_m`, so the pristine tree reports the distance (`nearest <= radius_m` holds as an identity) and an
  exclusive mutant reports `inf`. THE RULING IS B, and it is not because A is impossible.
  IS AN EXACT 1000.0 REACHABLE IN FLOATING POINT? YES - measured before ruling, because "unreachable" would
  have been the convenient answer. `snap.point_to_segment_m` projects to metres FIRST (`px = p[1] * kx`), so
  at lon -118 the operands are ~1.09e7 m and the difference `px - ax` is quantised at ULP(1.09e7) =
  1.862645149230957e-09 m - ten thousand times coarser than ULP(1000.0) = 1.1368683772161603e-13 - which is
  why a whole BAND of coordinates lands on the boundary rather than a knife edge. A throwaway bisection over
  the doubles (in the gitignored `.build-mutate-geometry/`, not committed) found it: a way
  (34.00,-118.00)-(34.01,-118.00) against the same pair offset east by 0.010836228509198522 deg gives
  `line_distance_m` -> `1000.0` exactly; 8191 consecutive doubles of that offset give the same value; and it
  survives `cos(radians(34.005))` moved +-3 ULP (kx 92283.02994450173 through 92283.02994450182, distance
  1000.0 at every one). So A needs no tolerance and would not be faking one. It is still the wrong shape.
  WHY B, on four grounds, none of them "A is hard":
  1. COVERAGE. A exercises the reporting boundary at ONE value in ONE case. B exercises it on EVERY
     proximity case - 17 of them across both geometry fixtures, crossing pairs at 0.0 included - at that
     case's OWN answer. The hole named at 03:35Z is about the EQUIVALENT arm, and a false equivalence wrong
     only at the boundary can be wrong at any distance, not only at 1000.0.
  2. NO HAND-TUNED COORDINATE, which is what the fixture would have to carry. 0.010836228509198522 is a
     17-significant-digit literal found by bisecting the doubles; it is a fact about the rounding of this
     projection, not about geometry, while every other case in that file is a geometry with `workings`
     stating what it means. Its consumers compare with `abs=` tolerances, so no test in the suite could see
     the exactness - only the probe could.
  3. SILENT DECAY, which is this repository's signature defect. If that literal ever stopped landing exactly
     on the boundary - a different libm, a re-association of the arithmetic in `point_to_segment_m`, a
     projection constant moved - the table would go quietly back to `(IDENTICAL)` and no gate would go red.
     Under B nothing can silently un-exercise the boundary: the radius IS the answer, whatever the answer
     becomes, and the identity `x <= x` is not a property of any libm.
  4. THE BLINDNESS IS THE WITNESS'S, SO THE FIX BELONGS TO THE WITNESS. A would add a case to the fixture
     population - a record of geometry shared by four suites - to repair an instrument. B touches
     `ops/mutate/geometry_probe.py` and nothing else: no new fixture case, no new parametrised test id, no
     interaction with that file's `TestFixtureShape` collinearity guard.
  WHAT B DOES NOT BUY, stated rather than implied: it passes its own radius, so it says nothing about the
  VALUE of `MOTORWAY_SEARCH_RADIUS_M`. That constant is measured by the existing default-radius emit (a
  mutant that moves it changes the answer for any case that straddles the new value) and by
  `test_proximity.py`'s structural assertion that the radius stays clear of score.py's 150 m. That is
  unchanged by this edit, and it is not the hole 03:35Z named.
  CONSEQUENCES ACCEPTED: the baseline fingerprint and the value count MOVE (one new line per proximity
  case), so every digest quoted in the 03:30Z and 04:05Z tables is superseded by the re-run below; and the
  radius mutation's row must turn from `(IDENTICAL)` to `(differs)` while still being killed by
  `test_the_radius_is_inclusive`, which is the check this edit exists to buy.
- 2026-09-19T04:45Z RED BY NAME FIRST, then green. THE EDIT IS ONE FILE: `ops/mutate/geometry_probe.py`
  gains `at_its_own_radius` and one `emit` per proximity case. Nothing under `etl/` is touched, no fixture
  case is added, and `git diff --stat` at this commit is `ops/mutate/geometry_probe.py | 31 +++` plus this
  task file.
  (a) THE WITNESS WAS BLIND, AND THE SAME MUTANT THROUGH BOTH PROBES SAYS SO. The exclusive-radius edit
  applied to a copy and fingerprinted twice - once through `git show HEAD:ops/mutate/geometry_probe.py`,
  once through this working tree's - with no pytest in it at all:

        HEAD's probe (the hole): pristine e92225a056e1d2b1 over 175 values | exclusive-radius mutant e92225a056e1d2b1 over 175 -> IDENTICAL - the witness is blind
        this tree's probe      : pristine 7e4a5ae891425963 over 192 values | exclusive-radius mutant db4462b2c31aec4e over 192 -> differs

  16 of the 192 values move - every motorway case except `no_motorways_at_all`, whose unbounded answer is
  already `inf` and for which `inf < inf` and `inf <= inf` agree. 192 = 175 + one line for each of the 17
  proximity cases in the two geometry fixtures.
  (b) THE ARM ITSELF, RED, WITH THE FALSE EQUIVALENCE THE HOLE WOULD HAVE WAVED THROUGH. A fifth EQUIVALENT
  entry claiming exactly the ruling this hole made possible - *the reporting radius is exclusive, "no case
  sits on it anyway"* - added to `geometry_arms.py` in the worktree, `python ops/mutate/geometry.py`,
  exit 1:

        equivalent         RED DEMO ONLY - the reporting radius is exclusive, 'no case sits on it anyway'
            exit=1   1 red  fingerprint db4462b2c31aec4e over 192 values (DIFFERS)
            WITNESS FAILED: The false equivalence the blind witness would have waved through

        POPULATION 12 mutations over 6 classes (floor 12), 5 equivalent (floor 4)
        EQUIVALENT BUT CAUGHT - a test with an opinion about how the code is WRITTEN:
            ("RED DEMO ONLY - the reporting radius is exclusive, 'no case sits on it anyway'", ['test_the_radius_is_inclusive'])
        EQUIVALENT BUT THE FINGERPRINT MOVED - the ruling is false, like round 3's:
            RED DEMO ONLY - the reporting radius is exclusive, 'no case sits on it anyway'

  Under HEAD's probe that same entry would have printed `(IDENTICAL)` on the witness arm - (a) is the
  measurement. The entry was then REMOVED: it is a demonstration, not a population member, and
  `geometry_arms.py` is byte-identical to HEAD at this commit (`git status --short` -> two paths, neither
  of them that file).
- 2026-09-19T04:50Z ACCEPTANCE, RE-RUN BARE AND RE-QUOTED WHOLE AT THE FINAL CODE COMMIT. The baseline
  fingerprint and the value count MOVED with this edit, so every digest in the 03:30Z A3 table and in the
  04:05Z re-measurement is superseded by the table below; the 04:22Z verifier's line-for-line match is
  against the old probe and is superseded with them. `python ops/mutate/geometry.py`, exit 0, whole output:

        BASELINE  6 test files, pytest exit=0, 0 failed; fingerprint 7e4a5ae891425963 over 192 values

        MUTATIONS - each must be killed BY THE TEST THAT NAMES IT
        segment-subset     line_distance_m walks only the WAY's first segment
            exit=1  10 red  fingerprint 69771d6ccb375ac6 (differs)  named red: ['test_the_nearest_approach_may_be_on_a_later_segment_of_the_way', 'test_the_way_may_bend_toward_the_motorway_between_its_end_nodes']
        segment-subset     line_distance_m walks only the WAY's last segment
            exit=1   8 red  fingerprint 2a1354986781a5db (differs)  named red: ['test_the_way_may_bend_toward_the_motorway_between_its_end_nodes']
        segment-subset     snap.length_m drops the way's LAST segment (every-but-last)
            exit=1  38 red  fingerprint 296f09518bae04c4 (differs)  named red: ['test_a_multi_segment_tunnel_is_measured_end_to_end', 'test_the_sinuosity_matches_the_fixture']
        chord-for-path     tunnel_meters measures the bore's chord, not its path
            exit=1   5 red  fingerprint 7ca2f9b8fbea0706 (differs)  named red: ['test_the_bore_measures_its_path_and_not_its_chord', 'test_a_bent_bore_crosses_the_threshold_only_along_its_path']
        chord-for-path     the CANDIDATE motorway is reduced to its chord before it is measured
            exit=1   4 red  fingerprint 7a7706edf3ce2528 (differs)  named red: ['test_the_metres_to_the_nearest_motorway_match_the_fixture']
        chord-for-path     way_sinuosity's NUMERATOR becomes the chord, so every way reads 1.0
            exit=1   7 red  fingerprint 5bccddfad2c85ebf (differs)  named red: ['test_the_sinuosity_matches_the_fixture', 'test_the_term_is_raw_and_unbounded_not_a_0_to_1_score']
        candidate-order    the LAST candidate wins instead of the nearest one
            exit=1   2 red  fingerprint d0cc0b3703a2ebdb (differs)  named red: ['test_the_candidate_order_cannot_change_the_answer']
        candidate-order    the reporting radius becomes exclusive - a tie at the radius reads inf
            exit=1   1 red  fingerprint db4462b2c31aec4e (differs)  named red: ['test_the_radius_is_inclusive']
        interior-interior  drop the pairs interior to BOTH lines - round 3's retracted 'equivalent'
            exit=1   3 red  fingerprint 87f3b02e2332c7c8 (differs)  named red: ['test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines', 'test_the_pairs_that_touch_an_end_segment_all_read_past_the_proximity_threshold']
        earth-model        metres per degree of latitude becomes the equatorial 111234.7
            exit=1  13 red  fingerprint 5d425b46a1f0ea4a (differs)  named red: ['test_the_way_may_bend_toward_the_motorway_between_its_end_nodes', 'test_the_nearest_approach_may_need_a_segment_interior_to_both_polylines']
        earth-model        is_tunnel consults the allowlist without stripping or lowercasing
            exit=1   2 red  fingerprint 8a84e385ed83e609 (differs)  named red: ['test_the_tunnel_metres_match_the_fixture', 'test_is_tunnel_agrees_with_the_metres']
        banded-subset      keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class
            exit=1   3 red  fingerprint b5934330655c321d (differs)  named red: ['test_the_minimum_can_sit_far_off_the_diagonal_of_the_segment_pair_matrix', 'test_the_banded_window_answers_inf_where_the_whole_matrix_answers_99_metres']

        EQUIVALENT - must go MISSED, with a digest identical to the pristine one
        equivalent         measure the candidate against the way instead of the way against the candidate
            exit=0   0 red  fingerprint 7e4a5ae891425963 over 192 values (IDENTICAL)
        equivalent         snap.length_m pairs the coordinates with an explicit slice instead of relying on zip
            exit=0   0 red  fingerprint 7e4a5ae891425963 over 192 values (IDENTICAL)
        equivalent         the candidate distance is the first argument of min rather than the second
            exit=0   0 red  fingerprint 7e4a5ae891425963 over 192 values (IDENTICAL)
        equivalent         _crosses tests the degeneracies before the sides rather than after
            exit=0   0 red  fingerprint 7e4a5ae891425963 over 192 values (IDENTICAL)

        POPULATION 12 mutations over 6 classes (floor 12), 4 equivalent (floor 4)
        every one of the 12 mutations was killed by the test that names it, and every one of
        the 4 equivalent mutants went MISSED with a byte-identical fingerprint

  TWELVE OF TWELVE NOW `(differs)`: the radius row is the one that read `(IDENTICAL)` at 03:30Z and 04:05Z
  and it is `db4462b2c31aec4e (differs)`, still killed by `test_the_radius_is_inclusive` and by nothing
  else. ALL FOUR EQUIVALENT ENTRIES STILL COME BACK IDENTICAL, at the new baseline `7e4a5ae891425963` -
  none of the four became visible when 17 boundary questions were added, which is what their reasons
  predict (a symmetry, zip's truncation rule, min's commutativity, the order of pure conjuncts: none of
  them is about the radius comparison).
  * `python ops/mutate/geometry.py --prove-floor`, exit 0 - all four arms unchanged by this edit:
    `FLOOR PROOF OK: emptied -> refused=True, one deleted -> refused=True, class 'banded-subset' deleted
    -> refused=True, real -> accepted=True`, over `with the population emptied:` (8 FLOOR lines),
    `with one mutation and one equivalent deleted (11, 3):` (3 lines), and `with class 'banded-subset'
    traded for copies of 'segment-subset', population still 12:` (the one `no mutation left in class`
    line). This is P-PROC-05's assertion.
  * `python ops/mutate/geometry.py --non-example`, exit 0: `pristine digest 7e4a5ae891425963 over 192
    values / mutant digest 87f3b02e2332c7c8 over 192 values`, `3 of 192 fingerprint values differ; 3 named
    test(s) red`, ending `NON-EXAMPLE OK: the round-3 ruling is REFUTED by this arm's own test`. It was
    2 of 175 before; the third differing value is the new `meters_at_its_own_radius` line for
    `nearest_approach_interior_to_both_polylines`, 99.48600000003353 against 406.4842081198996 - the same
    two numbers the entry's reason quotes.
  * `cd services/etl && python -m pytest tests -rs` -> `1040 passed in 106.53s (0:01:46)`, exit 0, and the
    `-rs` short summary is EMPTY: zero skips. Unchanged at 1040 - this edit adds no test and touches
    nothing under `etl/`. Every `__pycache__` under services/etl was removed before the run.
  * `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8),
    none over 300 lines`, exit 0.
  * `bash ops/lib/check-exec-bits` -> `P-OPS-01: 68 files, 23 required present, all modes correct`, exit 0.
  * `bash ops/queue-check` -> `QUEUE OK (182 tasks)`, exit 0.
  * `bash ops/check-pins --source-only` -> `PINS ok=12 skipped=14 pending=1 expired=0 failed=0 tier=linux
    source-only`, exit 0 (P-PROC-05 is `anchor: process`, so --source-only skips it by design).
  * `wc -l ops/mutate/geometry*.py`: geometry.py 237, geometry_arms.py 75, geometry_mutations.py 145,
    geometry_probe.py 119, geometry_tree.py 110 - and services/etl/tests/test_proximity_banded.py 190.
    geometry_probe.py is the only one that moved (88 -> 119) and it is 181 lines clear of the 300-line
    cap, so nothing is split. `git ls-files -s ops/mutate/geometry*.py` -> all five 100644 (ruling 2).
- 2026-09-19T04:52Z STILL OPEN, superseding the 03:35Z list. Item 1 is CLOSED; the other four stand
  unchanged and none of them is claimed as done.
  1. CLOSED by this commit. The boundary is no longer a coordinate that has to land on 1000.0: the probe
     asks each proximity case for its own answer back at its own answer, `<=` is the identity `x <= x`
     there, and the exclusive mutant answers `inf` on 16 of the 17 cases. Measured both ways at 04:45Z (a)
     and demonstrated on the arm itself at 04:45Z (b). What is NOT closed and never was part of item 1:
     the probe says nothing about the VALUE of `MOTORWAY_SEARCH_RADIUS_M`, which the default-radius emit
     and `test_proximity.py`'s structural assertion carry between them.
  2. NOTHING RUNS THE FULL SWEEP ON A SCHEDULE. Stands exactly as written at 03:35Z: P-PROC-05 asserts
     `--prove-floor`, and the 17-run sweep is run by hand, here and by the reviewer. T-0184 is where that
     changes.
  3. `test_the_metres_to_the_nearest_motorway_match_the_fixture` exists in BOTH test_proximity.py and
     test_proximity_bends.py and `red_by_name` matches on the bare name. Stands; recorded, not renamed.
  4. The probe measures `sinuosity` and `proximity` only, never `score.score`, so the product costs are
     argued from score.py's constants rather than measured end to end. Stands - this edit adds a
     proximity question, not a score one. T-0168 is what makes it measurable.
  5. `snap.py` is a subject with two mutations and one equivalent but no class of its own in
     REQUIRED_CLASSES. Stands; a seventh class, not a thirteenth entry, if T-0161's successor grows it.
- 2026-09-19T05:16:32Z **REVIEW ROUND 1 - FAIL, one BLOCKING - agent/rv1-pr107 on PR #107, head 654fe97.**
  RE-RUN BARE in a detached worktree at 654fe97: `python ops/mutate/geometry.py` exit 0, table identical
  line for line to the 04:50Z acceptance block including every digest and the baseline
  `7e4a5ae891425963 over 192 values`; `--prove-floor` exit 0 (FLOOR PROOF OK, all four arms);
  `--non-example` exit 0 (`3 of 192`, 99.48600000003353 against 406.4842081198996);
  `cd services/etl && python -m pytest tests -rs` -> `1040 passed in 108.59s`, exit 0, zero skips;
  `bash ops/lib/check-line-cap` -> 71 Swift files, none over 300; `bash ops/lib/check-exec-bits` ->
  `68 files, 23 required present, all modes correct`; `bash ops/queue-check` -> `QUEUE OK (182 tasks)`;
  `bash ops/check-pins --source-only` -> `PINS ok=12 skipped=14 pending=1 expired=0 failed=0 tier=linux
  source-only`; every quoted `wc -l` (237/75/145/119/110/190) and all five 100644 modes confirmed;
  `git diff dcaf3bd...HEAD -- queue/` is append-only; `gh pr checks 107` -> core pass, pins-source-only pass.
  FIVE MUTANTS OF THE HARNESS, each alone, `git status --short` empty after each. Four REFUSED as claimed:
  a killer naming a test that does not exist (exit 1, NAMED TEST DID NOT GO RED); an anchor absent from the
  source (exit 1, `DID NOT APPLY - anchor appears 0 times`, NEVER APPLIED - it did not run a pristine tree
  and call it caught); a real killed mutation pasted into `geometry_arms.py` (exit 1, EQUIVALENT BUT CAUGHT
  **and** EQUIVALENT BUT THE FINGERPRINT MOVED - the witness refuses by digest); `TEST_FILES` minus
  `tests/test_proximity_banded.py` (exit 1, `named red: []`, refused as not-red rather than green).
  **BLOCKING (1) - AN EMPTY `killers` LIST READS AS "KILLED BY THE TEST THAT NAMES IT".** Replace the
  banded entry's two killer names in `ops/mutate/geometry_mutations.py` with `[]` and `python
  ops/mutate/geometry.py` exits 0 over

        banded-subset      keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class
            exit=1   3 red  fingerprint b5934330655c321d (differs)  named red: []

        POPULATION 12 mutations over 6 classes (floor 12), 4 equivalent (floor 4)
        every one of the 12 mutations was killed by the test that names it, and every one of
        the 4 equivalent mutants went MISSED with a byte-identical fingerprint

  `--prove-floor` is exit 0 in that state too, so P-PROC-05 and CI stay green. `red_by_name` returns `[]`
  and the guard is `len(red) != len(killers)` - 0 == 0 - while `population_ok` counts entries and classes
  and never asks whether an entry names a killer. budget.py has no such hole because it has no per-entry
  killers: its `trapped` bucket ("non-zero exit, but NO named test failed - does not count") is the floor
  this runner loses at zero. The quiet trim is realistic - a renamed or flaky killer deleted, `[]` left -
  and it leaves the SIXTH CLASS, the reason this task exists, measured by nothing while the sheet reads
  clean. This is P-PROC-05's own `why_no_test_catches_it` one axis down.
  RECORDABLE, not blocking: (1) `geometry_probe.py` cannot tell the copy from the worktree - pointed at
  `services/etl` it prints the pristine 192 lines and the BASELINE digest with no refusal, and the table
  names no measured root; (2) STILL OPEN (5) is understated - `tests/test_snap.py` is in TEST_FILES but no
  killer names a test in it (the snap mutations' killers are in test_proximity.py and test_sinuosity.py),
  so snap.py is a dependency of this population rather than a subject of it; (3) for T-0187: copy the
  copy-then-mutate tree, the computed witness and the two-sided floor; do NOT copy the `killers` field
  without a non-empty clause, and use a `file::test` killer form, because
  `test_the_metres_to_the_nearest_motorway_match_the_fixture` already exists in two TEST_FILES
  (test_proximity.py:149, test_proximity_bends.py:151).
  Review worktree removed; nothing in the repository was changed by this review.
- 2026-09-19T05:24:41Z **ROUND 2 - rv1-pr107's B1 REPRODUCED AND ACCEPTED, rulings before code - agent/claude-opus-5.**
  REPRODUCED FIRST, at 654fe97, by emptying the banded-subset entry's `killers` in
  `ops/mutate/geometry_mutations.py` (`[]` in place of the two names) and running both entry points bare:

        banded-subset      keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class
            exit=1   3 red  fingerprint b5934330655c321d (differs)  named red: []

        POPULATION 12 mutations over 6 classes (floor 12), 4 equivalent (floor 4)
        every one of the 12 mutations was killed by the test that names it, and every one of
        the 4 equivalent mutants went MISSED with a byte-identical fingerprint
        SWEEP_EXIT=0

  and `python ops/mutate/geometry.py --prove-floor` -> `FLOOR PROOF OK: emptied -> refused=True, one
  deleted -> refused=True, class 'banded-subset' deleted -> refused=True, real -> accepted=True`,
  `FLOOR_EXIT=0`. Both exit 0. The reviewer is right line for line: `red_by_name([], failed)` is `[]`,
  the sweep's guard is `len(red) != len(killers)` - `0 == 0` - and `population_ok` counts entries,
  equivalents and classes and never asks whether an entry NAMES a killer. The mutant still applies, still
  moves the fingerprint, still turns three tests red, and the sheet still reads clean: the sixth class,
  the axis this task exists for, is measured by nothing while P-PROC-05 and CI stay green. The tracked
  file was restored with `git checkout --` immediately; `git status --short` is the task file alone.
  RULING 1 - WHERE THE PER-ENTRY FLOOR GOES: `population_ok()`, beside the count and class arms, and NOT
  a second guard inside `sweep()`. The floor runs before `fingerprint_of_pristine()` and before the
  baseline pytest, so an entry that names no killer refuses BY NAME at exit 2 having run no test at all,
  which is the same shape and the same exit code as a deleted class. A belt-and-braces `if not killers`
  in `verdict`'s bucket would be unreachable once the floor exists, and CLAUDE.md forbids shipping a
  check that can never be demonstrated red. One point of refusal, demonstrable.
  RULING 2 - THE ARM COUNT. `--prove-floor` printed FOUR claims (emptied, one deleted, class traded,
  real); it now prints FIVE - the fourth is the killers of the last entry emptied with the population
  left AT 12 over all SIX classes, so neither the count arm nor the class arm can see it, exactly as the
  class arm was built to see what the count arm cannot. rv1's "fourth arm" is the fourth REFUSAL arm; the
  fifth claim is the real population, which must still be accepted.
  RULING 3 - R1, THE MEASURED ROOT: the probe emits the root's IDENTITY as line one, and NOT a digest of
  the three subject sources. A source digest is CONTENT, and the wrong tree here is `services/etl`, which
  is PRISTINE by construction - its content digest is the baseline's content digest, so a worktree-
  pointed probe would fold in exactly the bytes that make it read IDENTICAL. It would be a witness that
  agrees with the mistake it is supposed to expose. A location cannot be confused that way. Line one is
  the root written RELATIVE to the repository root with forward slashes (`.build-mutate-geometry/etl` vs
  `services/etl`), never the absolute path: an absolute path would make every digest depend on the
  checkout, and the round-1 review quoting this table line for line from a different worktree is the
  reason that property is worth keeping. WHY THE EQUIVALENT ARM CAN NO LONGER BE SATISFIED BY A
  WORKTREE-POINTED PROBE: that arm passes only on `digest == base_digest`, the baseline is taken over the
  copy and now carries `.build-mutate-geometry/etl` in its first hashed line, so any fingerprint taken
  over `services/etl` differs in line one whatever the module answers. It reads DIFFERS - a WITNESS
  FAILED - instead of IDENTICAL. It fails closed. Demonstrated below, at no pytest cost, by running the
  probe over both roots. The baseline digest and the value count both move (192 -> 193 lines) and every
  digest in the table with them; the numbers quoted in the 04:50Z entry are not edited, they are
  superseded by this entry's.
  RULING 4 - R2, SNAP.PY: recorded, no code. `tests/test_snap.py` is in TEST_FILES and `snap.py` carries
  two mutations and one equivalent, but no `killers` list names a test in that file - the snap mutations
  are killed from test_proximity.py and test_sinuosity.py, through `length_m` and `distance_on_earth`.
  So snap.py is a DEPENDENCY of this population, not a subject of it, and STILL OPEN item 5 says that
  from this entry on instead of "a subject with no class of its own". A seventh REQUIRED_CLASS is owed
  the day snap.py grows behaviour of its own (a segment rule, a projection choice) rather than being the
  arithmetic the other two terms lean on; adding one now would declare an axis with nothing on it, which
  is the defect this harness refuses in the other direction.
  RULING 5 - THE PIN. P-PROC-05's `why_no_test_catches_it` enumerates what `--prove-floor` does; a fourth
  refusal arm that the prose does not mention is a pin that documents less than it asserts, so the prose
  records the empty-killers hole, that rv1-pr107 found it, and that it was seen red before green. The
  statement and the assertion command are unchanged, and no floor constant moves: MIN_MUTATIONS stays 12
  and MIN_EQUIVALENT stays 4, so no ratchet proviso is owed.
- 2026-09-19T05:38:06Z **ROUND 2 FIX - the per-entry killer floor, its arm, and the measured root; whole acceptance
  block re-run at the final commit - agent/claude-opus-5.** `git diff --numstat` at this commit:
  `ops/mutate/geometry.py` 40/9, `ops/mutate/geometry_mutations.py` 6/4, `ops/mutate/geometry_probe.py`
  30/1, `pins/PINS.yaml` 1/1 (the one prose scalar). No test file and nothing under `services/etl/etl/`
  was touched, and no floor constant moved: MIN_MUTATIONS is still 12, MIN_EQUIVALENT still 4.
  RED FIRST, BY NAME, WITH NO PYTEST. The banded-subset entry's two killer names replaced by `[]` - the
  state that was exit 0 twice at 05:24Z - `python ops/mutate/geometry.py`:

        POPULATION FLOOR: keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class names
        no killer - a mutation nobody is required to catch is not a measurement. A shrunken population
        must never read as a clean sheet.
        SWEEP_EXIT=2

  It returns in under a second: the floor is the first thing `sweep()` calls, so it refuses before the
  copy is made and before the baseline pytest - no test is run over a population that is not a
  measurement. `python ops/mutate/geometry.py --prove-floor` in the same state, `FLOOR_EXIT=1`:

        with the killers of 'keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class'
        emptied, population still 12 over 6 classes:
        POPULATION FLOOR: ... names no killer - a mutation nobody is required to catch is not a measurement.
        with the real population (12 mutations over 6 classes, 4 equivalent):
        POPULATION FLOOR: ... names no killer - a mutation nobody is required to catch is not a measurement.
        FLOOR PROOF FAILED: emptied -> refused=True, one deleted -> refused=True, class 'banded-subset'
        deleted -> refused=True, killers emptied -> refused=True, real -> accepted=False

  Both ways, exactly as rv1-pr107 asked: the new arm refuses AND the real population is rejected, so
  P-PROC-05 goes red on the state that used to keep it green. The tracked file was restored from a byte
  copy taken before the edit, never `git checkout --`, which would have reverted this commit's work with
  it.
  R1, DEMONSTRATED AT NO PYTEST COST. The same pristine content measured at two roots, which before this
  commit was the same digest twice:

        the COPY      digest 9e82ff9a84e7753e over 193 values
            line one: MEASURED ROOT  tree  .build-mutate-geometry/etl
        the WORKTREE  digest 647283a7a5b12abd over 193 values
            line one: MEASURED ROOT  tree  services/etl

  Identical bytes under `etl/`, identical 192 values after line one, two different fingerprints. The
  EQUIVALENT arm passes only on `digest == base_digest` and the baseline is taken over the copy, so a
  probe pointed at `services/etl` can no longer satisfy it whatever the module answers - it reads
  DIFFERS and prints WITNESS FAILED. The path is relative with forward slashes, so the digest is the
  same number in any checkout and this table is still quotable line for line from a review worktree.
  THE WHOLE ACCEPTANCE BLOCK, RE-RUN BARE AT THIS COMMIT. Every digest below is NEW - line one moved the
  fingerprint from 192 values to 193 - and supersedes the 04:50Z table rather than editing it.
  * `python ops/mutate/geometry.py`, `SWEEP_EXIT=0`. `BASELINE 6 test files, pytest exit=0, 0 failed;
    fingerprint 9e82ff9a84e7753e over 193 values`, then:

        segment-subset     line_distance_m walks only the WAY's first segment
            exit=1  10 red  09f2d2d176a7e1dd (differs)  ['..._may_be_on_a_later_segment_of_the_way',
                                                         '..._may_bend_toward_the_motorway_...']
        segment-subset     line_distance_m walks only the WAY's last segment
            exit=1   8 red  c59e9325ed921152 (differs)  ['..._may_bend_toward_the_motorway_...']
        segment-subset     snap.length_m drops the way's LAST segment (every-but-last)
            exit=1  38 red  41816e1e1d93f95b (differs)  ['test_a_multi_segment_tunnel_is_measured_end_to_end',
                                                         'test_the_sinuosity_matches_the_fixture']
        chord-for-path     tunnel_meters measures the bore's chord, not its path
            exit=1   5 red  20d179f8ce2fe41d (differs)  ['test_the_bore_measures_its_path_and_not_its_chord',
                                                         'test_a_bent_bore_crosses_the_threshold_...']
        chord-for-path     the CANDIDATE motorway is reduced to its chord before it is measured
            exit=1   4 red  716a64b23a534da4 (differs)  ['test_the_metres_to_the_nearest_motorway_...']
        chord-for-path     way_sinuosity's NUMERATOR becomes the chord, so every way reads 1.0
            exit=1   7 red  99cf288220409df6 (differs)  ['test_the_sinuosity_matches_the_fixture',
                                                         'test_the_term_is_raw_and_unbounded_...']
        candidate-order    the LAST candidate wins instead of the nearest one
            exit=1   2 red  97d939fd7cfa097d (differs)  ['test_the_candidate_order_cannot_change_the_answer']
        candidate-order    the reporting radius becomes exclusive - a tie at the radius reads inf
            exit=1   1 red  8fdbf69aca444534 (differs)  ['test_the_radius_is_inclusive']
        interior-interior  drop the pairs interior to BOTH lines - round 3's retracted 'equivalent'
            exit=1   3 red  fd28a2d3d96546e8 (differs)  ['..._interior_to_both_polylines',
                                                         '..._all_read_past_the_proximity_threshold']
        earth-model        metres per degree of latitude becomes the equatorial 111234.7
            exit=1  13 red  4b46fef332716390 (differs)  ['..._may_bend_toward_the_motorway_...',
                                                         '..._interior_to_both_polylines']
        earth-model        is_tunnel consults the allowlist without stripping or lowercasing
            exit=1   2 red  4345137c27cfb8c1 (differs)  ['test_the_tunnel_metres_match_the_fixture',
                                                         'test_is_tunnel_agrees_with_the_metres']
        banded-subset      keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class
            exit=1   3 red  f2e69fa493a1ecc0 (differs)  ['..._far_off_the_diagonal_of_the_segment_pair_matrix',
                                                         '..._answers_inf_where_the_whole_matrix_answers_99_metres']

        EQUIVALENT - all four exit=0, 0 red, 9e82ff9a84e7753e over 193 values (IDENTICAL):
        the candidate measured against the way; snap.length_m's explicit slice; the candidate distance as
        min's first argument; _crosses testing the degeneracies before the sides

        POPULATION 12 mutations over 6 classes (floor 12), 4 equivalent (floor 4)
        every one of the 12 mutations was killed by the test that names it, and every one of
        the 4 equivalent mutants went MISSED with a byte-identical fingerprint

    Twelve of twelve `(differs)` and named-red exactly as before; the four equivalents are still IDENTICAL
    at the new baseline, which is what their reasons predict - none of them is about which tree was
    measured, and all four move with the baseline together.
  * `python ops/mutate/geometry.py --prove-floor`, `FLOOR_EXIT=0`: `FLOOR PROOF OK: emptied ->
    refused=True, one deleted -> refused=True, class 'banded-subset' deleted -> refused=True, killers
    emptied -> refused=True, real -> accepted=True`, over five headed sections - `with the population
    emptied:` (8 FLOOR lines), `with one mutation and one equivalent deleted (11, 3):` (3), `with class
    'banded-subset' traded for copies of 'segment-subset', population still 12:` (1), `with the killers
    of '...' emptied, population still 12 over 6 classes:` (1), and the real population (none). This is
    P-PROC-05's assertion, and the fourth refusal arm is the one the other three cannot see.
  * `python ops/mutate/geometry.py --non-example`, exit 0: `pristine digest 9e82ff9a84e7753e over 193
    values / mutant digest fd28a2d3d96546e8 over 193 values`, `3 of 193 fingerprint values differ; 3
    named test(s) red`, the three differing values still 99.48600000003353 against 406.4842081198996,
    ending `NON-EXAMPLE OK: the round-3 ruling is REFUTED by this arm's own test`. Line one is identical
    in both trees here - both are the copy - so it adds a value and no difference, which is the property
    that lets the digest carry the root without inventing a diff.
  * `cd services/etl && python -m pytest tests -rs -o addopts=` -> `1040 passed in 104.34s (0:01:44)`,
    exit 0, and the `-rs` short summary is EMPTY: zero skips. Unchanged at 1040 - this commit adds no
    test and touches nothing under `etl/`. Every `__pycache__` under services/etl was removed first.
  * `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8),
    none over 300 lines`, exit 0.
  * `bash ops/lib/check-exec-bits` -> `P-OPS-01: 68 files, 23 required present, all modes correct`, exit 0.
  * `bash ops/queue-check` -> `QUEUE OK (182 tasks)`, exit 0.
  * `bash ops/check-pins --source-only` -> `PINS ok=12 skipped=14 pending=1 expired=0 failed=0 tier=linux
    source-only`, exit 0 (P-PROC-05 is `anchor: process`, so --source-only skips it by design; it was run
    bare above).
  * `wc -l ops/mutate/geometry*.py` RE-MEASURED at this commit: geometry.py 268 (was 237),
    geometry_arms.py 75 (unchanged), geometry_mutations.py 147 (was 145), geometry_probe.py 148 (was
    119), geometry_tree.py 110 (unchanged). The runner is 32 lines clear of the 300-line cap and nothing
    is split: the boundary of meaning is unchanged - the floor is the protocol and belongs beside the
    other two arms, and moving it out would put a refusal in a file that decides nothing. The next
    addition to `geometry.py` should be weighed against that 32, and `geometry_probe.py`'s growth is the
    reason to watch it. `services/etl/tests/test_proximity_banded.py` is untouched this round (`git
    status --short` names only the four files above), so its 190 is quoted from 04:50Z, not re-measured.
  * `git ls-files -s ops/mutate/geometry*.py` -> all five `100644`. Data, not scripts (ruling 2 of
    03:10Z); `core.filemode` is false here so the mode is asserted from the index, not the disk.
- 2026-09-19T05:38:06Z STILL OPEN, superseding the 04:52Z list. Items 2, 3 and 4 stand unchanged and none of them is
  claimed as done; item 1 stays closed; item 5 is restated as rv1-pr107's R2 puts it; item 6 is new and
  is a boundary of THIS commit's fix, stated by the fixer rather than found by the next reviewer.
  1. CLOSED, and closed further by this commit. The reporting boundary is measured on every proximity
     case (04:50Z), and the fingerprint now also states WHICH tree produced it, so the EQUIVALENT arm
     cannot be satisfied by a probe pointed at the pristine worktree. rv1-pr107's R1 is closed with it.
  2. NOTHING RUNS THE FULL SWEEP ON A SCHEDULE. Stands exactly as written at 03:35Z: P-PROC-05 asserts
     `--prove-floor`, which costs no pytest run, and the 17-run sweep is run by hand - here, and by the
     reviewer. T-0184 is where that changes.
  3. `test_the_metres_to_the_nearest_motorway_match_the_fixture` exists in BOTH test_proximity.py and
     test_proximity_bends.py and `red_by_name` matches on the bare name. Stands; recorded, not renamed.
     rv1-pr107's R3 is the same fact aimed at T-0187: a `file::test` killer form is the fix, and it is
     that task's to make, not a rename here.
  4. The probe measures `sinuosity` and `proximity` only, never `score.score`, so the product costs are
     argued from score.py's constants rather than measured end to end. Stands. T-0168 makes it measurable.
  5. `snap.py` IS A DEPENDENCY OF THIS POPULATION, NOT A SUBJECT OF IT (rv1-pr107's R2, and the 04:52Z
     wording was wrong to call it a subject with no class). `tests/test_snap.py` is in TEST_FILES and two
     mutations plus one equivalent are written into `snap.py`, but no `killers` list names a test in that
     file: they are killed from test_proximity.py and test_sinuosity.py, through `length_m` and
     `distance_on_earth`. A seventh REQUIRED_CLASS is owed the day snap.py grows behaviour of its own -
     a segment rule, a projection choice - and declaring one now would create an axis with nothing on it,
     which is the defect this harness refuses in the other direction.
  6. NEW, the boundary of the floor added here: it asks only that `killers` be NON-EMPTY, not that the
     tests it names EXIST. A killer naming a test that has been renamed away is caught by the sweep -
     rv1-pr107 mutated one and got exit 1, `NAMED TEST DID NOT GO RED` - but only at the cost of a full
     pytest run, and `--prove-floor`, which is what P-PROC-05 asserts and what CI runs, cannot see it.
     Deciding it cheaply needs the names collected from the six TEST_FILES by parse rather than by
     running them, which is T-0187's `file::test` killer form (item 3) and is filed there, not here.
- 2026-09-19T05:58:56Z **REVIEW ROUND 2 - PASS - agent/rv2-pr107 on PR #107, head cd1319f (654fe97..cd1319f).**
  Read-only detached worktree `.worktrees/rv2-pr107` at cd1319f; `git status --short` there empty before and after
  every mutant, and the worktree removed at the end. Not the owner, not rv1-pr107, not the fixer.
  * SCOPE OF THE DIFF. `git diff 654fe97..HEAD --stat` -> `ops/mutate/geometry.py | 49 +-`,
    `ops/mutate/geometry_mutations.py | 10 +-`, `ops/mutate/geometry_probe.py | 31 +-`, `pins/PINS.yaml | 2 +-`,
    this task file `| 257 +++`. Nothing else. The task-file diff is APPEND-ONLY: `git diff 654fe97..cd1319f
    --numstat -- 'queue/**'` -> `257 0`, and `git diff 654fe97..cd1319f -- 'queue/**' | grep -c '^-[^-]'` -> `0`.
    rv1-pr107's 05:16:32Z FAIL entry stands ahead of the fixer's 05:24:41Z and 05:38:06Z entries; no earlier line
    was rewritten.
  * B1 IS CLOSED, AND CLOSED BY NAME. Re-applied rv1's B1 on the worktree - the banded-subset entry's `killers`
    -> `[]` - and ran `python ops/mutate/geometry.py` bare. The WHOLE output is one line, exit 2:
    `POPULATION FLOOR: keep only the segment pairs with abs(i - j) <= 1 - rv4-pr94's sixth class names no killer -
    a mutation nobody is required to catch is not a measurement. A shrunken population must never read as a clean
    sheet.` There is no `BASELINE` line, so NO pytest ran: the refusal is `population_ok()` at the top of
    `sweep()`, before the copy is built. `python ops/mutate/geometry.py --prove-floor` in the same state -> exit 1,
    `FLOOR PROOF FAILED: emptied -> refused=True, one deleted -> refused=True, class 'banded-subset' deleted ->
    refused=True, killers emptied -> refused=True, real -> accepted=False` - the new arm refuses AND the real
    population is rejected, both directions as rv1 asked. Restored with `git checkout --`; `git status --short`
    empty.
  * NOTHING REGRESSED. `python ops/mutate/geometry.py` bare on the untouched tree -> exit 0: `BASELINE 6 test
    files, pytest exit=0, 0 failed; fingerprint 9e82ff9a84e7753e over 193 values`; all 12 mutations `exit=1 ...
    (differs)`, each with a non-empty `named red: [...]` naming its own killers; all four EQUIVALENT rows
    `exit=0   0 red  fingerprint 9e82ff9a84e7753e over 193 values (IDENTICAL)`; closing `POPULATION 12 mutations
    over 6 classes (floor 12), 4 equivalent (floor 4)` and `every one of the 12 mutations was killed by the test
    that names it`. `--prove-floor` -> exit 0, `FLOOR PROOF OK` with all four refusals True and `real ->
    accepted=True`. `--non-example` -> exit 0, `3 of 193 fingerprint values differ; 3 named test(s) red`,
    `NON-EXAMPLE OK: the round-3 ruling is REFUTED by this arm's own test`.
  * THE GATES, BARE. `cd services/etl && python -m pytest tests -rs -o addopts=` -> `1040 passed in 72.66s
    (0:01:12)`, exit 0, `-rs` short summary EMPTY (zero skips); every `__pycache__` under services/etl purged
    first. `bash ops/lib/check-line-cap` -> `P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8),
    none over 300 lines`, exit 0. `bash ops/lib/check-exec-bits` -> `P-OPS-01: 68 files, 23 required present, all
    modes correct`, exit 0. `bash ops/queue-check` -> `QUEUE OK (182 tasks)`, exit 0. `bash ops/check-pins
    --source-only` (run once) -> `PINS ok=12 skipped=14 pending=1 expired=0 failed=0 tier=linux source-only`,
    exit 0.
  * THE MEASURED NUMBERS ARE THE LOG'S NUMBERS. `wc -l ops/mutate/geometry*.py` -> geometry.py 268,
    geometry_arms.py 75, geometry_mutations.py 147, geometry_probe.py 148, geometry_tree.py 110 - every one equal
    to the 05:38:06Z re-quote, and 268 is 32 lines clear of the cap. `git ls-files -s ops/mutate/geometry*.py` ->
    all five `100644`.
  * rv1's R1, PROBE PROVENANCE: CLOSED, and closed the right way round. The no-argument call still refuses
    (`REFUSED: usage: geometry_probe.py <services/etl to measure>`, exit 2). Pointed at the WORKTREE the probe
    does not refuse - it FINGERPRINTS DIFFERENTLY, which is the stronger fix: line one is now
    `MEASURED ROOT ... tree  services/etl` against `MEASURED ROOT ... tree  .build-mutate-geometry/etl`, and
    `fingerprint()` in geometry_tree.py hashes the WHOLE stdout (`hashlib.sha256(out.encode("utf-8"))`), so a
    worktree-pointed fingerprint can never equal a baseline taken over the copy - sha256 of the two probe outputs
    measured here: `607ad1cb...` against `77cf9410...`. The docstring's ruling that a CONTENT digest would have
    been the wrong instrument is correct: `services/etl` is pristine by construction, so its content digest IS the
    baseline's. rv1's R2 is recorded above by the owner, not a finding of mine.
  * MY OWN MUTANT, the per-entry contract one notch past B1: a killers list with one REAL name DUPLICATED -
    banded-subset's two names replaced by two copies of
    `test_the_minimum_can_sit_far_off_the_diagonal_of_the_segment_pair_matrix`. IT SURVIVES: `python
    ops/mutate/geometry.py` -> exit 0 with the clean two-line verdict, `--prove-floor` -> exit 0. RECORDABLE, NOT
    BLOCKING, and the reason is in the population itself: `red_by_name` returns one element per KILLER
    (`[k for k in killers if ...]`), so a duplicated name matches twice and the sweep's `len(red) != len(killers)`
    is satisfied by ONE distinct test - but a one-killer entry is LEGAL by design (four entries name exactly one),
    so reducing a two-name contract to one distinct name is a legal state reached by a cosmetic route, not an
    unmeasured mutant: this mutation is still killed by a test that names it, and nothing reads as caught that is
    not. The residual is real and smaller: `named red: ['A', 'A']` overstates the evidence, and the second named
    check (`test_the_banded_window_answers_inf_where_the_whole_matrix_answers_99_metres`) can leave the contract
    without a word. A `len(set(killers)) == len(killers)` clause in `population_ok` closes it; recorded here for a
    follow-up rather than bought as a round.
    Two neighbouring shapes weighed and NOT findings. (a) `red_by_name`'s match is `f == k or (f or
    "").startswith(k + "[")` - EXACT or parametrised, so a killer that is a SUBSTRING or a bare prefix of a longer
    test name matches nothing and the entry fails CLOSED as `CAUGHT, BUT NOT BY THE TEST THAT NAMES IT`. (b) An
    EQUIVALENT entry with an empty `reason` is only ever read on the failure path (`WITNESS FAILED: %s`), so it
    degrades a message on a run that is already exit 1; it never buys a clean verdict.
  * VERDICT: PASS, no blocking finding. queue/claimed/ -> queue/done/, reviewer agent/rv2-pr107. Not merged: a
    reviewer signs off, the merge is somebody else's step.
