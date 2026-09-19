---
id: T-0224
title: etl - MEASUREMENT: the residential and service way-length distribution over the LA clip per highway class, and the longest residential/service run on T-0213's window routes at lambda 0 and 8 - numbers only; the no-rat-run threshold for T-0209/T-0221 is written after
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T20:27:23Z
lease_expires_at: 2026-09-20T00:27:23Z
worktree: .worktrees/T-0224
branch: task/T-0224
exclusive: []
touches: [services/etl/tests/, services/routing/tests/]
pins_affected: []
reviewer: null
depends_on: [T-0213]
verify: [ops/test, ops/check-pins]
acceptance:
  - "over the MAIN checkout's services/etl/work/la/la-filtered.osm.pbf (560,208 filtered ways; T-0112's osmium-export shape): per highway class the way-length distribution (count, median, p90, max, the share over 800 m) quoted in the Log; residential and service first"
  - "over T-0213's window graph (services/routing/work/t0213/graph-la-window, image scenic-routing:t0213, its pytest harness): for the routed pair at lambda 0 and 8, the longest residential/service RUN (consecutive edges of one class, in m, way ids) quoted; no threshold asserted - the Log ends with the numbers T-0209's ruling will read"
  - "nothing under services/etl/etl/ or services/routing/ changes; a measurement script, if committed, lives under tests/ with the command that produced each number; queue-check bare"
---
## Brief

From the 11:13 panel (STRATEGY, fable-grounded): T-0209 clause 3 asserted 'no residential or service run over 800 m'
over a population nobody had looked at (the only 800 m in the tree was its own copy into T-0221); T-0112:72-73
measured the top-200 LA ways' median length at 0.60 km. Measure first, rule after - the plan's rat-run property
('no run >800 m of residential/living_street') is a Bay Area number until LA says otherwise.

## Log
- 2026-09-19T20:26:45Z filed by agent/claude-fable-5-1 (11:13 panel, fable-grounded on T-0112:72-73, T-0209 Log 15:26:14Z, CLAUDE.md 74615e0). Not started; Log-only, no lock; startable now.
- 2026-09-19T20:27:23Z claimed by agent/claude-opus-5; lease until 2026-09-20T00:27:23Z
- 2026-09-19T20:27:23Z PROMOTED and claimed by agent/claude-fable-5-1 (orchestrator): the 11:13 panel ranked it the free slot's start (Log-only, no lock, inputs in the main checkout). Beside T-0208 (which holds scenic-index and is writing la-tagged.osm.pbf) - this task reads la-filtered.osm.pbf and the t0213 graph only.

