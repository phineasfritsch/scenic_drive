---
id: T-0168
title: ETL tagged-PBF rewrite - osmium writes scenic_score 0..10 and its terms onto ways, in the container, over a real extract
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [scenic-index]
touches: [services/etl/etl/, services/etl/tests/, ops/etl-extract, services/etl/Dockerfile]
pins_affected: []
reviewer: null
depends_on: [T-0146, T-0169, T-0161, T-0189, T-0142]
verify: [ops/test, ops/check-pins]
acceptance:
  - "RED BY NAME before code: a test that runs the tagged-PBF writer twice over the same input and asserts byte-identical output (P-DATA-01), red until the writer exists; then green with both sha256 values quoted"
  - "the manifest line re-recorded the same day as the fetch: the fetcher's `verified california-osm.pbf bytes=<N> retrieved=<YYYY-MM-DD> md5 ok` line quoted, and manifest.yaml's bytes:/retrieved: equal it in the same commit (the T-0169 copy is gone - see the INPUT ruling)"
  - "`osmium fileinfo -e` over the output PBF, run in WSL, with its node/way counts quoted; the count of ways carrying scenic_score printed by the writer equals the way count the assembler scored"
  - "the two `ops/sane` check-4 clauses printed as NUMBERS by a check that refuses on either: ways with a NULL scenic_score = 0; motorway/trunk/private/unpaved ways with scenic_score > 0 = 0"
  - "the ranked top-10 ways by scenic_score printed with name, highway class and a coordinate, for the human's '8/10 are roads you'd drive' read (plan M2 exit); the list is quoted, the judgement is not made by the agent"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit; every wc -l re-measured there"
---
## Brief

The WSL half of what T-0146 used to be (cut by the 2026-09-18 14:13 panel, grounded). T-0146 proves the
assembly and the check-4 gates over a committed fixture with native Python; THIS task runs it over a real
extract inside the pinned ETL image (docker on this box works only through WSL) and has `osmium` write
`scenic_score=0..10` plus the terms back onto the ways of the tagged PBF that T-0031 imports into GraphHopper.

It deliberately carries what a hand-written fixture cannot surprise its author with: real tag coverage
(per-class surface coverage goes into `meta`, plan M2 row), NULLs from ways with no DEM or land-cover sample,
and the plan's human exit clause - "8/10 top-scored ways are roads you'd drive" - printed as a ranked list
with names and coordinates for the human to read. `ops/sane` check 4's clauses run for real here: no NULL
scores; no motorway/trunk/private/unpaved way with a score above 0.

Rule in the Log before code: the 0..1 -> 0..10 quantisation (round, floor, or keep one decimal - the
GraphHopper encoded value's bit width decides); what happens to a way a producer REFUSED (a named flag, never
a silent 0); idempotence (P-DATA-01: running twice over the same extract is byte-identical); which extract
(the refetched California file from T-0169, clipped to regions/la's bbox (sfbay second)).

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
- 2026-09-19T00:40:47Z PROMOTED to ready/ with FOUR RULINGS and the input decision, by agent/claude-fable-5-1 (17:13 panel, STRATEGY
  + grounding). depends_on gains T-0161 (T-0146's Log already says this task keeps it; #94 is in its fourth
  round with proximity.py judged correct four times).
  R1 QUANTISATION: `scenic_score` 0..10 = round-half-up of the 0..1 score x 10 (an integer; GraphHopper's
  encoded value holds it in 4 bits); the 0..1 value stays in the corpus, so nothing downstream re-derives it.
  R2 REFUSED: a way a producer refused carries `scenic_refused=1` and NO `scenic_score` tag - never a silent 0
  (0 means "dull", the CLAUDE.md invariant for motorway/trunk); the check-4 NULL count therefore counts only
  ways that should have a score and lack one.
  R3 IDEMPOTENCE: running the writer twice over the same input is byte-identical (built_at is an INPUT, not a
  clock; osmium's output ordering is fixed by input order) - the first acceptance line.
  R4 INPUT: T-0169's verified 1,328,688,632-byte california-osm.pbf was DELETED with its worktree the hour
  #99 merged (only the unverifiable 2026-09-08 build survives as hardlinks in .worktrees/T-0028 and T-0107,
  1,482,437 bytes short of the manifest). REFETCH natively - `cd services/etl && python -m etl.fetch --only
  california-osm.pbf` (T-0169's run took 7m43s) - INTO THE MAIN CHECKOUT's gitignored services/etl/inputs/
  (C:/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/inputs/), never into a worktree, and point
  the extract at it; re-record manifest bytes:/retrieved: the same day. The 51 MB Sep-8 sfbay-filtered.osm.pbf
  in .worktrees/T-0028 may serve as a SMOKE input for the osmium write loop only, with its provenance gap
  named in the Log. T-0177 makes the shared inputs directory the rule.
- 2026-09-19T00:49:41Z LA FIRST, by agent/claude-fable-5-1 (the owner lives in Los Angeles - memory user-lives-in-la): the extract this task clips and scores is LA FIRST (`services/etl/regions/la/region.json`'s bbox), sfbay second - the owner drives in Los Angeles, and the plan's '8/10 top-scored ways are roads you'd drive' is a judgement only the owner can make over roads the owner knows; both clips come from the same statewide california-osm.pbf.
- 2026-09-19T02:11:14Z WORDS FOLLOW THE RULING, by agent/claude-fable-5-1 (19:13 panel, grounded): the Brief's 'clipped to the sfbay bbox' contradicted the 00:49:41Z LA FIRST line; corrected (1 replacement). The refetch into the main checkout's services/etl/inputs/ was started by the orchestrator at 2026-09-19T02:11:14Z (log under .artifacts/fetch/); re-record manifest bytes:/retrieved: from its printed line in this task's commit.
- 2026-09-19T02:54:47Z INPUT ON DISK, by agent/claude-fable-5-1: the refetch into the MAIN checkout's gitignored services/etl/inputs/ verified at 2026-09-19T02:54:47Z after one md5 race with Geofabrik's daily rebuild (the first attempt's sidecar changed mid-download; the fetcher deleted the file and retried, as T-0169 designed). The fetcher printed: `verified california-osm.pbf bytes=1328857020 retrieved=2026-09-19 md5 ok`. os.path.getsize -> 1328857020 (a newer build than T-0169's 1,328,688,632). This task's commit re-records manifest.yaml's bytes:/retrieved: from that line; the file survives worktree removal now (T-0177).
- 2026-09-19T03:45:19Z depends_on += T-0189 by agent/claude-fable-5-1 (rv1-pr104's finding): dem.py and landcover.py still read a per-worktree inputs/ and return None silently when a tile is absent; from a worktree this task would score LA with terrain zeroed and a green suite. T-0189 makes the four consumers read the shared directory and refuse by name.
- 2026-09-19T04:34:10Z depends_on += T-0142 by agent/claude-fable-5-1 (22:13 panel, grounded): T-0142's Log at 2026-09-19T02:58:56Z rules its finding 3 'a HARD prerequisite of T-0168' - dem.tile_for returned None for every point outside sfbay's eight tiles, so an LA clip would score with terrain silently zeroed and this task's check-4 numbers and top-10 read would mean nothing. The queue now says what that Log already rules: a claimer cannot start this before PR #106 merges.
