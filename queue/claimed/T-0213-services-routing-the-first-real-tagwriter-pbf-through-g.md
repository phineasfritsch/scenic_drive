---
id: T-0213
title: services/routing - the first REAL tagwriter PBF through GraphHopper 11.0: the canyon window imported, the TagParser proved on real scenic_score tags, /info's hash recorded, ops/deploy-routing created (T-0209's index-free half)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T11:47:06Z
lease_expires_at: 2026-09-19T17:47:06Z
worktree: .worktrees/T-0213
branch: task/T-0213
exclusive: [routing-config]
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
- 2026-09-19T11:47:06Z claimed by agent/claude-opus-5; lease until 2026-09-19T17:47:06Z
- 2026-09-19T11:52:44Z RULINGS, before any code (author rule). Read first: this task file, services/routing/
  entire (Dockerfile, config.yml, pom.xml, ScenicRouterMain.java 123, ScenicScoreImportRegistry.java 24,
  ScenicScoreParser.java 42, profiles/*.json, build-slice.sh, README.md, tests/*), T-0031's Log (R4, the
  container command lines, the Vermont counts) and T-0168's contract. Input verified where it lies, read-only,
  in the MAIN checkout:

      $ sha256sum services/etl/work/la/window-tagged-1.osm.pbf
      06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090 *services/etl/work/la/window-tagged-1.osm.pbf

  and its own read-back (services/etl/work/la/window-readback.osm.xml, osmium 1.16.0) counted by this session:
  ways 12402, scored 11740, refused 0, score histogram 0:5975 1:758 2:1677 3:1397 4:926 5:693 6:245 7:65 8:4.
  That matches the task file's 12,402 / 11,740 exactly, so the acceptance block's numbers are the artifact's.

  (R1) HOW A SECOND INPUT IS IMPORTED WITHOUT DISTURBING THE VERMONT SLICE. build-slice.sh is not
  parameterised for this: steps 1-3 are the SYNTHETIC tagger and step 5 hard-codes work/graph-cache. Ruled:
  ONE recipe, extracted - a new sibling `services/routing/import-graph.sh <input.pbf> <graph-dir>` carries the
  single `docker run ... --mode import` command line, and build-slice.sh step 5 is replaced by a call to it.
  So there is exactly one import recipe in the tree and the Vermont path exercises the same lines the LA
  window does. The Vermont graph-cache in the MAIN checkout is never touched: every output of this task lands
  under THIS worktree's gitignored services/routing/work/.

  (R2) THE PROBE - how a test reads an encoded value back for a NAMED OSM way. GraphHopper does not index by
  way id, and a snapped short route proves only "some edge near this point", not way 74344132: the snap can
  land on a neighbour and the test still passes. Ruled: GraphHopper 11 ships the `osm_way_id` encoded value;
  `osm_way_id` joins graph.encoded_values in config.yml (the serial file this task holds), and
  ScenicRouterMain - THE SHIPPING ENTRY POINT, the same main() that runs the import - gains `--mode probe
  --probe-ways <id,id,...>`, which walks getBaseGraph().getAllEdges() and prints, per requested way id, the
  edge count and the distinct scenic_score values the import actually encoded. The binding is way id ->
  score, both read out of the built graph, with no coordinate in the loop. Cost of carrying osm_way_id in the
  shipping config: 31 bits per edge in the graph and nothing at query time; it is also what makes any future
  "why did this edge score that" answerable, so it stays in the shipped config rather than a probe-only one -
  the profile and config under test must be the ones that ship (T-0031's rule).
  THE DEFAULT FOR A WAY WITH NO scenic_score TAG. ScenicScoreParser.parse today: null/blank -> 0, <=0 -> 0,
  unparsable -> 0, >10 -> clamped to 10 (source, not paraphrase: lines 32-41). So a way with no tag is
  encoded 0, which in profiles/car_scenic_request.json falls in the `low` band - i.e. indistinguishable from
  a motorway that was scored 0 on the merits. For a T-0168 `scenic_refused=1` way (refused carries NO
  scenic_score) that is "refused reads as dull 0 silently", and it is WRONG as a long-run semantic: refused
  is no evidence, and no evidence is not a zero score. Ruled OUT OF SCOPE here and recorded for T-0209:
  fixing it means a widened encoded value (a sentinel, e.g. 4 bits 0..10 plus a separate scenic_known flag)
  and a matching band rule in profiles/*.json - and the profiles are NOT this task's lock. This task changes
  no semantics; it proves the joint. Also load-bearing for this window: refused=0 here (counted above), so
  nothing in this import is affected by the ruling either way.

  (R3) THE THREE PROBE WAYS, picked from the real read-back, not invented:
    - 74344132 Topanga Canyon Boulevard, highway=primary, scenic_score=8 (scenic_score_unit 0.7722) - one of
      only 4 ways at 8 in the whole window.
    - 10715427, highway=track, scenic_score=0 with scenic_gate=track - a GATED way. It is imported (config's
      import.osm.ignored_highways names footway, cycleway, path, pedestrian, steps - not track), gated by the
      PROFILE, so it must be present in the graph carrying 0.
    - no highway way in this window lacks scenic_score: scored 11740 of 12402 and refused 0, so the 662
      unscored ways are all NOT-A-ROAD (e.g. way 4883641, tags `natural`, `source` only - T-0168 leaves those
      untouched). Ruled honestly: the third probe is way 4883641 asserted ABSENT from the routable graph
      (edges=0) - a real property of the import, not a score - and the ruled no-tag default (0) is instead
      demonstrated by the RED run below, where the parser's key no longer matches any tag and EVERY probed
      way, Topanga included, reads 0. That is the default exercised over the real graph rather than asserted
      in prose.

  (R4) ops/deploy-routing's CONTRACT and its rehearsal. Contract: (1) refuses unless HEAD is reachable on
  origin (ops/deploy's own rule, same `git branch -r --contains`); (2) refuses unless the named box
  credentials are in the environment - SCENIC_ROUTING_HOST, SCENIC_ROUTING_USER, SCENIC_ROUTING_KEY,
  SCENIC_ROUTING_ROOT - naming each missing one; (3) uploads the graph to a NEW release dir
  <root>/releases/<utc>-<sha>, never into the live one; (4) flips <root>/current by writing a fresh symlink
  beside it and `mv -T` over the old one, which is atomic on one filesystem (ln -sfn is NOT: it unlinks
  first); (5) restarts the service; (6) prunes to N-1 == keeps the 2 newest releases, so the previous one is
  there to flip back to. REHEARSAL WITHOUT A VPS: the script's only privileged verbs are `remote` (ssh) and
  `send` (rsync). With SCENIC_ROUTING_REHEARSE=<dir> set, `remote` runs the same command line under `bash -c`
  and `send` is `cp -r`, against a local temp dir under work/; the restart command comes from
  SCENIC_ROUTING_RESTART_CMD so the rehearsal can pass `echo`. Same code path, same flip, same prune - only
  the transport is swapped, and the transcript of two consecutive rehearsed deploys (flip + N-1 prune) is
  quoted in this Log. The VPS half is BLOCKED ON THE HUMAN (no host, no key in this session) and is recorded
  as such; nothing in this task claims a deployed router.

  (R5) DISAGREEMENT WITH THE ACCEPTANCE BLOCK, ruled now rather than at review: the block asks for "/info's
  hash recorded". There is no HTTP surface in services/routing - T-0031 R4 ruled the Dropwizard `server:`
  section out of that slice and this task does not add one (it is T-0209's serving half). /info is therefore
  not reachable and no /info hash exists to record. Ruled: what IS recorded is the graph's own identity as
  GraphHopper writes it - services/routing/work/graph-la-window/properties in full (it carries the encoded
  value list, the import date and the datareader file) plus its sha256 - which is the fact /info would report.
  Recorded as an acceptance wording correction, not as a met item.
- 2026-09-19T11:56:30Z RED BY NAME, on the real input. `services/routing/work/red-build.sh` (scratch, work/ is
  gitignored) copies Dockerfile, config.yml, profiles/ and plugins/ and misspells the parser's TAG KEY in the
  COPY only - the committed source is never edited:

      29:        scenicScore.setInt(false, edgeId, edgeIntAccess, parse(way.getTag(KEY + "_typo", "")));

  The encoded value still exists and the import still succeeds - which is the whole point: this is the defect
  that leaves every other check green. Red import (image scenic-routing:t0213-red, the same
  window-tagged-1.osm.pbf, sha256 quoted by import-graph.sh as 06046be0...0090):

      pass1 - finished, processed ways: 12,402, accepted ways: 11,740, way nodes: 131,312, relations: 76
      pass2 - finished, processed ways: 12,402, way nodes: 131,312, nodes with tags: 3,577, ignored barriers at junctions: 11
      Finished reading OSM file: /data/window-tagged-1.osm.pbf, nodes: 21,137, edges: 24,057, zero distance edges: 1,644
      GraphHopper - nodes: 21,137, edges: 24,057
      SCENIC_EV present=true bits=4 max=10

  Red probe over that graph:

      PROBE way=74344132 edges=2 scenic_score=0
      PROBE way=10715427 edges=1 scenic_score=0
      PROBE way=4883641 edges=0 scenic_score=-

  and the test, pointed at the red image and red graph by SCENIC_ROUTING_IMAGE / SCENIC_ROUTING_GRAPH:

      FAILED tests/test_scenic_score_readback.py::test_named_way_carries_its_real_scenic_score
      AssertionError: way 74344132 carries scenic_score=8 in window-tagged-1.osm.pbf but the graph encoded [0]
      over its 2 edge(s). A parser reading the wrong tag key encodes the no-tag default 0 here while the
      import, the encoded value and every routed test stay green.
      1 failed, 2 passed in 5.81s

  Stated rather than hidden: only the Topanga assertion goes red. The gated way and the not-a-road way read
  the same under the misspelling (0 is both their real value and the default, and a not-a-road way has no
  edge either way), so those two are not red-demonstrated by this mutation - they are demonstrated by the
  numbers themselves being present in the green run below. This is also R3's no-tag default (0) exercised on
  the real graph rather than asserted in prose: with no tag matching, all 11,740 scored ways take it.

- 2026-09-19T11:58:40Z GREEN, the REAL import, foreground, counts quoted as the stage landed. Image rebuilt
  from the committed source as `scenic-routing:t0213` (tag bumped from t0031 with config.yml: a graph built
  under the new graph.encoded_values cannot be loaded by an image carrying the old list, and the Dockerfile's
  own rule is that a moving tag is a silent change - so the tag moves with the config, and the existing
  Vermont slice - image scenic-routing:t0031 and the MAIN checkout's services/routing/work/graph-cache - is
  left exactly as it was. build-slice.sh and test_lambda_monotone.py move to t0213 together; re-running
  build-slice.sh re-imports Vermont under the new config.)

      06046be00d336f2f976a31676ce452d2f35fabba15f63d437be3043d909a0090  .../services/etl/work/la/window-tagged-1.osm.pbf
      == import: scenic-routing:t0213 -> .../services/routing/work/graph-la-window ==
      pass1 - finished, processed ways: 12,402, accepted ways: 11,740, way nodes: 131,312, relations: 76
      pass2 - finished, processed ways: 12,402, way nodes: 131,312, nodes with tags: 3,577, ignored barriers at junctions: 11
      Finished reading OSM file: /data/window-tagged-1.osm.pbf, nodes: 21,137, edges: 24,057, zero distance edges: 1,644
      PrepareRoutingSubnetworks - car_scenic - Marked 24720 subnetworks (biggest: 323 edges) -> 1 components(s) remain (smallest: 21645, biggest: 21645 edges), total marked edges: 1261
      GraphHopper - nodes: 21,137, edges: 24,057
      SCENIC_EV present=true bits=4 max=10
      GRAPH nodes=21137 edges=24057

  accepted ways 11,740 is the artifact's own scored-way count, which is the cleanest single corroboration
  available that the routable set and the scored set are the same ways.

  THE GRAPH'S IDENTITY (R5: there is no /info in this slice; this is what /info would report), from
  services/routing/work/graph-la-window/properties, sha256
  170bfe37bda146a51821f74fa53d9a42084e1cb3db27e2841205fe432c20b188:

      datareader.data.date=1970-01-01T00:00:00Z
      profiles=car_fast|-421433575,car_scenic|1913116034
      graph.em.version=4
      graph.em.bytes_for_flags=12
      graph.encoded_values=[... "name":"scenic_score","bits":4,"max_storable_value":15,"max_value":8 ...
                            ... "name":"osm_way_id","bits":31,"max_value":1558336363 ...]

  `scenic_score` max_value=8 is the graph itself agreeing with the read-back histogram: the highest score
  anywhere in this window is 8, and 4 ways carry it.

- 2026-09-19T11:59:20Z GREEN PROBE, the shipped image over the real graph:

      PROBE way=74344132 edges=2 scenic_score=8      Topanga Canyon Boulevard, tagged 8
      PROBE way=10715427 edges=1 scenic_score=0      highway=track, scenic_gate=track, tagged 0 - IMPORTED
      PROBE way=4883641 edges=0 scenic_score=-       natural=..., no highway, no score - never a road edge

      $ cd services/routing && python -m pytest tests/test_scenic_score_readback.py -rs
      3 passed in 5.25s

  This is the joint T-0031 could not close: real tagwriter bytes -> ScenicScoreParser -> the built graph,
  read back per NAMED way id.

- 2026-09-19T12:00:10Z ONE ROUTED REQUEST inside the window, PCH at Topanga -> Topanga near Old Topanga, over
  the same graph, lambda 0 and lambda 8 (models substituted from the committed profiles/scenic_lambda_bands.json
  into profiles/car_scenic_request.json, work/models-la/):

      ROUTE profile=car_fast   model=-              time_ms=507242 distance_m=8121.6
      ROUTE profile=car_scenic model=lambda-0.json  time_ms=507242 distance_m=8121.6
      ROUTE profile=car_scenic model=lambda-8.json  time_ms=507242 distance_m=8121.6

  NO monotonicity claim and NO bite claim is made from this. It is a SMOKE graph: the scores in it are
  T-0207's and T-0208's to move (residential/service escaping the anti-rat-run clause, and the window
  fixture re-record), so any T(lambda) shape measured here measures a number that is about to change. What
  this request proves is that the graph routes and that a per-request custom model referencing scenic_score
  loads and is accepted against it. For the record, and explicitly NOT as a property: the two durations are
  identical on this pair, which is what one expects when the direct route is already the scenic one - Topanga
  Canyon Boulevard is scored 8, i.e. in the never-penalized `high` band at every lambda. T-0209 owns T(lambda)
  over LA pairs.
