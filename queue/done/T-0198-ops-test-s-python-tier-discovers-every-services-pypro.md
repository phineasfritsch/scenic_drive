---
id: T-0198
title: ops/test's python tier discovers every services/*/pyproject.toml (tiles, routing) instead of services/etl alone, and the floor counts them; red first on a services/tiles test made to fail
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T06:03:54Z
lease_expires_at: 2026-10-18T06:03:54Z
worktree: .worktrees/T-0198
branch: task/T-0198
exclusive: [floors]
touches: [ops/test, ops/lib/, pins/]
pins_affected: []
reviewer: agent/rv3-t0198
depends_on: [T-0165]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 ops/test Tier 1c reads the classification table ops/lib/python-suites.txt through ops/lib/python_suites.py and runs pytest --junitxml=.artifacts/pytest-junit-<dir>.xml for every `run` row (services/etl, services/tiles, services/routing - routing's docker-routed tests self-skip where docker/image/graph/PBF are absent and still count); it prints `PYTEST services/etl=N services/tiles=N services/routing=N` naming each suite, and the suites' totals join TESTS linux=N/F"
  - "A2 WHITELIST: every services/*/pyproject.toml on disk is a `run` or an `exclude <dir> <reason>` row; an unclassified one, a row with no pyproject, a duplicate row, a malformed row or an exclude without a reason fails ops/test by name (FAIL: ... services/<dir>/pyproject.toml); a `run` suite with no report or with total=0 fails by name"
  - "A3 RED first, quoted: (a) main's ops/test with services/tiles/tests/test_tile_meta.py forced red exits 0; (b) this branch's ops/test with the same forced red exits 1 and names the test; (c) an untracked services/zz/pyproject.toml makes ops/test exit 1 naming services/zz/pyproject.toml; (d) python ops/lib/python_suites.py with a stale row, a duplicate, a reasonless exclude and a malformed row exits 1 naming each; then green. Forced reds live in the working tree only and are restored before any commit"
  - "A4 pins/floor_linux.txt ratcheted from 76 to the LOWER of the two measured totals on the final head (this box's bash ops/test and the PR's CI core job TESTS line), both lines quoted before and after; never 76+132"
  - "A5 on the final merged head: bash ops/test bare (exit 0, PYTEST and TESTS lines quoted); bare gates bash ops/check-pins --source-only, python ops/lib/check-pins-yaml.py, bash ops/lib/check-exec-bits, bash ops/lib/check-safety-disclaimer, python ops/lib/check-mutate-population.py, python ops/lib/check-mutate-only.py, bash ops/queue-check; wc -l of ops/test and ops/lib/python_suites.py under 300"
---
## Brief

From T-0165's STILL OPEN 1 and rv2-pr105's recordable: ops/test's python tier is gated on services/etl/pyproject.toml,
so the 28 services/tiles tests and services/routing's static profile tests run in no CI job - green means core +
pins-source-only. A regression in either directory is invisible to the one command the harness rests on.

## Log
- 2026-09-19T05:38:57Z filed by agent/claude-fable-5-1 from T-0165's STILL OPEN 1 (PR #109) and rv2-pr105's recordable on PR #105. Not started.
- 2026-09-19T12:44:08Z exclusive: a lock name is a SLUG, by agent/claude-fable-5-1 (05:13 panel, grounded): [pins/floor_linux.txt] -> [floors] (the name queue/LOCKS/ already uses). queue/LOCKS/floors.lock has been held by the stale claimed task T-0071 since 2026-09-08 and must be released (queue-sweep, or T-0071's owner) before this task can claim it.
- 2026-10-17T06:03:54Z claimed by agent/claude-opus-5; lease until 2026-10-18T06:03:54Z
- 2026-10-17T06:17:19Z MEASURED by agent/claude-opus-5 (owner), before any code, worktree at main cf085098:
  - `ls services/*/pyproject.toml` -> services/etl, services/routing, services/tiles (three). services/api is
    vitest (Tier 1b), services/search has no pyproject and no tests. `git ls-files '*pyproject.toml'` names no
    other pyproject anywhere in the tree.
  - ops/test Tier 1c today: `if [[ -f services/etl/pyproject.toml ]]`, one `cd services/etl && pytest
    --junitxml=.artifacts/pytest-junit.xml`; services/tiles and services/routing are run by nothing.
  - Per directory on this box, `python -m pytest -q -p no:cacheprovider --junitxml=...` then junit_count.py:
    services/etl `total=4109 failed=0 skipped=0` in 224.0 s; services/tiles `total=82 failed=0 skipped=0` in
    10.3 s; services/routing `total=50 failed=0 skipped=4` in 61.3 s.
  - services/routing detail (`-rs --durations=8`): the 4 skips are test_lambda_monotone.py:101/112/143/153 "no
    graph at services/routing/work/graph-cache". The docker-routed fixtures (test_route_details.py,
    test_route_details_fixture.py, test_scenic_score_readback.py, test_deploy_routing_rehearsal.py) RAN here
    through WSL docker because the image exists on this box: 13.40 s, 12.34 s, 10.01 s, 4.34 s, 3.95 s setups
    are the bulk of the 61 s. Each such fixture calls `pytest.skip` when docker / the image / the PBF / the
    graph is absent (test_route_details.py:57/60, test_route_details_fixture.py:76, test_scenic_score_readback.py
    :82/123/129, test_lambda_monotone.py:62/78/80).
  - Imports of tiles + routing tests and modules (stdlib, pytest, their own modules); `osmium` appears once in
    a routing tool, not in a collected test. CI core installs python3 + python3-pytest + python3-yaml only.
  - CI core job, last green linux-core on main (run 39003839635, head 1272ec4d, 2026-10-17T04:54-05:07Z, 12m52s
    for the whole job): `TESTS linux=7813/76 ios=skipped failed=0 skipped=1`. pins/floor_linux.txt = 76,
    pins/floor_ios.txt = 0.
- 2026-10-17T06:17:19Z RULINGS by agent/claude-opus-5 (owner), before any code:
  - R1 Brief vs reality: the Brief's "28 services/tiles tests" is 82 today (the directory grew after
    2026-09-19). routing has 8 test files: 4 carry docker-routed fixtures that self-skip
    (lambda_monotone, route_details, route_details_fixture, scenic_score_readback), 1 drives ops/deploy-routing
    through bash/WSL (deploy_routing_rehearsal), 3 are static (profiles_static, request_models_static,
    route_details_runs).
  - R2 Discovery is a WHITELIST, anchored on the files on disk, not on a comment: ops/lib/python-suites.txt
    holds one row per services/*/pyproject.toml, `run services/<dir>` or `exclude services/<dir> <reason>`.
    ops/lib/python_suites.py globs services/*/pyproject.toml and refuses, each by name: a pyproject with no row
    (UNCLASSIFIED), a row whose pyproject is gone (STALE), a duplicate row, a malformed row, an exclude with no
    reason. ops/test prints its FAILs and goes red but still runs every classified `run` row, so one red run
    names everything. No opt-out env var: a way to skip the tier is a way to make it green.
  - R3 services/routing is `run`, whole directory. The Brief allows ruling heavy-dep tests out; the heavy tests
    here already rule themselves out at fixture level (pytest.skip where docker, the image, the graph or the PBF
    is missing - every CI runner), so the directory needs no heavy dep to run. Picking the static files by
    name would be a second list to rot. deploy_routing_rehearsal needs bash + a POSIX filesystem, which the CI
    container has (on this box it goes through WSL and passed). Skips count in JUnit totals, so routing contributes 50 on every host.
    Cost: 61 s on this box (the routed tests actually run here), a few seconds on CI.
  - R4 Counts join: each `run` row writes .artifacts/pytest-junit-<dir>.xml (CI already uploads
    .artifacts/*.xml), which junit_count.py sums into linux total/failed/skipped and which joins junit_reports so
    a red suite is NAMED by --list-failures. A new line before TESTS: `PYTEST services/etl=N services/tiles=N
    services/routing=N` (+ `excluded=<dir>,...` when any). The TESTS line's format is unchanged. A `run` suite
    with no report or total=0 is a FAIL by name: a suite that collects nothing is not green.
  - R5 Floor. Acceptance said "ratcheted by the reviewer to include the new suites' counts". 76 + 132 = 208
    would stay green with services/tiles deleted (CI total 7813 today), so it cannot hold what this task adds.
    Ruling: the owner writes the ratchet in this PR (exclusive floors held) as the LOWER of the two measured
    totals on the final head - this box's bash ops/test and the PR's CI core job - both quoted; the reviewer's
    PASS is the ratchet's approval and re-reads the number off the CI log. Raising needs no floor-lower line.
  - R6 Old report path .artifacts/pytest-junit.xml has no reader outside ops/test (grep: only done task Logs);
    renamed to per-suite files. The `rm -f` at the top clears pytest-junit*.xml so a stale report never counts.
  - R7 Out of touches: services/tiles/pyproject.toml's comment saying the tier does not see it goes stale; it
    is a comment (nothing anchors on it) and services/ is not in touches - recorded, not edited.
- 2026-10-17T06:47:48Z RED by agent/claude-opus-5 (owner). Forced reds were working-tree only: services/tiles/tests/
  test_tile_meta.py `assert tile_meta.main(argv) == 0` -> `== 1`, and an untracked services/zz/pyproject.toml;
  both restored (`git checkout --`, `rm -r`) before this commit, `git status` clean of them.
  - (a) main's ops/test (`git show HEAD:ops/test` run as a copy, services/api deps installed with npm ci) with the
    tiles test forced red: `TESTS linux=7770/76 ios=skipped failed=0 skipped=0` / `OK` / rc=0 in 636 s - the
    defect: a red services/tiles test leaves the one command green. 7770 is also this box's BEFORE line (CI
    main's is 7813: the swift tier counts differently on Windows).
  - (b)+(c) this branch's ops/test, same forced red plus services/zz/pyproject.toml, rc=1 in 630 s:
    `FAIL: UNCLASSIFIED services/zz/pyproject.toml: add `run services/zz` or `exclude services/zz <reason>` to
    ops/lib/python-suites.txt` / `FAIL: ops/lib/python_suites.py exited 1 - classify every
    services/*/pyproject.toml in ops/lib/python-suites.txt` / `PYTEST services/etl=4109
    services/tiles=82(failed=1) services/routing=50` / `TESTS linux=7902/76 ios=skipped failed=1 skipped=4` /
    `FAIL: 1 failing test(s):` / `  - tests.test_tile_meta.test_merge_stamps_the_arguments_into_the_source_metadata
    - AssertionError: assert 0 == 1`. 7902 = 7770 + 82 + 50.
  - (d) `python ops/lib/python_suites.py --table <copy>` with a duplicate routing row, `run services/gone`,
    `exclude services/tiles` (no reason), `run`, `skip services/etl because`: rc=1 and `FAIL: ...:6: exclude
    services/tiles has no reason - an exclusion must say why` / `FAIL: ...:7: malformed row 'run'` / `FAIL:
    ...:8: malformed row 'skip services/etl because'` / `FAIL: ...: services/routing has more than one row` /
    `FAIL: STALE row in ...: services/gone/pyproject.toml does not exist`. The exclude path with a reason
    (`exclude services/routing needs the GraphHopper container`) prints `EXCLUDE services/routing needs the
    GraphHopper container` and no RUN for it. The shipped table: `RUN services/etl` / `RUN services/tiles` /
    `RUN services/routing`, rc=0.
- 2026-10-17T07:08:22Z GREEN + FLOOR + ACCEPTANCE re-run by agent/claude-opus-5 (owner), on 2042f960 merged with
  origin/main cf085098 (main had not moved; `git fetch origin` in the main checkout):
  - A1/A3 green, this box, forced reds restored: `PYTEST services/etl=4109 services/tiles=82
    services/routing=50` / `TESTS linux=7902/76 ios=skipped failed=0 skipped=4` / `OK` / rc=0 in 727 s.
  - A1 CI core job, PR #285 run 39011319158 on 2042f960 (core pass 13m1s, pins-source-only pass 6m10s):
    `PYTEST services/etl=4109 services/tiles=82 services/routing=50` / `TESTS linux=7945/76 ios=skipped
    failed=0 skipped=24` (7945 = main's 7813 + 82 + 50; skipped 1 -> 24: routing's docker-routed tests skip
    on CI and still count, as R3 ruled).
  - A4 floor: BEFORE this box 7770/76 (RED (a) run), CI 7813/76. AFTER this box 7902, CI 7945; the lower is
    7902, so pins/floor_linux.txt 76 -> 7902 (a raise; commit-msg needs no floor-lower line).
  - A5 bare `bash ops/test` with the new floor: `PYTEST services/etl=4109 services/tiles=82
    services/routing=50` / `TESTS linux=7902/7902 ios=skipped failed=0 skipped=4` / `OK` / rc=0 in 746 s.
    Gates, each bare, rc=0: check-safety-disclaimer; check-mutate-population.py `the floor of 171 holds`;
    check-mutate-only.py `NAME-PAIRS OK`; check-pins-yaml.py `PINS-YAML ok pins=52 fields=418`; check-exec-bits
    `P-OPS-01: 246 files, 23 required present, all modes correct`; queue-check `QUEUE OK (379 tasks)`.
    `timeout 600 bash ops/check-pins --source-only` returned 124 on this box (the known line-cap hang), so it
    is NOT verified locally; CI's pins-source-only job ran it and passed on 2042f960. `wc -l`: ops/test 157,
    ops/lib/python_suites.py 103, ops/lib/python-suites.txt 9.
- 2026-10-17T09:59:56Z PRE-REVIEW M3a CLOSED by agent/claude-opus-5 (owner). Finding: a services/tiles/tests/
  conftest.py that marks every collected item `pytest.mark.skip` when an import fails left ops/test green -
  junit_count.py counts skipped testcases in total, and Tier 1c's only per-suite check was total > 0, so 82
  self-skipped tiles tests held the floor and nothing named services/tiles. Is the acceptance weaker than the
  Brief: yes, in exactly this respect (a vanished optional dependency made a suite invisible); A1-A5 otherwise
  stand.
  - R8 CLASS, not spelling: "a suite's testcases count toward TESTS linux= without executing". Closed per
    suite on the JUnit report, whatever made the tests skip (conftest marker, module pytestmark, pytest.skip in
    a fixture, xfail): (i) FAIL by name when total - skipped <= 0 ("all N tests skipped - a suite that executes
    nothing is not green"); (ii) WHITELIST ceiling - every `run` row must carry `max-skipped=<N>` (no default;
    a row without it, or with -1 / 03 / trailing text, is refused by name by python_suites.py), and a suite
    reporting more skipped testcases than its ceiling FAILs by name. A skip ban was not an option: routing
    legitimately self-skips its docker/graph/PBF tests.
  - Ceilings MEASURED before they were written, per host, from the JUnit reports: this box (07:08 run)
    etl 0 / tiles 0 / routing 4; CI core run 39011319158 on 2042f960 (`gh run download`, test-reports/
    pytest-junit-*.xml through junit_count.py) etl `total=4109 failed=0 skipped=1` (test_fallback_committed's
    gitignored LA input absent), routing `total=50 failed=0 skipped=23` (lambda_monotone x4 no graph,
    route_details x6 + scenic_score_readback x10 no PBF, route_details_fixture x3 no image), tiles
    `total=82 failed=0 skipped=0`. Table: etl max-skipped=1, tiles max-skipped=0, routing max-skipped=23 (the
    max over both hosts). The PYTEST line now appends `(skipped=N)` per suite, so a skip is visible by name.
  - R9 Out of scope, recorded: Tier 1a (swift) and 1b (vitest) count skipped tests in linux_total the same
    way; this task's Brief is the python tier. Both report 0 skipped on CI today (CI total skipped 24 = etl 1 +
    routing 23).
  - MISSED, pre-fix ops/test (fix stashed, head aa76be60) with the M3a conftest planted in services/tiles/tests:
    `PYTEST services/etl=4109 services/tiles=82 services/routing=50` / `TESTS linux=7902/7902 ios=skipped
    failed=0 skipped=86` / `OK` / rc=0 in 682 s.
  - CAUGHT, this fix, same M3a conftest plus a partial mutant (`pytestmark = pytest.mark.skip` appended to
    services/etl/tests/test_assemble.py, 15 tests) so each check is seen red on its own: `FAIL: services/etl:
    15 tests skipped, over its max-skipped=1 in ops/lib/python-suites.txt` / `FAIL: services/tiles: all 82
    tests skipped - a suite that executes nothing is not green` / `FAIL: services/tiles: 82 tests skipped, over
    its max-skipped=0 in ops/lib/python-suites.txt` / `PYTEST services/etl=4109(skipped=15)
    services/tiles=82(skipped=82) services/routing=50(skipped=4)` / `TESTS linux=7902/7902 ios=skipped
    failed=0 skipped=101` / rc=1 in 1061 s. Both mutants restored (`rm`, `git checkout --`) before this commit.
  - Table refusals, `python ops/lib/python_suites.py --root <copy>` rc=1: `run services/etl` -> `...:1: run
    services/etl has no max-skipped=<N> - a run row must bound its skipped tests`; `max-skipped=-1`,
    `max-skipped=03`, `max-skipped=23 extra` -> `malformed row ...`, each also UNCLASSIFIED by name. Shipped
    table: `RUN services/etl 1` / `RUN services/tiles 0` / `RUN services/routing 23`, rc=0.
- 2026-10-17T10:30:27Z A5 re-run by agent/claude-opus-5 (owner) on c7f4ea99 = 3efffe62 merged with origin/main
  e41a7170 (`git fetch origin` in the main checkout; origin/main is an ancestor of HEAD, re-checked after the run):
  - bare `bash ops/test`, rc=1 in 970 s: `PYTEST services/etl=4109 services/tiles=82
    services/routing=50(skipped=4)` / `TESTS linux=7902/7902 ios=skipped failed=1 skipped=4` / `FAIL: 1 failing
    test(s):` / `  - the GET /config answer path (T-0288 rv3 B1) loading the shipped worker leaves every global,
    intrinsic and prototype the /config answer runs on untouched - Error: STACK_TRACE_ERROR`. That is the
    services/api vitest flake the pre-review verifier also hit on a loaded box (the gates ran concurrently); it
    is not in this diff. Alone on the same head `npx vitest run test/configAnswerPath.test.ts`: `Test Files 1
    passed (1)` / `Tests 3 passed (3)`. The python tier and floor are green; A5's "exit 0" is NOT shown on this
    box for this head and rests on the PR's CI core job.
  - Gates, each bare, rc=0: check-safety-disclaimer; check-mutate-population.py `the floor of 171 holds`;
    check-mutate-only.py `NAME-PAIRS OK`; check-pins-yaml.py `PINS-YAML ok pins=52 fields=418`;
    check-exec-bits `P-OPS-01: 246 files, 23 required present, all modes correct`; queue-check `QUEUE OK (385
    tasks)`. check-pins --source-only not re-run (124 on this box, as at 07:08); CI's pins-source-only job.
    `wc -l`: ops/test 161, ops/lib/python_suites.py 112, ops/lib/python-suites.txt 10.
- 2026-10-17T14:03:11Z ROUND 2 (rv1 B1, stale base with drift in the measured populations) by agent/claude-opus-5
  (owner). Merged origin/main 2daea62c (T-0387, T-0390, T-0392: etl test_gate_parity +3, routing
  test_deploy_routing_rehearsal +2, Worker wranglerBindings) -> 621f138a, pushed it so CI measured it, then
  origin/main 5e4150a0 (T-0391 wrangler.jsonc ROUTER_URL/GRAPH_VERSION, queue files only otherwise) -> ab1f3763.
  - R10 The ceilings and the floor are measurements over the populations main just changed, so they are re-read,
    not carried: ceilings may only stay or rise if a host now skips more; the floor may only rise.
  - MEASURED, this box, bare `bash ops/test` on 621f138a, rc=0 in 1581 s: `PYTEST services/etl=4112
    services/tiles=82 services/routing=52(skipped=4)` / `TESTS linux=7910/7902 ios=skipped failed=0 skipped=4` /
    `OK`.
  - MEASURED, CI core job, PR #285 run 39029933315 on 621f138a (core pass 12m45s, pins-source-only pass 5m14s):
    `PYTEST services/etl=4112(skipped=1) services/tiles=82 services/routing=52(skipped=23)` / `TESTS
    linux=7953/7902 ios=skipped failed=0 skipped=24` / `OK`.
  - Ceilings: the max skipped over both hosts is etl 1 (CI) / tiles 0 / routing 23 (CI) - unchanged, so
    ops/lib/python-suites.txt is not edited. The two new rehearsal tests run (not skip) on both hosts.
  - A4 floor: BEFORE 7902 (this box 7902, CI 7945 on 2042f960). AFTER this box 7910, CI 7953; the lower is 7910,
    so pins/floor_linux.txt 7902 -> 7910 (a raise).
  - M3a re-confirmed on the merged head (fm's note): services/tiles/tests/conftest.py planted, its
    pytest_collection_modifyitems adding pytest.mark.skip to every item, floor 7910 in the working tree; bare
    `bash ops/test` rc=1 in 2074 s: `FAIL: services/tiles: all 82 tests skipped - a suite that executes nothing is
    not green` / `FAIL: services/tiles: 82 tests skipped, over its max-skipped=0 in ops/lib/python-suites.txt` /
    `PYTEST services/etl=4112 services/tiles=82(skipped=82) services/routing=52(skipped=4)` / `TESTS
    linux=7910/7910 ios=skipped failed=0 skipped=86`. The floor alone holds at 7910/7910 - only the per-row
    max-skipped and executed>0 checks name tiles, which is the mechanism. conftest removed (`rm`, __pycache__
    purged) before this commit; `git status` showed only pins/floor_linux.txt modified.
  - A5 on ab1f3763 with floor 7910, this box, bare `bash ops/test` twice, both rc=1 on services/api vitest
    STACK_TRACE_ERROR timeouts (no services/api file is in this diff; the box is loaded): run 1 in 1550 s
    `PYTEST services/etl=4112 services/tiles=82 services/routing=52(skipped=4)` / `TESTS linux=7896/7910
    ios=skipped failed=3 skipped=4` (authAppleFields, configAnswerPath, planCost: vitest reported 2676 tests, 14
    fewer, after the timeouts); run 2 in 675 s `PYTEST services/etl=4112 services/tiles=82
    services/routing=52(skipped=4)` / `TESTS linux=7910/7910 ios=skipped failed=1 skipped=4` (waitlist T-0296).
    Alone, `npx vitest run` on ab1f3763: `Tests 1 failed | 2689 passed (2690)`, the failure configAnswerPath at
    5017ms (the 5 s timeout); `npx vitest run test/configAnswerPath.test.ts test/sessionIdentity.test.ts`:
    `Tests 43 passed (43)`. The python tier and the floor are green on this box; "exit 0" is NOT shown on this box
    for this head and rests on the PR's CI core job on the pushed head.
  - `wc -l`: ops/test 161, ops/lib/python_suites.py 112, ops/lib/python-suites.txt 10.
- 2026-10-17T16:46:50Z ROUND 3 (rv2 FAIL: stale base with code drift in the measured populations) by
  agent/claude-opus-5 (owner). `git fetch origin` in the main checkout; merged origin/main efbb58e9 (T-0196
  services/tiles tests incl. test_publish_upload_keys.py + test_basemap_assets.py, T-0394 APIBaseURL Swift +
  tests, T-0393 services/etl seedplaces tests, T-0400/T-0401 filings) into b9a43ae6 -> cd0329dd, pushed it so CI
  measured the same head. Per R10 the ceilings and the floor are re-read, not carried.
  - MEASURED, this box, bare `bash ops/test` on cd0329dd, rc=0 in 1017 s: `PYTEST services/etl=4160(skipped=1)
    services/tiles=112 services/routing=52(skipped=4)` / `RO-GRAMMAR OK 30 cases` / `TESTS linux=7998/7910
    ios=skipped failed=0 skipped=5` / `OK`. No vitest flake this run.
  - MEASURED, CI core job, PR #285 run 39048522577 on cd0329dd (core pass 13m13s, pins-source-only pass 5m39s):
    `PYTEST services/etl=4160(skipped=1) services/tiles=112 services/routing=52(skipped=23)` / `RO-GRAMMAR OK 30
    cases` / `TESTS linux=8041/7910 ios=skipped failed=0 skipped=24` / `OK`; queue-check `QUEUE OK (391 tasks)`.
  - The new services/tiles tests (82 -> 112) skip on NEITHER host: tiles skipped=0 on both, ceiling 0 holds.
  - This box's etl skip is new (was 0): from .artifacts/pytest-junit-etl.xml, tests.test_seedplaces
    `test_every_out_state_exits_0_or_2_with_exact_output_and_whole_tree[dir-with-a-symlink]` - `cannot create a
    symlink here: [WinError 1314] A required privilege is not held by the client`. CI's etl skip stays 1
    (test_fallback_committed). Max skipped over both hosts: etl 1 / tiles 0 / routing 23 - equal to the table, so
    ops/lib/python-suites.txt is not edited (a ceiling rises only when a host skips more than it allows).
  - A4 floor: BEFORE 7910 (both hosts above it: 7998 / 8041). The lower total is 7998 (this box), so
    pins/floor_linux.txt 7910 -> 7998 (a raise; never to 8041, never lowered).
  - Gates on cd0329dd, each bare, rc=0: check-safety-disclaimer (P-SAFE-03 ... `Not checked here: rendering
    (T-0180), taps, whether that write RUNS, contrast, Dynamic Type, 44 pt.`); check-mutate-population.py
    `P-PROC-06: 391 modules, 221 covered by 50 populations, 150 allowlisted, 0 added by this branch` / `P-PROC-06:
    every added module is covered or allowlisted; the floor of 173 holds`; check-mutate-only.py `MUTATE-ONLY OK:
    248 of 248 driver runs refused with exit 64 (67 drivers, 114 range probes: 25 digit, 47 name, 42 N-(N+1))` /
    `NAME-PAIRS OK: 242318 pair tokens over 50 id populations, each refused in process by select_only in 4 modes
    and by onlyIds (0 calls not refused, floor 201117 tokens)`; check-pins-yaml.py `PINS-YAML ok pins=53
    fields=426`; check-exec-bits `P-OPS-01: 252 files, 23 required present, all modes correct`; queue-check
    `QUEUE OK (391 tasks)`. check-pins --source-only: CI's pins-source-only job (pass 5m39s above).
  - `wc -l`: ops/test 161, ops/lib/python_suites.py 112, ops/lib/python-suites.txt 10.
- 2026-10-17T17:08:15Z ROUND 3 confirmation on d41ca50d (floor 7998) by agent/claude-opus-5 (owner).
  - CI core job, PR #285 run 39051036963 on d41ca50d (core pass 8m32s, pins-source-only pass 5m31s): `PYTEST
    services/etl=4160(skipped=1) services/tiles=112 services/routing=52(skipped=23)` / `TESTS linux=8041/7998
    ios=skipped failed=0 skipped=24` / `OK`.
  - This box, bare `bash ops/test` on d41ca50d, rc=1 in 600 s: `PYTEST services/etl=4160(skipped=1)
    services/tiles=112 services/routing=52(skipped=4)` / `TESTS linux=7998/7998 ios=skipped failed=1 skipped=5` /
    `FAIL: 1 failing test(s):` / `  - the GET /config answer path (T-0288 rv3 B1) loading the shipped worker
    leaves every global, intrinsic and prototype the /config answer runs on untouched - Error:
    STACK_TRACE_ERROR` - the known services/api vitest timeout under load (no services/api file in this diff).
    Alone, `npx vitest run test/configAnswerPath.test.ts`: `Test Files  1 passed (1)` / `Tests  3 passed (3)`.
    The python tier and the floor (7998/7998) are green on this box; "exit 0" on d41ca50d rests on CI's core job
    (the same head's cd0329dd run above was rc=0 on this box).
  - Last step: `git fetch origin` in the main checkout; origin/main had moved to 8444fbc8, `git diff --name-only
    efbb58e9 8444fbc8` = queue/ only (prod.lock, T-0395 claimed -> done, T-0402/T-0403 filings). Outside every
    measured population, so merged without re-measuring.
- 2026-10-17T17:22:13Z REVIEW ROUND 3 (ancestry/CI/gates) by agent/rv3-t0198 (not the owner): PASS. rv2 passed the
  content and failed only on ancestry; this round checks that alone, on head fc44e345.
  - `git fetch origin` in the main checkout: origin/main 8444fbc8, origin/task/T-0198 fc44e345 (== PR #285 head,
    base main, MERGEABLE). `git merge-base --is-ancestor origin/main origin/task/T-0198` exit 0. Drift since the
    measured head d41ca50d is queue/ only (prod.lock, T-0395 claimed -> done, T-0402/T-0403 filings, this file).
  - Floor not lowered: `git diff origin/main origin/task/T-0198 -- pins/floor_linux.txt` = `-76` / `+7998`.
  - CI core run 39052544602 on fc44e345 (core success, pins-source-only success): `PYTEST
    services/etl=4160(skipped=1) services/tiles=112 services/routing=52(skipped=23)` / `TESTS linux=8041/7998
    ios=skipped failed=0 skipped=24` / `OK`. Each skip count is within ops/lib/python-suites.txt (etl max-skipped=1,
    tiles 0, routing 23); 8041 >= floor 7998. Run 39051036963 on d41ca50d shows the same three lines.
  - Bare gates in detached worktree .worktrees/rv3-t0198 at fc44e345, all exit 0: check-safety-disclaimer (P-SAFE-03
    report, exit 0); check-mutate-population `the floor of 173 holds`; check-mutate-only `MUTATE-ONLY OK: 248 of 248`
    and `NAME-PAIRS OK`; check-pins-yaml `PINS-YAML ok pins=53 fields=426`; check-exec-bits `P-OPS-01: 252 files,
    23 required present, all modes correct`; queue-check `QUEUE OK (391 tasks)`.
  - Recorded, not blocking: this box's bare ops/test on d41ca50d exited 1 on the services/api vitest flake
    (configAnswerPath STACK_TRACE_ERROR), no services/api file in this diff; the python tier and floor were green.
  - floors.lock released; queue/claimed/ -> queue/done/.
