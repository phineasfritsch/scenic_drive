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
acceptance: []
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
