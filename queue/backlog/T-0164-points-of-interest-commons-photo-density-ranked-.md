---
id: T-0164
title: points_of_interest - Commons geocoded photo density, ranked within 50 km, top decile penalised
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/photodensity.py, services/etl/tests/test_photodensity.py, services/etl/tests/fixtures/, services/etl/inputs/manifest.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0163]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The one scorer term that needs the network and its OWN normaliser. plan:57 names Wikimedia Commons geocoded
photo COUNTS as a signal (no images redistributed - LICENSE-DATA already says so); plan:89 says "Commons photo
density rank-normalized in 50 km, top decile penalized" - a local rank, not the region rank T-0163 builds, and
with a penalty at the top (the most-photographed places are crowded, not scenic-to-drive). `score.py` takes it
as `points_of_interest` in 0..1. Until this lands, T-0163's record carries the term as an explicit
`None -> 0.0 with a flag`.

Rule in the Log before code: the query (Commons GeoData API vs a dump), the cell size, the cache (fetched
inputs are manifest-pinned with a sha256 - `services/etl/inputs/manifest.yaml`; a live API is not pinnable, so
say what IS pinned), what "penalized" means numerically (the plan does not say), and how a 50 km window behaves
at the region's edge. Fixture-driven tests with typed-out expectations; no test touches the network.

## Log
- 2026-09-18T19:52:17Z filed by agent/claude-fable-5-1 from the 13:13 panel's grounded synthesis. Not started.
- 2026-09-25T23:46:40Z MEASURED by the Commons probe (agent/claude-opus-5 orchestrator, .artifacts/data-probe/commons/): over the 11,740 canyon-window ways 81% are zero; the owner's 8 good back roads carry 1.08 photos/km against 3.20 on the 4 busy scenic highways (PCH top, Encinal zero), so as the positive points_of_interest term it points the WRONG way; road class alone separates the 12 roads, so an inverted crowding penalty adds nothing. Not to be built as a score term; the E slot goes to T-0240 (quietness) if the owner clears its licensing.
