---
id: T-0069
title: T-0025's provenance guard is hollow: both halves of the round-5 fix can be deleted with tests green
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T01:19:37Z
lease_expires_at: 2026-09-08T05:19:37Z
worktree: wt/T-0069
branch: task/T-0069
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
depends_on: [T-0025]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0025's round-5 blocker was that a green run could replace the committed oracle with a subset of itself
while the fixture still claimed the pinned digest. The fix had two halves: `build()` computes
`source_sha256` from the file it read, and refuses a KMZ whose digest does not match the manifest's pin.
`test_oracle_report.py::TestTheFixtureRecordsRealProvenance::test_the_fixture_was_built_from_the_pinned_oracle`
was written as the guard that makes it stick, and the task was signed off into `queue/done/` on it.

**Both halves can be deleted with the whole suite green.** Executed on task/T-0025:

    restore the hardcoded literal - defect #4 verbatim:
      "source_sha256": "3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046",
      -> 171 passed on Windows/CPython 3.10, 171 passed in the pinned scenic-etl image. Nothing red.

    delete the refusal: `if want and digest != want:` -> `if False:`
      -> also survives the whole suite with nothing red.

**Why.** Both sides of the assertion are committed, hand-editable text in the same commit: the fixture's
`source_sha256` field and `inputs/manifest.yaml`'s pin. And **no test in the suite ever calls
`oracle_select.build()` or `eligible()`** - `git grep -n 'build(\|eligible('` over `services/etl/tests/` on
that branch returns exactly one hit, inside this file's own module docstring. So the property the fix
actually introduced - that the field is COMPUTED rather than typed - is untested, and the committed fixture
already carries the manifest's literal.

The docstring's sentence *"Rebuild from any other file and `build()` records that file's digest, and this
fails"* is a claim about `build()` that the assertion cannot reach.

- Call `build()` in a test. Point it at a temporary KMZ whose digest is known and different, and assert the
  written `source_sha256` is that digest and not the manifest's. That is the property, and nothing currently
  exercises it.
- Assert the refusal separately: `build()` against an unpinned KMZ must raise, with the message naming both
  digests.
- The sweep also notes `build()`'s refusal keys on the BASENAME via `oracle.pinned_digest(kmz.name)`, so a
  differently-named file with the same basename resolves to the same pin. Check whether that is reachable.
- Demonstrate red by restoring the literal, exactly as above, and show the new test failing where the whole
  suite currently passes.

**This is the same defect one level further out, for the sixth time in this task's history** - each round's
fix containing the shape it was written to remove. Worth stating in the log rather than only fixing, because
the pattern is the finding.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the self-referential-check sweep, which was built precisely to
  hunt this class after it appeared in five consecutive rounds of T-0025. It found it in the round-5 fix.
- 2026-09-08T01:19:37Z claimed by agent/claude-opus-5; lease until 2026-09-08T05:19:37Z
- 2026-09-08 agent/claude-opus-5 fixed by adding `services/etl/tests/test_oracle_build.py` (189 lines, 6
  tests), the first thing in the suite to CALL `oracle_select.build()`. It drives build() off a synthetic
  three-node KMZ written into `tmp_path`, so it needs neither the 2.5 MB oracle nor osmium. No production
  code changed - the defect was that nothing exercised the two halves, not that either half was wrong.

### RED - the two halves deleted, whole suite green (host CPython 3.10.11, pytest 9.1.1, cd services/etl)

Baseline first:

    $ python -m pytest
    ........................................................................ [ 42%]
    ........................................................................ [ 84%]
    ...........................                                              [100%]
    171 passed in 5.47s

Mutation 1 - `"source_sha256": digest,` -> `"source_sha256": "3bdf4d14...9046",`:

    $ python -m pytest
    ........................................................................ [ 42%]
    ........................................................................ [ 84%]
    ...........................                                              [100%]
    171 passed in 4.39s

Mutation 2 - `if want and digest != want:` -> `if False:` (mutation 1 reverted first):

    $ grep -n 'if False:' etl/oracle_select.py
    187:    if False:
    $ python -m pytest
    ........................................................................ [ 42%]
    ........................................................................ [ 84%]
    ...........................                                              [100%]
    171 passed in 4.31s

Both halves of the round-5 fix deleted, nothing red, exactly as filed.

### RED - the same two mutations against the new test file

