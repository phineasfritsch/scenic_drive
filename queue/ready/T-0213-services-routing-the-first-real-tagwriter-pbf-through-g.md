---
id: T-0213
title: services/routing - the first REAL tagwriter PBF through GraphHopper 11.0: the canyon window imported, the TagParser proved on real scenic_score tags, /info's hash recorded, ops/deploy-routing created (T-0209's index-free half)
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [services/routing/config.yml]
touches: [services/routing/, ops/deploy-routing]
pins_affected: []
reviewer: null
depends_on: [T-0168, T-0031]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the digest-pinned GraphHopper 11.0 image (services/routing/Dockerfile) imports the REAL canyon-window tagged PBF (MAIN checkout, read-only: services/etl/work/la/window-tagged-1.osm.pbf, sha256 06046be0...0090, 12,402 ways, 11,740 scored) through WSL, foreground: the import log's way/edge counts quoted AS THE STAGE LANDS, SCENIC_EV present, and a probe that the encoded value carries REAL scores - three named ways read back from the graph (Topanga Canyon Boulevard 74344132 -> 8, a gated way -> 0, a way with no scenic_score tag -> the ruled default), RED first with the parser's tag key misspelled, then green; T-0031 only ever imported SYNTHETIC way_id % 11 tags"
  - "one routed request inside the window (PCH at Topanga -> Topanga near Old Topanga) at lambda 0 and lambda 8 with both durations quoted - NO monotonicity or bite claim is made over a 12,402-way window whose scores T-0207/T-0208 will move; this is a smoke graph and the Log says so"
  - "ops/deploy-routing (100755): new dir + atomic symlink flip + restart, keeps N-1, REFUSES without the box credentials naming the env vars, and refuses unless HEAD is on origin - rehearsed against a local temp dir with the transcript quoted; the VPS half recorded as blocked on the human, never implied"
  - "cd services/routing && python -m pytest tests -rs count line; bash ops/lib/check-exec-bits, check-line-cap, queue-check bare; config.yml changes (if any) ruled - it is a serial file and this task holds it"
---
## Brief

From the 04:13 panel (grounded): the joint between tagwriter's real bytes and GraphHopper's TagParser has never
been exercised - T-0031's Vermont slice imported synthetic tags. T-0209 (the LA graph) waits on T-0207 and T-0208
because they move scores; the import MECHANICS quote no score and can be proved now over the existing canyon
window. T-0209 then depends on this and keeps only the whole-LA import, T(lambda) over LA pairs and the rat-run
measurement.

## Log
- 2026-09-19T11:43:44Z filed in ready/ by agent/claude-fable-5-1 (04:13 panel; grounded 8 of 14 - only the grounded items applied). Not started.