- 2026-09-19T20:37:43Z RULINGS by agent/claude-opus-5 (author rule: every disagreement between plan, Brief,
  code and reality ruled BEFORE the code), worktree .worktrees/T-0224 at 2fce36b == origin/main, clean.

  R1. ACCEPTANCE 2 ASKS FOR SOMETHING THE HARNESS CANNOT ANSWER, and acceptance 3 forbids the change that
  would make it answerable. The longest run of consecutive residential/service edges needs GraphHopper PATH
  DETAILS (road_class, osm_way_id, per-edge distance). The image's ENTRYPOINT is ScenicRouterMain
  (services/routing/plugins/scenic-score-parser/src/main/java/com/scenicdrive/routing/ScenicRouterMain.java):
  its `route()` prints exactly `ROUTE profile=%s model=%s time_ms=%d distance_m=%.1f` out of
  `ResponsePath.getTime()` / `getDistance()` and never calls `getPathDetails()`; its mode dispatch is
  `probe`, `route`, else silent return. The pom (same plugin) names ONE graphhopper dependency,
  `graphhopper-core` - no graphhopper-web/application is in the shaded jar, so the image serves no HTTP
  `/route` and a `details=road_class&details=osm_way_id` query has nowhere to arrive. Reaching per-edge
  details means editing services/routing/plugins/..., which acceptance 3 refuses.
  RULED: take the task's own fallback - route the pair, QUOTE what comes back, and DEMONSTRATE the boundary
  (an unknown `--mode` against the same container; the pom's dependency list) instead of describing it. The
  run length is NOT measured, NOT estimated and NOT claimed anywhere in this task.

  R2. THE PAIR'S COORDINATES WERE NEVER RECORDED. T-0213's Log names the pair in prose ("PCH at Topanga ->
  Topanga near Old Topanga", car_fast 507242 ms / 8121.6 m); no lat,lon appears in queue/done/T-0213-*.md or
  in services/routing/work/t0213/. RULED: type the endpoints here, bind them back by DISTANCE, and quote
  both distances side by side rather than asserting the pair is identical.

  R3. meta.json's per-class counts (which sum to the Brief's 560,208) are osmium tags-filter counts by KEY
  PATTERN: its "primary" 45,535 is primary + primary_link, "motorway" 17,394 is motorway + motorway_link,
  and so on. RULED: the table below reports osmium export's own `highway` VALUES, one row per exact value,
  and the reconciliation against meta.json is quoted rather than the rows being reshaped to match it.

  R4. METRIC, stated once: way length = the haversine sum over the way's own node sequence with
  R = 6_371_008.8 m (the mean Earth radius ScenicKit uses, so a length here and a length on the device are
  the same number). Median = mean of the two middle values at even n. p90 = NEAREST-RANK (the ceil(0.9n)-th
  smallest), i.e. always a value the population actually contains. No threshold is asserted anywhere: the
  800 m column is a SHARE, reported because T-0209/T-0221's clause names that number, not because this task
  rules on it.

- 2026-09-19T20:37:43Z STAGE 1 LANDED - way-length distribution per highway class over the LA clip
  (services/etl/work/la/la-filtered.osm.pbf in the MAIN checkout, osmium + python3 both out of the pinned
  `scenic-etl` image). Quoted as it landed, per CLAUDE.md. Command (one line, git-bash):

      wsl -e bash -lc "docker run --rm -v /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/work/la:/data:ro -v /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0224/services/etl/tests:/scripts:ro scenic-etl bash -lc 'osmium export /data/la-filtered.osm.pbf -f geojsonseq --geometry-types=linestring --add-unique-id=type_id | python3 /scripts/measure_way_lengths.py --source la-filtered.osm.pbf'"

      WAY LENGTHS source=la-filtered.osm.pbf radius_m=6371008.8 metric=haversine-sum
      percentile=nearest-rank median=mean-of-two-middle long_way_threshold_m=800
      highway class         count   median m      p90 m       max m   n>800m  share>800m  longest way
      -----------------------------------------------------------------------------------------------------------
      residential          99,715      170.7      584.7      7088.9    4,821      4.83%  w202029047 (7088.9 m)
      living_street           195       52.2      218.0       965.7        1      0.51%  w639291336 (965.7 m)
      service             312,619       59.9      190.8     10162.4    1,497      0.48%  w27208618 (10162.4 m)
      primary              43,815       51.4      181.3     31647.1      147      0.34%  w172244780 (31647.1 m)
      secondary            42,237       48.2      212.4     14546.6      346      0.82%  w173014744 (14546.6 m)
      tertiary             25,380       59.5      515.5     15463.0    1,246      4.91%  w221164472 (15463.0 m)
      motorway_link         9,908       99.2      291.5      1340.2       21      0.21%  w159605399 (1340.2 m)
      track                 8,136      221.2     1172.4     16020.7    1,280     15.73%  w186083285 (16020.7 m)
      motorway              7,486      145.4      570.3      7604.1      394      5.26%  w1300439250 (7604.1 m)
      unclassified          5,460      118.1      492.0      8323.4      234      4.29%  w47283886 (8323.4 m)
      (no highway tag)      4,064      420.3     1975.0    133307.8    1,211     29.80%  w338528425 (133307.8 m)
      trunk                 1,939       50.0      220.5      6586.4       31      1.60%  w373549984 (6586.4 m)
      primary_link          1,720       48.6      110.0       596.4        0      0.00%  w22727115 (596.4 m)
      secondary_link          961       40.9       95.3       473.1        0      0.00%  w4341154 (473.1 m)
      tertiary_link           418       34.4       79.3       257.6        0      0.00%  w1466603409 (257.6 m)
      trunk_link              178       63.6      220.4       497.1        0      0.00%  w63062979 (497.1 m)
      footway                  94       24.0      145.6       262.4        0      0.00%  w385648322 (262.4 m)
      road                      3       61.5      145.1       145.1        0      0.00%  w24851748 (145.1 m)
      steps                     1       62.5       62.5        62.5        0      0.00%  w37120567 (62.5 m)

      ALL CLASSES          564,329       68.2      322.4    133307.8   11,229      1.99%
      FEATURES read=564,329 measured=564,329 non-linestring=0 under-2-nodes=0
      residential+living_street+service combined: n=412,529 median=71.1 m p90=309.5 m max=10162.4 m over-800m=6,319 (1.53%)

  RECONCILIATION to meta.json's 560,208 (R3), every row accounted for: residential 99,715 = 99,715;
  living_street 195 = 195; unclassified 5,460 = 5,460; road 3 = 3; primary 43,815 + primary_link 1,720 =
  45,535; secondary 42,237 + 961 = 43,198; tertiary 25,380 + 418 = 25,798; motorway 7,486 + 9,908 = 17,394;
  trunk 1,939 + 178 = 2,117. Two rows fall SHORT of meta.json and the gap is named: service 312,619 vs
  312,645 (-26) and track 8,136 vs 8,148 (-12) - 38 closed ways that osmium export emits as polygons and
  `--geometry-types=linestring` therefore drops. 560,208 - 38 = 560,170 = 564,329 measured - 4,064
  (no highway tag) - 94 footway - 1 steps, those 4,159 being the POI/park/coastline ways the T-0107 keep-pass
  also kept. Nothing else is missing.

- 2026-09-19T20:37:43Z STAGE 1b LANDED - the same script over T-0213's window (window-tagged-1.osm.pbf, the
  exact bytes that built graph-la-window), because that is the population any run on the routed pair could
  come from. Same command with `--source window-tagged-1.osm.pbf`:

      WAY LENGTHS source=window-tagged-1.osm.pbf radius_m=6371008.8 metric=haversine-sum
      percentile=nearest-rank median=mean-of-two-middle long_way_threshold_m=800
      highway class         count   median m      p90 m       max m   n>800m  share>800m  longest way
      -----------------------------------------------------------------------------------------------------------
      residential           2,562      140.7      616.3      4036.1      158      6.17%  w13452810 (4036.1 m)
      living_street             4      132.3      310.0       310.0        0      0.00%  w13308585 (310.0 m)
      service               6,817       69.5      216.6      3688.7       33      0.48%  w172569450 (3688.7 m)
      track                   988      196.6      960.2      8696.2      125     12.65%  w228166785 (8696.2 m)
      tertiary                406       81.8     1276.7     15463.0       67     16.50%  w221164472 (15463.0 m)
      (no highway tag)        374      800.8     3492.3     43912.0      188     50.27%  w829182866 (43912.0 m)
      secondary               277      106.9     1048.6      5869.8       35     12.64%  w13295089 (5869.8 m)
      trunk                   251       75.9      573.6      3494.2       15      5.98%  w73090074 (3494.2 m)
      primary                 181       84.2      695.9      4252.0       16      8.84%  w74865586 (4252.0 m)
      unclassified             94      149.5     1232.5      8212.8       15     15.96%  w149210418 (8212.8 m)
      motorway_link            73      164.7      369.1       639.3        0      0.00%  w159240659 (639.3 m)
      motorway                 48      480.4     1294.6      3130.1       15     31.25%  w55468517 (3130.1 m)
      trunk_link               14       57.9      140.4       149.8        0      0.00%  w38340887 (149.8 m)
      primary_link             10       78.9      160.6       261.2        0      0.00%  w42777610 (261.2 m)
      tertiary_link             8       12.6       62.7        62.7        0      0.00%  w813998713 (62.7 m)
      secondary_link            6       11.4       13.5        13.5        0      0.00%  w724343596 (13.5 m)

      ALL CLASSES           12,113       88.3      496.3     43912.0      667      5.51%
      FEATURES read=12,113 measured=12,113 non-linestring=0 under-2-nodes=0
      residential+living_street+service combined: n=9,383 median=78.5 m p90=320.1 m max=4036.1 m over-800m=191 (2.04%)

  The window holds 12,113 linestring ways against the readback's 12,402 ways (the difference is the closed
  ways export drops plus the non-way records); residential+living_street+service is 9,383 of them.

