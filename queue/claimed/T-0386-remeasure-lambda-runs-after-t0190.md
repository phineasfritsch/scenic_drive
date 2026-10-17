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
  - "(3) RED BY NAME, THEN GREEN. Mutant (amended 2026-10-17T04:31:52Z, see Log): the recorded lambda-2.json written into the routed models under the names lambda-4.json AND lambda-8.json (Tests/Fixtures/custom-model/lambda-4.json and lambda-8.json overwritten with lambda-2.json's bytes in the worktree, restored with git checkout after) - a penalty that saturates at lambda 2, so T(lambda) stays non-decreasing. With BITE_FLOOR 0.05 (main) test_lambda_penalty_bites PASSES on it (the old floor's miss); with 0.18 it FAILS by name; on the real record all of test_lambda_monotone.py and test_route_details.py pass (9 passed), printing the stage-1 T(lambda) line byte-equal."
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
