# Scenic Drive

Plans enjoyable drives, not fast ones. iOS (SwiftUI) on a fully open stack: MapLibre + Protomaps tiles,
self-hosted GraphHopper with a derived scenic score, Ferrostar turn-by-turn, Cloudflare Workers backend.

Agents: read `CLAUDE.md`, then run `ops/agent-preflight`.

```
ops/test          # one command, prints a count, enforces a floor
ops/sane          # is the state sane (exit codes 2–9)
ops/check-pins    # load-bearing properties
```

Data: OpenStreetMap (ODbL), USGS 3DEP, USFS Tree Canopy, NLCD, FHWA/Caltrans scenic byways, Foursquare OS Places
(Apache-2.0), Overture Places (CDLA-Permissive-2.0). See `LICENSE-DATA` and `NOTICE`.