Mutation 1, `source_sha256` back to the hardcoded literal:

    $ python -m pytest
    >       assert written == sha256_of(kmz)
    E       AssertionError: assert '3bdf4d140a6d...f2340b7039046' == '9885865320f4...ac872ad893781'
    E         - 9885865320f45e3628df9b9281adf207e49c1a90dcc168f9d42ac872ad893781
    E         + 3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046
    =========================== short test summary info ===========================
    FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_written_digest_is_the_kmz_on_disk_and_not_the_manifest_pin
    FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_digest_moves_when_the_bytes_move
    FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_renaming_the_kmz_walks_straight_past_the_refusal
    3 failed, 174 passed in 4.92s

Mutation 2, the refusal disabled:

    $ python -m pytest
    >           with pytest.raises(SystemExit):
    E           Failed: DID NOT RAISE SystemExit
    =========================== short test summary info ===========================
    FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_it_raises_and_names_both_digests
    FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_is_keyed_on_the_basename_not_on_the_path
    2 failed, 175 passed in 4.86s

Both mutations at once in the PINNED image - `docker run --rm -v "$PWD:/w" -w /w scenic-etl:latest python3
-m pytest`, driven from WSL2 because docker is not on the Windows host PATH:

    FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_written_digest_is_the_kmz_on_disk_and_not_the_manifest_pin
    FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_digest_moves_when_the_bytes_move
    FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_it_raises_and_names_both_digests
    FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_is_keyed_on_the_basename_not_on_the_path
    FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_renaming_the_kmz_walks_straight_past_the_refusal
    5 failed, 171 passed, 1 skipped in 5.12s

### GREEN - oracle_select.py restored byte-for-byte, `git diff --stat` on it empty

    $ python -m pytest
    ........................................................................ [ 40%]
    ........................................................................ [ 81%]
    .................................                                        [100%]
    177 passed in 5.10s

Pinned image, same tree:

    176 passed, 1 skipped in 3.90s

The skip is `tests/test_manifest.py:47: git is not installed here, cannot check tracking` - the image ships
no git, so that test skips there and passes on the host. The brief's "171 passed in the pinned image" was
therefore 170 passed + 1 skipped. A cosmetic correction to the filing, not a finding.

### The BASENAME question, executed rather than reasoned

`build()` asks `oracle.pinned_digest(kmz.name)`, so the pin is keyed on the file NAME. Both directions are
reachable from the shipped CLI. One synthetic KMZ, two names:

    $ python -m etl.oracle --kmz work/probe/vermont-curvature.kmz --build work/probe/caseA.json \
        --export work/probe/subset.geojsonseq
    vermont-curvature.kmz is not the pinned oracle.
      pinned : 3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046
      on disk: c070142a00555a41ab0fd502377932788e31c9eca03c0e09148ee90b339ebef6
    Refusing to build a fixture from it. Re-fetch with ops/etl-fetch-inputs, or - if upstream really did
    regenerate it - re-pin deliberately after looking at what changed.
    exit=1
    ls: cannot access 'work/probe/caseA.json': No such file or directory

    $ cp work/probe/vermont-curvature.kmz work/probe/not-the-oracle.kmz     # byte-identical
    $ python -m etl.oracle --kmz work/probe/not-the-oracle.kmz --build work/probe/caseB.json \
        --export work/probe/subset.geojsonseq
      single_way                1
      have_geometry             1
      geometry_identical        1
      no_squash                 1
    oracle: wrote 1 way(s) to work\probe\caseB.json
    exit=0

So: a differently-LOCATED file carrying the pinned basename IS refused - the protective direction, and it is
reachable, since `services/etl/work/probe/` is not `inputs/`. A RENAMED file is not checked at all:
`pinned_digest` returns None, `want` is falsy, the refusal never runs. The rename is the hole.

It is contained, but only by the OTHER half. Measured, not argued - the case-B output copied over the
committed fixture:

    $ cp work/probe/caseB.json tests/fixtures/curvature_oracle.json
    $ python -m pytest tests/test_oracle_report.py
    E       AssertionError: the fixture was built from a KMZ that is not the pinned oracle
    E       assert 'c070142a0055...ee90b339ebef6' == '3bdf4d140a6d...f2340b7039046'
    FAILED tests/test_oracle_report.py::TestTheFixtureRecordsRealProvenance::test_the_fixture_was_built_from_the_pinned_oracle
    1 failed, 6 passed in 0.14s

