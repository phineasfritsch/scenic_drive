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
exclusive: [routing-config, scenic-index]
touches: [services/routing/, ops/deploy-routing]
pins_affected: []
reviewer: null
depends_on: [T-0207, T-0208, T-0213]
verify: [ops/test, ops/check-pins]
acceptance:
  - "PATH DETAILS: T-0224 (PR #123) could not measure a single run because the t0213 image's ScenicRouterMain never calls getPathDetails and its shaded jar carries no graphhopper-web - this task adds a --mode route-details (or the web bundle) that prints road_class / osm_way_id / distance per edge for every routed pair, RED first (the mode absent) then green, BEFORE clause 3's runs are measured; the pair coordinates it routes are typed into the Log (T-0213 left its pair in prose; T-0224 typed 34.0387,-118.5836 -> 34.0938,-118.6045 and got 8230.4 m against 8121.6 m)"
  - "the whole-LA tagged PBF (T-0208's region-normalised scores, T-0207's class cap in force) imported by the digest-pinned GraphHopper 11.0 image through WSL: the import log's way/edge counts quoted, SCENIC_EV present, /info's graph hash recorded (P-PROD-04's three-way equality named as pending until goldens exist)"
  - "T(lambda) non-decreasing over {0,1,2,4,8} on at least three LA origin-destination pairs the Log names (Westwood -> Malibu, Westwood -> Woodland Hills, Santa Monica -> Topanga) with the five durations quoted per pair, and the penalty BITES (the T-0031 bite floor re-ruled for LA from the measured spread, never copied from Vermont's 5%)"
  - "the residential and service RUNS on every returned route at every lambda on those pairs measured from path details and quoted per pair (longest run in m, its way ids, highway class); the no-rat-run threshold is RULED in the Log from that measurement and from the per-class way-length distribution (T-0224's numbers), never asserted first - a run the ruling names a rat-run FAILS the task and names the ways"
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
- 2026-09-19T15:26:14Z by agent/claude-fable-5-1 (orchestrator; 06:13 panel STRATEGY, grounded on the T-0208/T-0209 texts): clause 1's 'whole-LA tagged PBF' is now WRITTEN AND RETAINED by T-0208 (fourth acceptance line there); this task imports that artifact by sha256 and scores nothing. Lock order scenic-index: T-0208 -> T-0209 -> T-0216.
- 2026-09-19T20:26:45Z by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0): clause 3 was a predicate ('no run over 800 m') over an unmeasured population - CLAUDE.md 74615e0 forbids it; T-0112 measured the top-200 LA ways' MEDIAN length at 0.60 km, so an ordinary hillside way trips 800 m on geometry alone. Rewritten as the measurement; the threshold is ruled after T-0224's numbers exist. touches shed services/etl/etl/ per the 15:26:14Z ruling (this task imports T-0208's artifact and scores nothing). scenic-index KEPT: the lock order T-0208 -> T-0209 -> T-0216 is what holds the corpus shrink behind the routed drive.
- 2026-09-19T20:54:38Z by agent/claude-fable-5-1 (orchestrator, from T-0224's STILL OPEN 1-2): a path-details clause added first - clause 3's run measurement is impossible on the t0213 image (no getPathDetails, no graphhopper-web; T-0224 demonstrated --mode details prints nothing). T-0224's per-class way-length table (residential median 170.7 m, p90 584.7 m, 4.83 % of ways over 800 m; service median 59.9 m, 0.48 % over 800 m; three classes combined 1.53 %) is the population clause 3's ruling reads.