- 2026-09-19T20:37:43Z STAGE 2 LANDED - the routed pair at lambda 0 and lambda 8 over T-0213's window graph,
  and the boundary from R1 demonstrated rather than described. The graph was COPIED out of the main checkout
  (services/routing/work/t0213/graph-la-window, 5.1 MB) into this worktree's gitignored
  services/routing/work/t0224/ and the copy is what ran, so the read-only input was never opened for write.
  `python services/routing/tests/measure_runs.py` printed:

      ROUTED PAIR from=34.0387,-118.5836 to=34.0938,-118.6045  graph=.worktrees/T-0224/services/routing/work/t0224/graph-la-window
      T-0213 recorded car_fast time_ms=507242 distance_m=8121.6 on this pair
      PER-REQUEST MODELS (profiles/scenic_lambda_bands.json into profiles/car_scenic_request.json):
        lambda=0 model=[{"if": "scenic_score >= 7", "multiply_by": "1"}, {"else_if": "scenic_score >= 4", "multiply_by": "1"}, {"else": "", "multiply_by": "1"}]
        lambda=8 model=[{"if": "scenic_score >= 7", "multiply_by": "1"}, {"else_if": "scenic_score >= 4", "multiply_by": "0.2"}, {"else": "", "multiply_by": "0.111111"}]
      ROUTE:
        ROUTE profile=car_fast model=- time_ms=526739 distance_m=8230.4
        ROUTE profile=car_scenic model=lambda-0.json time_ms=526739 distance_m=8230.4
        ROUTE profile=car_scenic model=lambda-8.json time_ms=526739 distance_m=8230.4
      PATH DETAILS PROBE (unknown --mode, to show the CLI surface):
        exit=0 stdout-without-log-lines='SCENIC_EV present=true bits=4 max=10\nGRAPH nodes=21137 edges=24057'
      IMAGE DEPENDENCIES (why there is no HTTP /route to ask for details=):
        services/routing/plugins/scenic-score-parser/pom.xml artifactIds: scenic-score-parser, graphhopper-core, snakeyaml, slf4j-simple, junit-jupiter, maven-surefire-plugin, maven-shade-plugin
        graphhopper modules other than graphhopper-core in the image: NONE

  PER R2, the endpoints are 108.8 m of route longer than T-0213's (8230.4 m against its 8121.6 m, +1.34%):
  the same corridor, snapped to slightly different ends, because T-0213 recorded the pair only in prose. It
  is NOT claimed to be the identical request. What reproduces exactly is the SHAPE T-0213 recorded: car_fast,
  lambda 0 and lambda 8 return one and the same route (identical time_ms AND distance_m), on a graph whose
  corridor - Topanga Canyon Boulevard, scored 8 - sits in the never-penalized `high` band at every lambda.

  THE LONGEST RESIDENTIAL/SERVICE RUN IS NOT MEASURED, and the reason is R1's, now demonstrated: the
  unknown-mode run loads the very same graph (`SCENIC_EV present=true bits=4 max=10`,
  `GRAPH nodes=21137 edges=24057`) and then prints NOTHING about the route - that is the whole CLI surface
  beside `--mode route`'s four fields and `--mode probe`'s `PROBE way=<id> edges=<n> scenic_score=<csv>`.
  None of them carries road_class, a per-edge distance, or the routed edge sequence, so no run - not even a
  bound on one - can be honestly read out of this image.