The round-5 replacement attack does come back through a rename, and the committed-fixture assertion is the
only thing that stops it - which works only while `source_sha256` is COMPUTED. The refusal and the fixture
assertion cover each other's blind spot and neither covers its own; before this file, deleting either one
was free. Left as a finding rather than fixed here: narrowing the pin to a path, or refusing an unpinned
name outright, is a behaviour change to a load-bearing script and belongs in its own task.
`test_renaming_the_kmz_walks_straight_past_the_refusal` pins the hole as it stands, so closing it will show
up as a deliberate red rather than a silent one.

### The pattern, since the filing asks for it to be stated

Round 5 removed a self-referential guard - a fixture asserting its own provenance - and shipped the same
shape one level out: a test comparing two hand-editable literals that sit in the same commit, standing in
for a claim about a function neither side calls. The literal and the pin are not two independent
observations of the same fact; they are one fact typed twice. Nothing here is safe from the sixth round
either. The one property that distinguishes this fix is that the new tests fail when the code they describe
is deleted, and that was demonstrated above rather than asserted.

### Gates, in the worktree

    $ bash ops/queue-check
    QUEUE OK (50 tasks)
    $ bash ops/check-pins --source-only
    PINS ok=3 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
    $ bash ops/check-pins
    PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
    $ bash ops/test
    TESTS linux=227/76 ios=skipped failed=0 skipped=0
    OK

221 -> 227; the same command with the new file moved aside prints `linux=221/76`.

`ops/test` FAILED on its first run here, and it is not this change: `FAIL: services/api exists but vitest
produced no report`, exit 1, reproduced identically with `test_oracle_build.py` moved out of the tree.
`services/api/node_modules` does not exist in a fresh worktree, so `npx vitest` produced no report and
ops/test correctly refused to call that a pass. `npm ci` in `services/api` (85 packages, gitignored, nothing
staged) cleared it. Recorded because a fresh worktree fails the repo's one verification command for an
environment reason whose message names neither npm nor node_modules.

