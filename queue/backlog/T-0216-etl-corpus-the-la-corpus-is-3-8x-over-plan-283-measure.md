---
id: T-0216
title: etl/corpus - the LA corpus is 3.8x over plan:283's 60 MB: measure each shrink candidate on the real union corpus, rule which ship, and re-measure against the ceiling (the M2 exit clause is UNMET until this lands)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, Sources/PlaceStore/, Tests/PlaceStoreTests/]
pins_affected: []
reviewer: null
depends_on: [T-0206, T-0217]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURED FIRST, each candidate ALONE over the real three-window union (46,231 ways, 79,764 segments, 19,906,560 B = 430.59 B/way; T-0206's Log) with the bytes and B/way quoted as each lands: (a) VACUUM + an explicit PRAGMA page_size; (b) service ways left out of the corpus (312,645 of the clip's 560,208 filtered ways = 55.8%; T-0207 already scores every service way 0) - RULE what the app loses: the corpus serves saved-drive re-resolution, the hazard strip and segment lookup, so a route that legitimately crosses a service road must still resolve; (c) segments_rtree as a second copy of every bbox; (d) geom_sha256 at 32 B/way and the name column; (e) WITHOUT ROWID / integer-packed geometry"
  - "RULED in the Log from those numbers which candidates ship; any DDL change bumps schema_version with the DDL-hash pytest (plan: P-PROD-05) and the Swift PlaceStore reader in the same PR or a named dependent task; the extrapolation to 560,208 ways re-derived with python and quoted; the verdict against CORPUS_BUDGET_BYTES stated plainly - MET, or UNMET with the remaining factor and the next candidate (region-split download)"
  - "the extrapolation is still a FLOOR while terms_osm, terms_raster, places, curated and FTS5 are emitted empty - the Log says what each is expected to add, measured on the window if its emitter exists, else named as unmeasured"
---
## Brief

T-0206 (PR #120) ran corpus.build on real LA data for the first time: 430.59 B/way, so the whole clip extrapolates
to about 241.2 MB against 62,914,560 B - 3.8x over, and a floor. That task pinned the ceiling and shrank nothing.
The plan's first-run download is '~50 MB corpus' on cellular-or-Wi-Fi; 241 MB is a different product. This is a
product-and-schema decision measured candidate by candidate, not an emitter tweak. The predicate is written after
the measurement exists (CLAUDE.md): the population and its per-class mix are in T-0206's Log.

## Log
- 2026-09-19T13:12:06Z filed by agent/claude-fable-5-1 (orchestrator, from T-0206's measurement on PR #120). Not started. Holds scenic-index when claimed; after T-0217 so the input is a shipped adapter, not a throwaway.
