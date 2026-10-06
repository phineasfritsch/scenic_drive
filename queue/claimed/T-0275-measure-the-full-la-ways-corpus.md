---
id: T-0275
title: MEASUREMENT - build the full-region LA corpus (ways + segments + places) from the region build's seam-deduped tile docs and measure it against the plan's 60 MB budget, before any acceptance predicate is written over it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T05:45:00Z
lease_expires_at: 2026-10-06T17:45:00Z
worktree: .worktrees/T-0275
branch: task/T-0275
exclusive: [scenic-index]
touches: [services/etl/regionbuild/, services/etl/etl/, services/etl/tests/, ops/etl-region]
pins_affected: [P-DATA-01, P-PROD-05]
reviewer: null
depends_on: [T-0274]
verify: [ops/test, ops/check-pins]
acceptance:
  - "a ruled 'corpus' stage (after merge/places) feeds the merged tile docs through extractadapter --places-osm into etl.corpus for LA, run in the WSL image; the Log quotes, as each stage lands: ways in, segments out, places, per-table row counts, file bytes, build seconds, and the sqlite page/freelist stats - against the plan's corpus < 60 MB budget"
  - "if over budget, the Log measures at least two ruled reductions (e.g. drop geometry precision, drop low-score residential segments, shard by window) with their bytes and what each loses - the task does NOT pick one; it files the decision as the follow-up with the numbers"
  - "the stage is idempotent (two runs, identical content digest - P-DATA-01) and a regionbuild test over the fixture region pins the stage order and the corpus row counts by equality; no gitignored input deleted"
---
## Brief

T-0274 R1/stillOpen: regionbuild's merge writes "ways": [], so no full-region corpus exists - the device has only the
places-only fallback. Plan M2 exit: 'corpus < 60 MB; PMTiles < 120 MB'. CLAUDE.md: an acceptance over real data is
written AFTER its population is measured, so this is filed as a measurement task.

## Log
- 2026-10-06T05:42:16Z filed by agent/claude-opus-5 (orchestrator) after PR #163 (T-0274) merged.
- 2026-10-06T05:45:00Z claimed by agent/claude-opus-5; lease until 2026-10-06T17:45:00Z
- 2026-10-06T05:53:41Z RULINGS, before any code (agent/claude-opus-5, owner).
  - R1 WHERE THE WAYS COME FROM. merge.py writes the merged document with `"ways": []` and stays that way (tag reads it; a 2.7 GB ways array there would be re-read by every tag run). The new `corpus` stage reads the per-tile pass-1 documents (`layout.doc_of(tile)`, the 152 LA docs, 2.7 GB in /home/phineas/t0242/docs) in SORTED TILE ORDER and keeps the FIRST TILE's row of a way - merge.py's rule, `region_reference.merge`'s rule. Only `way_id`, `tags` and `coords` reach the corpus (extractadapter reads nothing else), so the merged document carries exactly those three keys per way.
  - R2 THE SEAM, COUNTED. `osmium extract -c` completes a border way, so a seam way's tags and coords must be equal in every tile. Counted (`seam_ways`, `seam_differ`); a seam way whose tags or coords differ REFUSES the stage (exit 3, merge.SEAM_REFUSED) and writes no corpus - the same refusal merge makes for two scores. A plan tile with no document refuses (exit 2), as reference/merge do; so does a store with no places stream (`places` has not run).
  - R3 THE CHAIN IS THE SHIPPING CLI, IN-PROCESS. merged ways -> `<region>-corpus-doc.json` -> `etl.extractadapter.main(--input, --out <region>-corpus-extract.json, --region, --places-osm <region>-places.osm.xml)` -> `etl.corpus.main(--input, --out <region>-corpus.sqlite, --built-at, --region)`. No second copy of either rule. `--built-at` is the module constant `fullcorpus.BUILT_AT = 2026-10-06T00:00:00Z` (T-0270's stamp; an INPUT, no clock - P-DATA-01).
  - R4 OVER BUDGET IS MEASURED, NOT HIDDEN. etl.corpus leaves an over-budget file on disk and exits BUDGET_EXIT (3) (T-0206 R4). The stage measures whatever file exists - per-table row counts, bytes, budget, page_size/page_count/freelist_count, dbstat bytes per table where the sqlite build has dbstat (else the line says so), the content digest (`contentdigest.content_sha256` over the file, so a refused build is still digested for P-DATA-01), seconds per sub-step - and then returns etl.corpus's exit code. On LA that is expected to be 3: the stage tells the truth, the reduction is the follow-up's decision.
  - R5 STAGE ORDER. `corpus` is appended to ALL after `fallback` ("after merge/places"); it is PLANNED (reads the tile plan), not PLANLESS. ops/etl-region's header names it. New module regionbuild/fullcorpus.py; layout gains corpus_doc / corpus_extract / corpus.
  - R6 THE TEST binds to `ops/etl-region --local corpus` (the entry point) and `cli.main`, over the two-tile seam fixture (seam_window_a/b, 12 ways each, 3 shared) + fixtures/places_allowlist.osm.xml: ALL by exact equality; the corpus's tables row for row equal to `etl.corpus.build` over `extractadapter.adapt_document` of the first-tile-wins documents computed in the test; the row counts as literals (measured on the fixture, quoted below); two runs -> equal content digest; seam differ -> exit 3 no corpus; over budget -> exit corpus.BUDGET_EXIT with the measurement printed.
  - R7 REDUCTIONS are measured, not shipped: a throwaway driver in the gitignored services/etl/work/t0275/ of the main checkout builds variant extracts through the same shipping etl.corpus (huge --budget-bytes) and reports bytes; the task picks none (acceptance 2).
