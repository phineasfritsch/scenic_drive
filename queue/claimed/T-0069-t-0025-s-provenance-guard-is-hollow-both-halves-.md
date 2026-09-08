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
