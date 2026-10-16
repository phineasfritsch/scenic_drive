---
id: T-0380
title: device reads the corpus landmarks table and the route card says 'passes X and Y'
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/PlaceStore/, Tests/PlaceStoreTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt, ops/lib/check-safety-disclaimer-pinned, ops/mutate/]
pins_affected: []
reviewer: null
depends_on: [T-0379]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE FIRST: the landmarks table T-0379 stores (columns, integer encodings ele_dm / lat_e5 / lon_e5, the LA row counts quoted in T-0379's Log) and the route card's current text; rule where the line sits before code."
  - "a PlaceStore reader of the landmarks table and a Swift port of landmarks.explain (up to MAX_NAMED = 2 names within NEAR_M = 300 m inclusive, ordered by where the route first comes nearest, a name said once casefolded), tested by full equality against rows the Python explain produces for the same fixture routes."
  - "the route card shows the explanation line from that port; no landmark name or route point leaves the device."
  - "rule (do not assume) whether the Surprise candidate pool reads landmarks (T-0379 R9 left it on places)."
---
## Brief

Filed by agent/claude-opus-5 from T-0379 ruling R9: T-0379 stores the landmarks table in the corpus (schema 4);
the device half - the reader, the explain port and the route card line - is Apple/Sources work outside its touches.

## Log
- 2026-10-16T18:31:00Z filed by agent/claude-opus-5 from T-0379 ruling R9.
