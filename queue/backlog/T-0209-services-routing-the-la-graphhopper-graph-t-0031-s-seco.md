---
id: T-0209
title: services/routing - the LA GraphHopper graph: T-0031's second half (the whole-LA tagged PBF imported with the scenic_score encoded value, T(lambda) monotone over LA pairs, the graph-cache handed to the box by rsync with the atomic symlink flip and N-1 kept)
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [services/routing/config.yml, scenic-index]
touches: [services/routing/, services/etl/etl/, ops/deploy-routing]
pins_affected: []
reviewer: null
depends_on: [T-0207, T-0208, T-0213]
verify: [ops/test, ops/check-pins]
acceptance:
  - "the whole-LA tagged PBF (T-0208's region-normalised scores, T-0207's class cap in force) imported by the digest-pinned GraphHopper 11.0 image through WSL: the import log's way/edge counts quoted, SCENIC_EV present, /info's graph hash recorded (P-PROD-04's three-way equality named as pending until goldens exist)"
  - "T(lambda) non-decreasing over {0,1,2,4,8} on at least three LA origin-destination pairs the Log names (Westwood -> Malibu, Westwood -> Woodland Hills, Santa Monica -> Topanga) with the five durations quoted per pair, and the penalty BITES (the T-0031 bite floor re-ruled for LA from the measured spread, never copied from Vermont's 5%)"
  - "no returned route carries a residential or service run over 800 m at any lambda on those pairs (the no-rat-run property, measured from path details) - if one does, the task FAILS and names the ways"
  - "the VPS half (rsync, symlink flip, N-1) either done with its transcript or recorded as blocked on the human's box credentials - never implied"
---
## Brief

From the 03:13 panel (STRATEGY, grounded): T-0031 closed as a Vermont slice whose Log rules 'the FIRST served graph
is LA' and leaves its second half unclaimed; the only graph task in the queue was T-0008 (Bay Area from R2). T-0182
(the CLI drive the owner takes) and T-0190 depended on T-0031, which is in done/, so the queue read them as
unblocked when nothing builds the graph they need. This is that task. Order ruled: #113 -> T-0207 (the class cap
moves scores) -> T-0208 (one region-wide normalisation) -> the whole-LA PBF -> this -> T-0182.

## Log
- 2026-09-19T10:46:00Z filed by agent/claude-fable-5-1 (03:13 panel, grounded). Not started.
- 2026-09-19T11:43:44Z depends_on += T-0213 by agent/claude-fable-5-1 (04:13 panel; grounded 8 of 14 - only the grounded items applied): the import mechanics over a real tagwriter PBF and ops/deploy-routing move to T-0213 (index-free, startable now); this task keeps the whole-LA import, T(lambda) over LA pairs, the LA bite floor and the 800 m no-rat-run measurement.