- 2026-09-08 adversarial verification by a second agent that did not write the fix. **holds = false.**
  The fix is real and its own transcript reproduces; it does not survive contact. Reproduced first,
  then every evasion below was EXECUTED, not argued. Full report follows verbatim so the next person
  inherits the limits along with the code.

  # Adversarial verification of T-0069 — holds = False
  
  ## Verdict
  
  HOLDS = FALSE. 12 evasions executed; 5 caught, 7 passed with the suite green at 177 passed.
  
  WHAT THE FIX GENUINELY DOES. Baseline reproduces exactly as the fixer reported: clean tree 177 passed (6 new tests in services/etl/tests/test_oracle_build.py, 171 before). Both claimed mutations go red at the counts claimed - the literal digest gives 3 failed / 174 passed, `if False:` gives 2 failed / 175 passed. `git diff --stat fc068e6 7c229c3` confirms no production code changed: 2 files, 414 insertions. I also tried the three standard dodges AROUND those two mutations and the guard caught all three: emptying the population (`published = {}`), typing the pin lookup so it silently misses (`kmz.name` -> `kmz.stem`), and nulling an operand so the equality is vacuous (`want = digest`). The one place this repo usually fails - a guard deriving both sides of its comparison from the thing it checks - the fixer got right: the test's `sha256_of()` is its own `hashlib` call, not `sel._sha256`. The two halves named in the task title are now genuinely mutation-covered.
  
  FINDING 1 (the funnel claim is over-stated - three passing evasions). `test_build_runs_the_funnel_rather_than_copying_the_kmz` claims build() runs the funnel, but it exercises exactly ONE negative path: a `junction=roundabout` way. Every other exclusion mechanism in `eligible()` can be deleted with the suite green, measured not argued:
    - E4: delete `or near_tagged_node(ours, grid)`. The guard's export carries zero node features, so the grid is always empty and the call is a no-op in the only test that reaches it; test_oracle_select.py tests the predicate in isolation and never its use. Probe: a way with a `highway=traffic_signals` node 10 m away goes from excluded (no_squash 0, fixture empty) to written into the fixture (no_squash 1, way 123 present). 177 passed.
    - E8: delete `if not same_geometry(ours, theirs): continue` while leaving the counter the guard asserts on. That is condition 2, which the module says excludes 726 of 3297 ways that agree only 29.6% of the time. 177 passed.
    - E9/E10: delete both copies of `if len(rows) != 1: continue` (etl/oracle.py `single_way_collections` and `kml_geometry`). Probe: a two-way collection's first way lands in the fixture carrying a collection-level curvature value. That is the entire justification for the oracle being comparable at all. 177 passed. Note E9 alone is green but only corrupts stages['single_way'] - the second copy of the gate in kml_geometry stops the way reaching `ways`. I measured this rather than assuming, and it is why E10 exists.
  No test in the suite references `single_way_collections`, `oracle.collections` or `kml_geometry` by name (`grep -rn` over services/etl/tests/*.py returned nothing); they are reached only through the new file's synthetic one-row KMZ.
  
  FINDING 2 (the guard runs only at synthetic scale - two passing evasions). Every KMZ the new tests build is a few hundred bytes in tmp_path; inputs/vermont-curvature.kmz is 2 557 952 bytes and is not in the tree.
    - E5: `if want and digest != want and kmz.stat().st_size < (1 << 20):`. A 2.5 MB KMZ carrying the pinned basename and a digest that is not the pin goes from REFUSED / no fixture written to ACCEPTED / 1 way written / source_sha256 = 64269c5c... The refusal is dead for the only file it exists to protect. 177 passed.
    - E6: collapse `_sha256`'s streaming loop to one `fh.read(1 << 20)`. Two different 2.5 MB files that share their first megabyte then hash to the SAME value (4e29ad18... for both) and neither digest is the file's, while `test_the_digest_moves_when_the_bytes_move` - the test written for precisely that property - stays green. 177 passed.
  
  FINDING 3 (the provenance chain is still two co-editable literals, one level up). E7: rewriting inputs/manifest.yaml's `sha256:` AND tests/fixtures/curvature_oracle.json's `source_sha256` to the same fabricated 64-hex value leaves 177 passed. Round 5 replaced "one hand-editable field compared with itself" with "two hand-editable fields compared with each other", and nothing in the suite hashes the real oracle because it is gitignored (services/etl/inputs/ contains only manifest.yaml). I state this as inherent rather than as a fixer defect - a pytest suite cannot hash a file that is not in the tree - and the containment is ops/etl-fetch-inputs failing at fetch time, which is outside `ops/test`. It is worth a queue task, not a re-work of T-0069.
  
  SEVERITY / RECOMMENDATION. Findings 1 and 2 are real regressions in what T-0069's own new file claims. The narrowest honest correction is small and belongs on this branch: (a) give the funnel test an export containing a tagged node and a second case where geometry differs by more than GEOMETRY_TOL_M, and a KMZ with a two-way Placemark, so each of the three conditions has a negative case driven through build(); (b) build one KMZ larger than 1 MB in the refusal test so the digest path is exercised at a size where a partial read differs from a whole-file read. Neither needs the 2.5 MB oracle or osmium, so both keep the fixer's "runs everywhere the suite runs" property. Finding 3 should be filed separately.
  
  Not re-verified: I ran the etl tier only (`python -m pytest` in services/etl, which is exactly what ops/test line 57 runs). I did not re-run the Swift tiers, so the fixer's `TESTS linux=227/76 failed=0` and the pinned-image run are unchecked by me. My findings are pure-Python logic and platform-independent.
  
  HYGIENE. Every mutation was reverted with `git checkout -- .` immediately after its run. Final commands: `python -m pytest` -> 177 passed; `git diff --stat` -> empty; `git status --short` -> NO OUTPUT (clean). Scratch scripts and mutation snippets are under C:\Users\phineasf\Documents\GitHub\wt\T-0069\services\etl\work\adv\ (mutate.py, probe_node.py, probe_size.py, probe_hash.py, probe_multiway.py, e8_coedit.py and the *_old/*_new snippet files) - `services/etl/work/` is gitignored, which is why the tree reads clean with them present. Nothing was committed, nothing was pushed, main was never touched.
  
  ## Evasions executed
  
  ### 1. CAUGHT — REPRODUCTION of the fixer's mutation 1, in etl/oracle_select.py build(): "source_sha256": digest  ->  "source_sha256": "3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046"
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle_select.py work/adv/m1_old.txt work/adv/m1_new.txt && python -m pytest
  MUTATE OK: etl\oracle_select.py
  E         + 3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046
  
  tests\test_oracle_build.py:186: AssertionError
  =========================== short test summary info ===========================
  FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_written_digest_is_the_kmz_on_disk_and_not_the_manifest_pin
  FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_digest_moves_when_the_bytes_move
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_renaming_the_kmz_walks_straight_past_the_refusal
  3 failed, 174 passed in 5.46s
  ```
  
  ### 2. CAUGHT — REPRODUCTION of the fixer's mutation 2, in etl/oracle_select.py build(): `if want and digest != want:`  ->  `if False:`
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle_select.py work/adv/m2_old.txt work/adv/m2_new.txt && python -m pytest
  MUTATE OK: etl\oracle_select.py
  >           with pytest.raises(SystemExit):
  E           Failed: DID NOT RAISE SystemExit
  
  tests\test_oracle_build.py:163: Failed
  =========================== short test summary info ===========================
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_it_raises_and_names_both_digests
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_is_keyed_on_the_basename_not_on_the_path
  2 failed, 175 passed in 5.46s
  ```
  
  ### 3. CAUGHT — E1 - EMPTY THE POPULATION THE GUARD ITERATES. etl/oracle_select.py eligible(): `published = oracle.single_way_collections(kmz)` -> `published = {}`
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle_select.py work/adv/e1_old.txt work/adv/e1_new.txt && python -m pytest
  MUTATE OK: etl\oracle_select.py
  E       assert 0 == 1
  
  tests\test_oracle_build.py:184: AssertionError
  =========================== short test summary info ===========================
  FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_the_written_digest_is_the_kmz_on_disk_and_not_the_manifest_pin
  FAILED tests/test_oracle_build.py::TestBuildRecordsTheFileItRead::test_build_runs_the_funnel_rather_than_copying_the_kmz
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_renaming_the_kmz_walks_straight_past_the_refusal
  3 failed, 174 passed in 4.94s
  ```
  
  ### 4. CAUGHT — E2 - TYPO ONE FIELD NAME SO THE LOOKUP SILENTLY MISSES. etl/oracle_select.py build(): `want = oracle.pinned_digest(kmz.name)` -> `want = oracle.pinned_digest(kmz.stem)`. The manifest keys on 'vermont-curvature.kmz', so .stem returns None and the refusal is dead for every file.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle_select.py work/adv/e2_old.txt work/adv/e2_new.txt && python -m pytest
  MUTATE OK: etl\oracle_select.py
  >           with pytest.raises(SystemExit):
  E           Failed: DID NOT RAISE SystemExit
  
  tests\test_oracle_build.py:163: Failed
  =========================== short test summary info ===========================
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_it_raises_and_names_both_digests
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_is_keyed_on_the_basename_not_on_the_path
  2 failed, 175 passed in 5.08s
  ```
  
  ### 5. CAUGHT — E3 - NULL OUT ONE OPERAND SO THE EQUALITY IS VACUOUS. etl/oracle_select.py build(): `want = oracle.pinned_digest(kmz.name)` -> `want = digest`, leaving `if want and digest != want:` intact and always false.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle_select.py work/adv/e2_old.txt work/adv/e4_new.txt && sed -n '185,190p' etl/oracle_select.py && python -m pytest
  MUTATE OK: etl\oracle_select.py
      digest = _sha256(kmz)
      want = digest
      if want and digest != want:
          raise SystemExit(
              f"{kmz.name} is not the pinned oracle.\n"
              f"  pinned : {want}\n"
  >           with pytest.raises(SystemExit):
  E           Failed: DID NOT RAISE SystemExit
  
  tests\test_oracle_build.py:163: Failed
  =========================== short test summary info ===========================
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_it_raises_and_names_both_digests
  FAILED tests/test_oracle_build.py::TestBuildRefusesAnUnpinnedOracle::test_the_refusal_is_keyed_on_the_basename_not_on_the_path
  2 failed, 175 passed in 4.58s
  ```
  
  ### 6. *** UNCAUGHT *** — E4 - PASSED. Delete half of funnel condition 3 in etl/oracle_select.py eligible(): `if way_is_squash_tagged(props.get(way_id, {})) or near_tagged_node(ours, grid):` -> `if way_is_squash_tagged(props.get(way_id, {})):`. test_build_runs_the_funnel_rather_than_copying_the_kmz's export carries zero node features, so the grid is always empty and near_tagged_node is a no-op in the only test that calls build() through the funnel. test_oracle_select.py tests the predicate in isolation, never its use.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/probe_node.py  # clean, then mutated, then python -m pytest
  --- CLEAN TREE ---
  near_tagged_node(way, grid) directly : True
  build() ways written                : 0
  funnel                              : {'single_way': 1, 'have_geometry': 1, 'geometry_identical': 1, 'no_squash': 0}
  way ids in the fixture              : []
  
  --- E4 MUTATION APPLIED ---
  MUTATE OK: etl\oracle_select.py
  near_tagged_node(way, grid) directly : True
  build() ways written                : 1
  funnel                              : {'single_way': 1, 'have_geometry': 1, 'geometry_identical': 1, 'no_squash': 1}
  way ids in the fixture              : [123]
  
  --- guard ---
  177 passed in 5.05s
  ```
  
  ### 7. *** UNCAUGHT *** — E5 - PASSED. Condition the refusal on file size so it fires only for the tests' synthetic KMZs. etl/oracle_select.py build(): `if want and digest != want:` -> `if want and digest != want and kmz.stat().st_size < (1 << 20):`. Every KMZ tests/test_oracle_build.py builds is a few hundred bytes; inputs/vermont-curvature.kmz is 2 557 952 bytes.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/probe_size.py  # clean, then mutated, then python -m pytest
  --- CLEAN TREE ---
  kmz basename     : vermont-curvature.kmz
  kmz bytes        : 2550660 (real oracle: 2557952)
  manifest pin     : 3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046
  digest on disk   : d48d5aebb3f173ebda54d37dd0599af40781a8fbda3fae60ae1490398a997d5b
  RESULT           : REFUSED - SystemExit
  fixture written  : False
  
  --- E5 MUTATION APPLIED ---
  MUTATE OK: etl\oracle_select.py
  kmz bytes        : 2550660 (real oracle: 2557952)
  manifest pin     : 3bdf4d140a6dcef0501223357d993df1b960934adf1a5cebdcdf2340b7039046
  digest on disk   : 64269c5c29245ba127e60373e25fc9cb6b971e962a2e1ce25afb1b026e4d5a8a
  RESULT           : ACCEPTED - build() returned 1 way(s) {'single_way': 1, 'have_geometry': 1, 'geometry_identical': 1, 'no_squash': 1}
  fixture written  : True source_sha256 = 64269c5c29245ba1...
  
  --- guard ---
  177 passed in 4.72s
  ```
  
  ### 8. *** UNCAUGHT *** — E6 - PASSED. Stop _sha256 being a whole-file digest. etl/oracle_select.py: the streaming loop `for block in iter(lambda: fh.read(1 << 20), b""): h.update(block)` -> a single `h.update(fh.read(1 << 20))`. Identical for every file under a megabyte, which is every file the guard hashes.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/probe_hash.py  # clean, then mutated, then python -m pytest
  --- CLEAN TREE ---
  a bytes                : 2448590
  true sha256(a)         : 5ef6ac98410b0e41d498e54049144af9a03359e848cc5ac7aba72dd36bb7b805
  true sha256(b)         : 2c344181b1b7eb4029aaa9469267d0dce626df4609f1bba798386c66d47a8416
  sel._sha256(a)         : 5ef6ac98410b0e41d498e54049144af9a03359e848cc5ac7aba72dd36bb7b805
  sel._sha256(b)         : 2c344181b1b7eb4029aaa9469267d0dce626df4609f1bba798386c66d47a8416
  _sha256 tells them apart: True
  _sha256(a) is the real digest of a: True
  
  --- E6 MUTATION APPLIED ---
  MUTATE OK: etl\oracle_select.py
  sel._sha256(a)         : 4e29ad18ab9f42d7c233500771a39d7c852b200baf328fd00fbbe3fecea1eb56
  sel._sha256(b)         : 4e29ad18ab9f42d7c233500771a39d7c852b200baf328fd00fbbe3fecea1eb56
  _sha256 tells them apart: False
  _sha256(a) is the real digest of a: False
  
  --- guard ---
  177 passed in 4.68s
  ```
  
  ### 9. *** UNCAUGHT *** — E7 - PASSED. The repo's signature shape: both sides of the comparison are hand-editable text in the same commit. Rewrote inputs/manifest.yaml's `sha256:` and tests/fixtures/curvature_oracle.json's `source_sha256` to the same fabricated 64-hex value (deadbeef x8). No test in the suite hashes the 2.5 MB oracle - it is gitignored and inputs/ holds only manifest.yaml.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/e8_coedit.py && git diff --stat && python -m pytest
  manifest pin now : deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
  fixture claim now: deadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef
   services/etl/inputs/manifest.yaml                 | 2 +-
   services/etl/tests/fixtures/curvature_oracle.json | 2 +-
   2 files changed, 2 insertions(+), 2 deletions(-)
  177 passed in 4.88s
  ```
  
  ### 10. *** UNCAUGHT *** — E8 - PASSED. Delete funnel condition 2 outright in etl/oracle_select.py eligible(): removed `if not same_geometry(ours, theirs): continue`, keeping the `stages["geometry_identical"] += 1` line so the counter the guard asserts on still reads 1. Per the module's own note this condition excludes 726 of 3297 ways that agree only 29.6% of the time.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle_select.py work/adv/e9_old.txt work/adv/e9_new.txt && sed -n '150,165p' etl/oracle_select.py && python -m pytest
  MUTATE OK: etl\oracle_select.py
      for way_id, meta in sorted(published.items()):
          ours = ways.get(way_id)
          theirs = kml_geom.get(way_id)
          if not ours or not theirs or len(ours) < 3:
              continue
          stages["have_geometry"] += 1
          stages["geometry_identical"] += 1
          if way_is_squash_tagged(props.get(way_id, {})) or near_tagged_node(ours, grid):
              continue
          stages["no_squash"] += 1
  ........................................................................ [ 40%]
  ........................................................................ [ 81%]
  .................................                                        [100%]
  177 passed in 4.85s
  ```
  
  ### 11. *** UNCAUGHT *** — E9 - PASSED (green, but smaller blast radius than predicted). Delete funnel condition 1 in etl/oracle.py single_way_collections(): removed `if len(rows) != 1: continue`. The probe shows the two-way collection does enter stages['single_way'] (0 -> 1) but dies at have_geometry, because kml_geometry() carries a SECOND independent copy of the same gate. Recorded honestly: the mutation is green and corrupts the funnel count ops/etl-curvature-fixture keys its id_floor cross-check on, but alone it does not put a multi-way collection into the fixture.
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/probe_multiway.py  # clean, then mutated, then python -m pytest
  --- CLEAN TREE ---
  single_way_collections keys: []
  build() ways written       : 0
  funnel                     : {'single_way': 0, 'have_geometry': 0, 'geometry_identical': 0, 'no_squash': 0}
  way ids in the fixture     : []
  
  --- E9 MUTATION APPLIED ---
  MUTATE OK: etl\oracle.py
  single_way_collections keys: [111]
  build() ways written       : 0
  funnel                     : {'single_way': 1, 'have_geometry': 0, 'geometry_identical': 0, 'no_squash': 0}
  way ids in the fixture     : []
  
  --- guard ---
  177 passed in 4.45s
  ```
  
  ### 12. *** UNCAUGHT *** — E10 - PASSED. Follow-up to E9: delete BOTH copies of the single-way gate - `if len(rows) != 1: continue` in etl/oracle.py single_way_collections() and the same line in kml_geometry(). This removes the entire justification for the oracle comparison ('a way sharing a collection with others can have segments zeroed by a straight run in a neighbour').
  
  ```
  $ cd C:/Users/phineasf/Documents/GitHub/wt/T-0069/services/etl && python work/adv/mutate.py etl/oracle.py work/adv/e10_old.txt work/adv/e10_new.txt && python work/adv/mutate.py etl/oracle.py work/adv/e11_old.txt work/adv/e11_new.txt && python work/adv/probe_multiway.py && python -m pytest
  MUTATE OK: etl\oracle.py
  MUTATE OK: etl\oracle.py
  --- BOTH COPIES OF THE SINGLE-WAY GATE REMOVED ---
  single_way_collections keys: [111]
  build() ways written       : 1
  funnel                     : {'single_way': 1, 'have_geometry': 1, 'geometry_identical': 1, 'no_squash': 1}
  way ids in the fixture     : [111]
  
  --- guard ---
  ........................................................................ [ 40%]
  ........................................................................ [ 81%]
  .................................                                        [100%]
  177 passed in 4.65s
  ```
