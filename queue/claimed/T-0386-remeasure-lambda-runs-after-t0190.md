---
id: T-0386
title: Re-measure the routed lambda runs (test_lambda_monotone BITE_FLOOR, test_route_details lambda-8) against the models production now sends
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T04:12:32Z
lease_expires_at: 2026-10-18T04:12:32Z
worktree: .worktrees/T-0386
branch: task/T-0386
exclusive: []
touches: [services/routing/tests/, services/routing/measure_runs.py, Tests/Fixtures/custom-model/]
pins_affected: [P-PROD-01]
reviewer: null
depends_on: [T-0190]
verify: [ops/test, ops/check-pins]
acceptance:
  - "(1) MEASURED, QUOTED. The Log quotes the routed numbers on the T-0190 models with the graph hash (Vermont graph-cache file sha256s and both source PBF sha256s), the images, the command and its count line: Vermont T(lambda) = 5945246, 6015807, 6785536, 7510022, 8122353 ms (+36.6193 %); LA loop pair lambda-8 2522680 ms / 36576.6 m against car_fast 1449345 ms / 23971.0 m (+74.0566 %); T-0209's 3x3 grid 28 of 36 routed, lambda-0 == car_fast on 24, lambda-8 slower on 25."
  - "(2) THE FLOOR IS RULED FROM THE MEASUREMENT. test_lambda_monotone.BITE_FLOOR = 0.18 (R3: half the measured +36.6193 %, rounded down); its docstring quotes 5945246 -> 8122353 ms and no longer says UNVERIFIED. test_route_details quotes 2522680 ms and the stage-2 grid counts. `grep -rn -E '8491177|2515815|UNVERIFIED since T-0190|every one with lambda-0 == car_fast' services/routing/tests` prints nothing."
  - "(3) RED BY NAME, THEN GREEN. Mutant (amended 2026-10-17T04:31:52Z, see Log): the recorded lambda-2.json written into the routed models under the names lambda-4.json AND lambda-8.json (Tests/Fixtures/custom-model/lambda-4.json and lambda-8.json overwritten with lambda-2.json's bytes in the worktree, restored with git checkout after) - a penalty that saturates at lambda 2, so T(lambda) stays non-decreasing. With BITE_FLOOR 0.05 (main) test_lambda_penalty_bites PASSES on it (the old floor's miss); with 0.18 it FAILS by name; on the real record all of test_lambda_monotone.py and test_route_details.py pass (9 passed; 11 since the pre-review close of 2026-10-17T04:58:42Z, which added two tests to test_lambda_monotone.py), printing the stage-1 T(lambda) line byte-equal."
  - "(5) PRE-REVIEW CLOSE (added 2026-10-17T04:58:42Z, see Log). Mutant A, write_models writing lambda-4's record under the lambda-8 label (`recorded(4 if value == 8 else value)` in request_models.write_models): on the test files before the close test_request_models_static.py passes (MISSED); after, test_request_models_static.py::test_write_models_writes_each_label_its_own_record_bytes and test_lambda_monotone.py::test_lambda_durations_are_the_measured_record FAIL by name. Mutant B, BITE_FLOOR = 0.10: test_lambda_monotone.py passes before the close (MISSED); after, test_lambda_monotone.py::test_bite_floor_is_ruled_from_the_measured_record FAILS by name. On the real record test_lambda_monotone.py, test_route_details.py and test_request_models_static.py pass (18 passed)."
  - "(4) GATES at the final commit, on the merged head: services/routing pytest count line; bash ops/lib/check-safety-disclaimer, python ops/lib/check-mutate-population.py, python ops/lib/check-mutate-only.py, python ops/lib/check-pins-yaml.py, bash ops/lib/check-exec-bits, bash ops/queue-check, each run bare and quoted."
---
## Brief

