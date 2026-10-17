---
id: T-0198
title: ops/test's python tier discovers every services/*/pyproject.toml (tiles, routing) instead of services/etl alone, and the floor counts them; red first on a services/tiles test made to fail
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T06:03:54Z
lease_expires_at: 2026-10-18T06:03:54Z
worktree: .worktrees/T-0198
branch: task/T-0198
exclusive: [floors]
touches: [ops/test, ops/lib/, pins/]
pins_affected: []
reviewer: null
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