T-0190 (PR #279) made the shipped Worker builder the only source of the request models: 9 clauses, distance_influence 0, the T-0244 minor clause and new band slopes. The routed numbers recorded before it (test_lambda_monotone's five T(lambda) durations and BITE_FLOOR's measured +43%, test_route_details' lambda-8 2515815 ms) were measured with the old 3-clause template and are stale.

Run the LA GraphHopper container (WSL docker, the committed LA graph build; no VPS, no deploy), route the recorded pairs with Tests/Fixtures/custom-model/lambda-*.json through services/routing/request_models, quote every number in the Log, then rule the new floors from the measured population (never a typed guess). Record the graph hash. If the container cannot run on this box, file the measurement as unverified and stop.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from T-0190 stillOpen 1.
- 2026-10-17T04:12:32Z claimed by agent/claude-opus-5; lease until 2026-10-18T04:12:32Z
- 2026-10-17T04:22:55Z MEASURE, stage 1 (agent/claude-opus-5, worktree HEAD f712f37c). Inputs already on the box,
  nothing downloaded, no VPS, no deploy; docker through WSL. Images: `scenic-routing:t0213` (ff123b2f85b3, the image
  test_lambda_monotone names) and `scenic-routing:t0209` (349ad6f584a1, test_route_details' default). Models: the
  recorded Worker bytes, written by request_models.write_models from Tests/Fixtures/custom-model (T-0190, unchanged).
  - Vermont graph (test_lambda_monotone's): main checkout services/routing/work/graph-cache, imported
    2026-09-19T02:06:19Z (properties.txt `datareader.import.date`), copied into this worktree's gitignored work/ and
    `sha256sum -c` OK after the copy. sha256: edges 2c38ea99f3a820620f6eac1a3fc3d55cbd716a75f0fb29b4e1d844c9d12f91da,
    nodes 8b7734435ace593dba04580730c9511b35cee61defd065eba6af12d1c2904605, geometry
    c29d66849018da1b315b27023c169f16610bae107522f2c31837ead01a2a960f, properties
    4fac894c8aec6d27e334867c4f67c993cf3686065d601820828f264ea58ddbd6, location_index
    95cb59f3e6c24293c6ae395c7e29157e78a6c19972cff3c019d60d554aa7dfbc, edgekv_keys
    f7eae39c3b770cf51ba891d2d204179e4d9681fae4e364d1cfbeb9c3c7db4e5f, edgekv_vals
    818866317d85dae426e04c97d499d5b85dc437259a0eeec6fa70bf5f86ce0cbd. Its source PBF
    services/routing/work/vermont-scenic.osm.pbf sha256 0f058ac6999d0f2bb99035bd7ce253ece7041218e841ba6a8f4296ced049d077.
  - LA canyon window (test_route_details'): services/etl/work/la/window-tagged-1.osm.pbf sha256
    06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090 (== test_scenic_score_readback.PBF_SHA256); the
    test imports its own graph from it with the image under test, so there is no pre-built LA graph to hash.
  - Command: `SCENIC_ROUTING_PBF=<main>/services/etl/work/la/window-tagged-1.osm.pbf python -m pytest -q -p
    no:cacheprovider -o addopts= -s test_lambda_monotone.py test_route_details.py` (services/routing/tests),
    04:19:10Z -> 04:20:01Z, `9 passed in 48.77s`, exit 0. Lines it printed, verbatim:
    `T(lambda) ms: lambda=0: 5945246, lambda=1: 6015807, lambda=2: 6785536, lambda=4: 7510022, lambda=8: 8122353`
    `car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m`
    typed pair 34.0387,-118.5836 -> 34.0938,-118.6045: car_fast, lambda-0.json and lambda-8.json all
    `time_ms=526739 distance_m=8230.4`
    loop pair 34.0366,-118.7401 -> 34.0875,-118.6044: `ROUTE profile=car_fast model=- time_ms=1449345
    distance_m=23971.0`, `model=lambda-0.json time_ms=1449345 distance_m=23971.0`, `model=lambda-8.json
    time_ms=2522680 distance_m=36576.6`
  - Derived: Vermont T(lambda)/T(0) = +0, +1.1868 %, +14.1338 %, +26.3198 %, +36.6193 %; steps +70561, +769729,
    +724486, +612331 ms (every step strictly rises). Old 3-clause record was 5945246 -> 8491177 (+42.8230 %): lambda=0
    is byte-identical in time, lambda=8 is 368824 ms shorter under the 9-clause model. LA loop lambda-8 +74.0566 %
    (old record 2515815 ms, +73.5829 %): 6865 ms longer. The typed pair is unchanged (526739 / 8230.4 for all three,
    as before).
- 2026-10-17T04:29:29Z MEASURE, stage 2: test_route_details' loop-pair comment also quotes a POPULATION ("a 3x3 grid
  inside the window's import bounds, 28 of 36 pairs routed, every one with lambda-0 == car_fast and 20 with lambda-8
  slower"), measured by T-0209 on the old template. Re-routed with a gitignored scratch driver
  (services/routing/work/t0386/measure_grid.py: request_models.write_models((0, 8)), the t0209 image importing the
  window itself, `--mode route` per unordered pair of a 3x3 grid at fractions 0.2/0.5/0.8 of the import bounds -
  T-0209's grid: IMPORT bounds -118.9663074,-118.5138948,34.0026669,34.172355; points lat 34.0366/34.0875/34.1384 x
  lon -118.8758/-118.7401/-118.6044, which reproduces the loop pair). Count lines, verbatim: `GRID routed=28 of 36
  l8_slower=25`, `exit=0`, 8 pairs `exit=1` (the same 28/8 split as T-0209). From the PAIR lines: lambda-0 == car_fast
  on 24 of 28; on 4 lambda-0 is FASTER than car_fast - 34.0366,-118.7401 -> 34.1384,-118.8758 (1899294 vs 1899371
  ms), 34.0875,-118.8758 -> 34.0875,-118.6044 (2474921 vs 2504511), 34.1384,-118.7401 -> 34.1384,-118.6044 (1719585
  vs 1727424), and in the quartile grid (0.25/0.5/0.75, first run, 21 of 36 routed, l8_slower=17)
  34.0875,-118.8532 -> 34.1299,-118.8532 (1236965 vs 1245718) and 34.0451,-118.7401 -> 34.1299,-118.8532 (2247942 vs
  2248019). lambda-8 equal to car_fast on 3 of 28 (spread +0.00 %); smallest positive spread +0.20 %; the loop pair
  is +74.06 %, the largest +187.26 %.
- 2026-10-17T04:29:29Z RULINGS (before any code).
  - R1 (Brief vs code): the Brief says "the LA GraphHopper container ... the committed LA graph build". Reality:
    test_lambda_monotone's pair is in VERMONT (FROM_POINT 44.4759,-73.2121, a graph at services/routing/work/
    graph-cache), and test_route_details imports its own LA graph from the sha-pinned canyon window; no graph is
    committed (services/routing/.gitignore: work/). Ruled: each floor is re-measured on the fixture its test asserts
    on - Vermont for BITE_FLOOR, the LA window for lambda-8 - with that test's own image. Graph hashes above.
  - R2 (which image): T-0190 changed the per-request MODELS, not the image; both tests name their image
    (t0213, t0209) and were measured with it. The newer T-0381 profile (image scenic-routing:t0381) is in neither
    test and is not re-measured here; recorded in stillOpen.
  - R3 (BITE_FLOOR): measured bite +36.6193 % (5945246 -> 8122353 ms) on a deterministic router over a fixed graph and
    fixed model bytes. Ruled BITE_FLOOR = 0.18: half the measured bite, rounded DOWN to two places (0.1831 -> 0.18).
    The old 0.05 was "an order of magnitude below" a +43 % measurement and passes a model that bites at a third of
    the measured strength: lambda-2's recorded model routed under lambda-8's label is +14.1338 % on this pair (stage
    1), above 0.05 and below 0.18. Half leaves 2x headroom under the measurement and refuses a model whose bite has
    halved.
  - R4 (step rises): every one of the four steps rises (min +70561 ms, +1.19 % at 0 -> 1). Declined to tighten
    "at least one step rises" to "every step rises": the plan's property is non-decreasing, and the 0 -> 1 step is a
    near-tie no floor here was asked for.
  - R5 (test_route_details): the loop assertion stays `lambda-8 > car_fast` (it checks that each model file is
    routed under its own label, not a bite size). The quoted number becomes 2522680 ms (+74.06 %) and the grid
    sentence becomes the stage-2 counts (28 of 36 routed, lambda-0 == car_fast on 24, lambda-8 slower on 25).
  - R6 (lambda-0 != car_fast on 4 LA pairs): a real finding, out of this task's scope (touches are tests only). The
    models carry distance_influence 0 and car_scenic_base.json 30, so lambda-0 optimises pure time and can beat
    car_fast; test_lambda_zero_is_the_car_fast_route holds on the Vermont pair only. Not a ceiling breach (lambda-0
    is faster, never slower). Recorded in stillOpen for a follow-up task; no test here is changed to hide it.
  - R7 (touches): `services/routing/measure_runs.py` does not exist; the file is services/routing/tests/
    measure_runs.py (inside services/routing/tests/, already in touches). It quotes only T-0213/T-0224 numbers and
    is not changed. Tests/Fixtures/custom-model/ is not changed (the record is T-0190's, held by the vitest).
- 2026-10-17T04:29:29Z ACCEPTANCE written (frontmatter), before code.
- 2026-10-17T04:31:52Z RED, THEN GREEN (acceptance 3).
  - Mutant as first written (lambda-2's bytes as lambda-8.json only), BITE_FLOOR 0.05: `FAILED
    test_lambda_monotone.py::test_lambda_monotone_non_decreasing` (`assert 6785536 >= 7510022`), `1 failed, 2 passed
    in 5.40s` - the MONOTONE test catches it, so it does not isolate the floor. Acceptance (3)'s mutant amended to
    lambda-2's bytes as lambda-4.json AND lambda-8.json (a penalty that saturates at lambda 2, still non-decreasing).
  - Amended mutant, BITE_FLOOR 0.05 (main's): `T(lambda) ms: lambda=0: 5945246, lambda=1: 6015807, lambda=2:
    6785536, lambda=4: 6785536, lambda=8: 6785536`, `3 passed in 4.71s` - the old floor MISSES it.
  - BITE_FLOOR 0.18, same mutant, 04:31:15Z: `FAILED test_lambda_monotone.py::test_lambda_penalty_bites -
    AssertionError: the scenic penalty does not BITE: lambda=8 is 6785536 ms against lambda=0 at 5945246 ms, short of
    the +18% (7015390 ms) this asserts.`, `1 failed, 2 passed in 5.59s`. Fixtures restored (`git checkout --`,
    `git status --short Tests/` empty).
  - GREEN on the real record, 04:31:30Z (SCENIC_ROUTING_PBF set): `T(lambda) ms: lambda=0: 5945246, lambda=1:
    6015807, lambda=2: 6785536, lambda=4: 7510022, lambda=8: 8122353` (byte-equal to stage 1), loop lambda-8
    `time_ms=2522680 distance_m=36576.6`, `9 passed in 21.38s`. Whole services/routing pytest: `46 passed in 46.24s`.
  - Acceptance (2) grep: no output, exit 1. `wc -l`: test_lambda_monotone.py 144, test_route_details.py 175.
- 2026-10-17T04:36:57Z FINAL (acceptance 1-4 re-quoted). `git fetch origin` in the main checkout; origin/main is
  f712f37c, already an ancestor of task/T-0386 (`git merge-base --is-ancestor` exit 0), so the merge is a no-op and
  the head measured at 04:31:30Z (b02b1a9c, code unchanged since) is the merged head. (1) stage 1/2 entries above;
  (2) grep empty, BITE_FLOOR 0.18; (3) red/green above: `9 passed in 21.38s`, services/routing `46 passed in
  46.24s`. (4) gates, each bare, exit 0: check-safety-disclaimer 0; check-mutate-population.py 0 (`P-PROC-06: every
  added module is covered or allowlisted; the floor of 171 holds`); check-mutate-only.py 0 (`NAME-PAIRS OK: 238997
  pair tokens over 48 id populations`); check-pins-yaml.py 0 (`PINS-YAML ok pins=52 fields=418`); check-exec-bits 0
  (`P-OPS-01: 244 files, 23 required present, all modes correct`); queue-check 0 (`QUEUE OK (379 tasks)`).
- 2026-10-17T04:58:42Z PRE-REVIEW CLOSE (fable verifier: two mutants survived). Each closed by CLASS, MISSED then
  CAUGHT by name; mutants applied with sed in the worktree, restored with `git checkout --`, __pycache__ purged and a
  1.1 s python sleep between runs.
  - Class A (BLOCKING): the routed models directory is not byte-equal, label by label, to the record - a swap, a drop,
    an extra or a stale file. The verifier's instance, `recorded(4 if value == 8 else value)` in write_models, routes
    lambda=8 at 7510022 ms (+26.32 %), above the 0.18 floor, so no test saw it. Closed twice: (i) docker-free,
    test_request_models_static.py::test_write_models_writes_each_label_its_own_record_bytes calls the shipping
    write_models for both label sets the routed tests pass ((0,1,2,4,8) and (0,8)) into a directory holding a stale
    lambda-3.json, and holds the result by full equality - exactly the asked names, each byte-equal to
    Tests/Fixtures/custom-model/lambda-<l>.json read directly, not through recorded() - plus
    test_the_oracle_records_are_pairwise_distinct (a swap between equal records would be invisible); (ii) routed,
    test_lambda_monotone.py::test_lambda_durations_are_the_measured_record holds the five routed durations equal to
    MEASURED_T_MS = (5945246, 6015807, 6785536, 7510022, 8122353), the stage-1 measurement.
    MISSED, 04:54:49Z, mutant on the pre-close tests: test_request_models_static.py `5 passed in 0.25s`.
    CAUGHT, 04:56:10Z, same mutant: `FAILED test_request_models_static.py::test_write_models_writes_each_label_its_own_record_bytes`,
    `FAILED test_lambda_monotone.py::test_lambda_durations_are_the_measured_record` (`AssertionError: T(lambda) over
    [0, 1, 2, 4, 8] is (5945246, 6015807, 6785536, 7510022, 7510022) ms, not the measured (5945246, 6015807, 6785536,
    7510022, 8122353)`), `2 failed, 10 passed in 8.44s`.
  - Class B: BITE_FLOOR typed below the R3 rule, re-opening the lambda-2 saturation gap (verifier: 0.10 passed the
    whole suite). Ruling on the verifier's "a floor literal cannot guard itself": the floor is now bound to a value
    the router produces rather than to prose. test_bite_floor_is_ruled_from_the_measured_record (docker-free) asserts
    BITE_FLOOR == floor(50 * (T8/T0 - 1)) / 100 over MEASURED_T_MS (= 0.18) and lambda-2-saturation bite (+14.13 %)
    < BITE_FLOOR < measured bite (+36.62 %); MEASURED_T_MS is in turn held to the routed output by
    test_lambda_durations_are_the_measured_record. The residual: an edit that changes BITE_FLOOR, MEASURED_T_MS and
    the routed graph together - which is a re-measurement, the thing R3 asks for.
    MISSED, 04:54:57Z, BITE_FLOOR = 0.10 on the pre-close tests: test_lambda_monotone.py `3 passed in 9.12s`.
    CAUGHT, 04:56:26Z: `FAILED test_lambda_monotone.py::test_bite_floor_is_ruled_from_the_measured_record`,
    `1 failed, 4 passed in 7.99s`. Restored (`BITE_FLOOR = 0.18`).
  - Ruled: the acceptance (3) mutant (lambda-2 at labels 4 and 8) now also fails
    test_lambda_durations_are_the_measured_record; test_lambda_penalty_bites still fails it by name at 0.18 and passes
    it at 0.05, so (3) stands as written. The new equality test means a re-recorded custom-model fixture or a new
    image fails the routed run until T(lambda) is re-measured - intended (this task exists because the numbers went
    stale silently).
  - GREEN on the real record, 04:56:52Z (SCENIC_ROUTING_PBF=<main>/services/etl/work/la/window-tagged-1.osm.pbf):
    test_lambda_monotone.py + test_route_details.py + test_request_models_static.py `18 passed in 34.22s`; whole
    services/routing pytest `50 passed in 70.22s`. `wc -l`: test_lambda_monotone.py 174, test_request_models_static.py
    152, test_route_details.py 175.
- 2026-10-17T05:01:30Z FINAL after the pre-review close (acceptance 1-5 re-quoted). `git fetch origin` in the main
  checkout; origin/main 1272ec4d merged into task/T-0386 (b7a91073, clean). On the merged head, 05:00:23Z: whole
  services/routing pytest `50 passed in 46.88s`; (1) and (2) unchanged since 04:36:57Z (grep re-run empty: the close
  adds no stale number); (3) and (5) red/green in the 04:58:42Z entry. (4) gates, each bare, exit 0:
  check-safety-disclaimer 0; check-mutate-population.py 0 (`P-PROC-06: every added module is covered or allowlisted;
  the floor of 171 holds`); check-mutate-only.py 0 (`NAME-PAIRS OK: 239389 pair tokens over 48 id populations`);
  check-pins-yaml.py 0 (`PINS-YAML ok pins=52 fields=418`); check-exec-bits 0 (`P-OPS-01: 244 files, 23 required
  present, all modes correct`); queue-check 0 (`QUEUE OK (379 tasks)`).
