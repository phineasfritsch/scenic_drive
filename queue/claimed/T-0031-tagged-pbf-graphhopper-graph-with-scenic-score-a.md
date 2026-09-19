---
id: T-0031
title: Tagged PBF -> GraphHopper graph with scenic_score as an encoded value, deployed to the VPS
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T01:02:14Z
lease_expires_at: 2026-09-19T11:02:14Z
worktree: .worktrees/T-0031
branch: task/T-0031
exclusive: []
touches: [services/etl/, services/routing/]
pins_affected: []
reviewer: null
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance:
  - "FIRST SLICE (this promotion): the digest-pinned GraphHopper image imports .worktrees/T-0025/services/etl/inputs/vermont-osm.pbf (45,880,330 bytes == manifest.yaml) in WSL with the scenic_score TagParser plugin and the car_scenic_base profile; the import log's way/edge counts quoted"
  - "RED BY NAME: T(lambda) non-decreasing over {0,1,2,4,8} on every fixture (plan line 215) - red with a deliberately inverted band multiplier, then green; the five durations per fixture printed and quoted"
  - "the second half (the Bay Area graph, rsync, the atomic symlink flip, N-1 kept) stays behind T-0168 and is not claimed by this slice"
---
## Brief

osmium writes `scenic_score=0..10` back onto ways; the ~40-line GraphHopper TagParser plugin
registers it as an encoded value so `car_scenic` custom models can reference it. Import in WSL2, rsync the
graph-cache to the RackNerd box, atomic symlink flip keeping N-1.

RED: request a route with the lambda penalty at 0 and at 8 -> duration must be monotonically non-decreasing.
That is the property the whole budget search depends on, and it is cheap to check the moment the graph exists.

## Log
- 2026-09-18T19:52:17Z header corrected by agent/claude-fable-5-1 (13:13 panel, grounded): this task's own brief has osmium write
  `scenic_score=0..10` back onto ways, and T-0146 is the only producer of that value; `depends_on: []` said
  otherwise, and `ops/queue-next` reads headers, not prose. T-0029 (blocked, owned, with a named reviewer)
  has the same missing dependency - T-0146's brief says "Unblocks T-0029" - and is left for its owner.
- 2026-09-18T20:57:28Z amended by agent/claude-fable-5-1 (14:13 panel, grounded): (a) depends_on now names T-0168, the task that
  actually writes `scenic_score` onto ways (T-0146 was cut to its fixture half). (b) This task's RED tests
  lambda at 0 and at 8 only; plan line 215 reads "`T(lambda)` non-decreasing over {0,1,2,4,8} on every
  fixture" - the RED must run all five and assert each step. (c) The property is about the TagParser's
  encoded value and the custom model, not about California: the FIRST SLICE imports a small extract already
  on this box (`vermont-osm.pbf`, manifest-pinned, 45,880,330 bytes; or the filtered sfbay extract in
  `.worktrees/T-0028/services/etl/work/sfbay/`) in WSL and proves monotonicity there; the rsync, the atomic
  symlink flip and the full Bay Area graph stay in this task's second half.
- 2026-09-19T00:40:47Z PROMOTED to ready/ for its FIRST SLICE by agent/claude-fable-5-1 (17:13 panel, STRATEGY, grounded): the Vermont
  extract is on disk byte-matching the manifest, and the T(lambda) property is about the TagParser and the
  custom model, not California - the 20:57:28Z entry already ruled the slice. depends_on stays [T-0168] for
  the second half. Vermont carries no scenic_score tags: the slice tags them itself from a synthetic rule
  (e.g. curvature-only) and says so, or reads T-0146's assembler over a Vermont way-record fixture - rule it.
- 2026-09-19T00:49:41Z LA FIRST, by agent/claude-fable-5-1 (the owner lives in Los Angeles - memory user-lives-in-la): after the Vermont first slice, the FIRST served graph is LA (regions/la), sfbay second - the M3 exit 'you drive engine output from the CLI' is an LA drive; the plan's Bay Area fixtures stay the CI golden set.
- 2026-09-19T01:02:14Z claimed by agent/claude-opus-5; lease until 2026-09-19T11:02:14Z
- 2026-09-19T01:15:26Z RULINGS BEFORE CODE by agent/claude-opus-5 (OWNER, AUTHOR of this slice). Every disagreement
  between plan, Brief, code and reality, ruled here first.
  R1 SCOPE. FIRST SLICE only: `services/routing/` does not exist on main and is created here. No VPS, no rsync,
     no atomic symlink flip, no N-1, no Bay Area graph and no LA graph - those stay in the second half behind
     T-0168, which owns the real `scenic_score` writer.
  R2 SERIAL-ONLY FILES. CLAUDE.md makes `services/routing/profiles/*.json` and `services/routing/config.yml`
     serial-only. The header declares `exclusive: []`. Checked, not assumed: `grep -rn "services/routing"
     queue/claimed/*.md queue/ready/*.md` on main returns exactly one line, this task's own `touches:`. Nobody
     else can be writing them today, so they are created without a lock and the header is left untouched.
  R3 VERSION AND IMAGE. No upstream GraphHopper image is used: there is no published image that carries a
     third-party TagParser, so `services/routing/Dockerfile` builds ours. GraphHopper 11.0 (the newest version
     in Maven Central's `com/graphhopper/graphhopper-core/maven-metadata.xml`, printed this session). Both
     stages are digest-pinned, pulled and recorded this session:
       maven:3.9-eclipse-temurin-21@sha256:c2a2c58516d160f43b50f12baa427ca86989e0bc942609e04aff61da5d9a7d74
       eclipse-temurin:21-jre@sha256:49e21e16e3c86eb7816a44a67549910ed090fbeb40c29c525d58bf5e02e91b0f
       python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea (tagger)
     The Maven build runs INSIDE the builder stage; there is no java on the WSL host and none is installed.
  R4 NO HTTP SERVER IN THIS SLICE - a disagreement with the Brief's word "requests", ruled against it.
     GraphHopper's web server has no configuration hook that can register a third-party encoded value:
     registration is `GraphHopper.setImportRegistry(ImportRegistry)`, a Java call on the GraphHopper instance,
     and inside the Dropwizard bundle that instance is owned by `GraphHopperManaged` (verified against the
     11.0 jar with javap this session: `setImportRegistry(com.graphhopper.routing.ev.ImportRegistry)` is the
     only entry point). So this slice owns the instance in a small runner, `ScenicRouterMain`, which reads the
     SAME `services/routing/config.yml` the server will read (its `graphhopper:` node), imports the graph and
     answers the fixed A->B pair. The five lambdas are five per-request custom models through one loaded
     graph, not five HTTP calls; the runner still sets `ch.disable=true` on every request and the config
     declares no CH profiles, so every query is flexible by construction. The Dropwizard `server:` section and
     `/route` arrive with the second half; config.yml carries no `server:` block today because nothing here
     exercises one.
  R5 THE ENCODED VALUE. Name `scenic_score`; `IntEncodedValueImpl("scenic_score", 4, false)` - unsigned, 4
     bits, one direction. 4 bits stores 0..15; the tag contract is 0..10. A way with NO `scenic_score` tag
     gets 0, per T-0168's REFUSED ruling (no tag is no evidence, never "average"); so does an unparsable or
     negative value; a value above 10 clamps to 10.
  R6 SYNTHETIC SCORES. Vermont carries no `scenic_score` tags. `services/routing/tools/synthetic_scenic_tags.py`
     (pyosmium) writes `scenic_score = way_id % 11` on every way that has a `highway` tag and stamps the output
     PBF's own header `generator` with `SYNTHETIC-T-0031-wayid-mod-11`, so the marker lives in the built
     artifact's metadata and not in a comment. THESE SCORES ARE NOT A SCENIC INDEX. Chosen over a curvature
     rule because the property under test is the encoded value and the custom model; a curvature pass would
     put a second unproven computation inside the thing being proven. T-0168/T-0146 own the real value.
  R7 THE PER-REQUEST MODEL. `services/routing/profiles/car_scenic_request.json` is the plan's block MINUS
     (a) the anti rat-run `road_class == RESIDENTIAL && scenic_score < 7` rule and (b) the closure `areas`.
     Both are Problem A request-builder concerns, both are lambda-INDEPENDENT, and (a) would break the
     feasibility check below by making the lambda=0 model differ from car_fast. What is left is exactly the
     three lambda-scaled bands, so the edge weight is `w0(e) + lambda*c(e)` with `c(e) >= 0` - the shape the
     plan's bisection depends on.
  R8 CAR_FAST. Same profile family, same safety gates, no scenic term, so lambda=0 must reproduce the car_fast
     duration exactly. Both profiles load `car_scenic_base.json`: the gates are safety and server-side.
     Motorway and trunk are NOT gated anywhere in this slice (product invariant: they score 0 and are
     penalized, never hard-excluded). The gates are private/no access, the positive-evidence unpaved surfaces,
     and track.
  R9 WHERE THE CHECK LIVES. `ops/` is outside this task's `touches: [services/etl/, services/routing/]`, so the
     Brief's `ops/test-routing-slice` is ruled out and its alternative taken: a pytest under
     `services/routing/tests/`, run `cd services/routing && python -m pytest tests -rs` on the Windows host,
     shelling into WSL for docker because docker exists only there. `ops/test` Tier 1c runs pytest for
     `services/etl` only, so this test is NOT in the `ops/test` count; wiring `ops/test-routing` (plan line
     199) is STILL OPEN for a task whose touches: include ops/.
  R10 MONOTONE ON DURATION. The Lagrangian argument gives a non-decreasing `w0 = time + distance_influence *
     distance`; the plan's property table asserts the DURATION. The test asserts the duration, as the plan
     says, and the five measured numbers are quoted below rather than reasoned about.
- 2026-09-19T02:10:09Z BUILT, and four rulings the build overturned, by agent/claude-opus-5. Every command below is
  quoted as it ran; every number is from its output.

  WHAT RUNNING IT CHANGED. Four things the plan and my own rulings got wrong, each found by a failure:
  (a) `pip install osmium==3.7.0` on python:3.12-slim installs a wheel that cannot load:
      `ImportError: libexpat.so.1: cannot open shared object file: No such file or directory`.
      Dockerfile.tagger installs `libexpat1 libbz2-1.0` first.
  (b) `ScenicRouterMain` resolved custom_model_files itself and GraphHopper.init resolves them again:
      `java.lang.IllegalArgumentException: Do not use custom_model_files and custom_model together`
      (GraphHopper.java:1628). The runner now hands init the profiles as config.yml wrote them.
  (c) GraphHopper 11 refuses to start without a key neither the plan nor the Brief mentions:
      `java.lang.IllegalArgumentException: Missing 'import.osm.ignored_highways'. Not using this parameter
      can decrease performance, see config-example.yml for more details` (GraphHopper.java:576). config.yml
      sets `footway, cycleway, path, pedestrian, steps`. It names NO motorway and NO trunk: the product
      invariant stands, they are scored 0 and penalized, never hard-excluded.
  (d) THE ONE THAT CHANGED A FILE FORMAT. R7 shipped the plan's `"multiply_by": "1 / (1 + 0.5 * λ)"`
      verbatim. GraphHopper's expression compiler refuses it:
      `profile=car_scenic model=lambda-0.json errors=[java.lang.IllegalArgumentException: Cannot compile
      expression: invalid operation '/']`
      So the plan's formula CANNOT live in a profile file. It already lives in the producer that ships:
      `services/api/src/customModel.ts` has `scenicBandMultipliers(lambda) = { high: 1, mid: 1/(1+0.5*lambda),
      low: 1/(1+lambda) }` and `formatMultiplier` serialising to 6 decimals with trailing zeros dropped.
      RULED: `profiles/car_scenic_request.json` becomes the body with `${high} ${mid} ${low}` placeholders and
      `profiles/scenic_lambda_bands.json` carries the five plan lambdas' multipliers as typed literals;
      `test_band_multipliers_match_the_plan` ties those literals back to the plan's formula and runs without
      docker. The red demonstration then edits DATA, never the test.

  THE INPUT, read where it lies (no copy into git, as T-0177 asks):
    ls -l .worktrees/T-0025/services/etl/inputs/vermont-osm.pbf -> 45880330 bytes, == manifest.yaml's
    `bytes: 45880330` for vermont-osm.pbf.

  BUILD AND IMPORT, all inside WSL (docker exists only there; no java on the host, the jar is built in the
  builder stage):
    wsl -e bash -lc "cd /mnt/c/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0031 && bash services/routing/build-slice.sh"
  Images, digests recorded at pull time this session with
  `docker image inspect --format {{index .RepoDigests 0}}`:
    maven:3.9-eclipse-temurin-21@sha256:c2a2c58516d160f43b50f12baa427ca86989e0bc942609e04aff61da5d9a7d74
    eclipse-temurin:21-jre@sha256:49e21e16e3c86eb7816a44a67549910ed090fbeb40c29c525d58bf5e02e91b0f
    python:3.12-slim@sha256:78387bc3881b8273120a12ebe6c1ab22b018ccc2c9adf565ae1ac9b536e184ea
  GraphHopper 11.0 from Maven Central; the running jar prints
    `com.graphhopper.GraphHopper - version 11.0|2025-10-14T14:28:00Z (9,24,7,5,2,9)`.

  SYNTHETIC TAGGING (R6), its own output line:
    TAGGED ways=434265 tagged=161240 stamp=SYNTHETIC-T-0031-wayid-mod-11 out=/out/vermont-scenic.osm.pbf

  THE IMPORT LOG's way and edge counts, verbatim:
    pass1 - finished, processed ways: 434,265, accepted ways: 126,856, way nodes: 1,695,935, relations: 8,241
    pass2 - finished, processed ways: 434,265, way nodes: 1,695,935, nodes with tags: 14,912, node tag capacity: 1,056,768, ignored barriers at junctions: 4
    Finished reading OSM file: /data/vermont-scenic.osm.pbf, nodes: 212,912, edges: 240,968, zero distance edges: 1,153
    PrepareRoutingSubnetworks - car_scenic - Marked 182506 subnetworks (biggest: 374 edges) -> 2 components(s) remain (smallest: 498, biggest: 267562 edges), total marked edges: 22897
    GraphHopper - nodes: 212,912, edges: 240,968
  and the runner's own two lines, which are what say the encoded value survived the import:
    SCENIC_EV present=true bits=4 max=10
    GRAPH nodes=212912 edges=240968

  RED BY NAME, attempt 1 - the Brief's literal instruction, the `>= 4` band's multiplier grown with lambda
  (mid = 1, 1.5, 2, 3, 5 in scenic_lambda_bands.json), then
    cd services/routing && python -m pytest tests -rs -s
  IT DID NOT GO RED on the property. Verbatim:
    T(lambda) ms: lambda=0: 5945246, lambda=1: 6092977, lambda=2: 6893354, lambda=4: 7383129, lambda=8: 8160864
    car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m
    1 failed, 2 passed in 24.90s
  Only `test_band_multipliers_match_the_plan` failed (`assert 1.5 == 0.6666666666666666`). REPORTED, not
  hidden: scaling ONE band up is, up to a constant, the same as penalizing the other two, so every pairwise
  ratio still moves one way and the duration still rises. Monotonicity is robust to that edit. What breaks it
  is a band whose penalty SHRINKS as lambda grows.

  RED BY NAME, attempt 2 - the `else` band (scenic_score < 4, where the motorways and trunks are) inverted so
  its penalty shrinks with lambda (low = 0.111111, 0.2, 0.333333, 0.5, 1), same command. Verbatim:
    _____________________ test_lambda_monotone_non_decreasing _____________________
    E           AssertionError: T(lambda) DECREASED at step lambda=0 -> lambda=1: 8208740 ms -> 7312085 ms
    E           assert 7312085 >= 8208740
    tests\test_lambda_monotone.py:128: AssertionError
    ___________________ test_lambda_zero_is_the_car_fast_route ____________________
    E       AssertionError: lambda=0 must be the car_fast route - the bisection's feasibility end - but car_fast is 5945246 ms and lambda=0 is 8208740 ms
    E       assert 8208740 == 5945246
    3 failed in 17.65s
  Both named checks fail, by name, naming the step. The table was then restored to the plan's values.

  GREEN, the same command, nothing else changed:
    .T(lambda) ms: lambda=0: 5945246, lambda=1: 6015807, lambda=2: 6908455, lambda=4: 7664327, lambda=8: 8491177
    .car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m
    .
    3 passed in 5.34s
  5945246 <= 6015807 <= 6908455 <= 7664327 <= 8491177, and lambda=0 reproduces car_fast to the millisecond
  and the metre.

  STILL OPEN, plainly:
  - The scores are SYNTHETIC (way id % 11). Nothing here says anything about which Vermont road is pretty.
  - Vermont only. No LA graph, no Bay Area graph, no region fixtures, no golden set.
  - No VPS, no rsync, no atomic symlink flip, no N-1 kept, no `/info` graph hash: the second half, behind
    T-0168, which owns the real scenic_score writer.
  - No HTTP surface: no Dropwizard `server:` block, no `/route`, no Worker-to-router request path (R4).
  - This pytest is NOT in the `ops/test` count: Tier 1c runs `services/etl` only and `ops/` is outside this
    task's touches:. `ops/test-routing` (plan line 199, GraphHopper container + 20 goldens) is unwritten.
  - No Java unit test for `ScenicScoreParser.parse` itself: the 0-for-no-tag and clamp-at-10 branches are
    exercised only through the import. A parser fixture belongs with the real scores.
  - One pair, one direction, one region: the plan says "on every fixture" and this is one fixture.
- 2026-09-19T02:47:15Z ACCEPTANCE RE-RUN at the final pre-review commit, by agent/claude-opus-5. The whole block,
  each line answered by a command re-run at this commit.

  A1 "the digest-pinned GraphHopper image imports .worktrees/T-0025/services/etl/inputs/vermont-osm.pbf
     (45,880,330 bytes == manifest.yaml) in WSL with the scenic_score TagParser plugin and the car_scenic_base
     profile; the import log's way/edge counts quoted" - MET, with one wording correction ruled at R3: the
     image is not a pinned GraphHopper image, it is OUR image built from digest-pinned maven and temurin bases,
     because no published GraphHopper image can carry a third-party TagParser. `ls -l` on the input prints
     45880330 bytes, the manifest's own `bytes:` for vermont-osm.pbf. Import log, quoted in the 02:10:09Z
     entry: processed ways: 434,265, accepted ways: 126,856; nodes: 212,912, edges: 240,968; and
     `SCENIC_EV present=true bits=4 max=10` from the runner over the graph it had just built.

  A2 "RED BY NAME: T(lambda) non-decreasing over {0,1,2,4,8} on every fixture (plan line 215) - red with a
     deliberately inverted band multiplier, then green; the five durations per fixture printed and quoted" -
     MET for the one Vermont fixture this slice has, and honestly qualified: the Brief's literal inversion (the
     `>= 4` band) did NOT go red, which is reported above with its five durations; the `else` band inverted the
     same way did, naming the step:
       AssertionError: T(lambda) DECREASED at step lambda=0 -> lambda=1: 8208740 ms -> 7312085 ms
     Re-run green at this commit, `cd services/routing && python -m pytest tests -rs -s`:
       .T(lambda) ms: lambda=0: 5945246, lambda=1: 6015807, lambda=2: 6908455, lambda=4: 7664327, lambda=8: 8491177
       .car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m
       .
       3 passed in 22.33s
     "every fixture" is one fixture here; see STILL OPEN.

  A3 "the second half (the Bay Area graph, rsync, the atomic symlink flip, N-1 kept) stays behind T-0168 and is
     not claimed by this slice" - MET. Nothing in the diff mentions rsync, a symlink, a VPS or a region;
     `depends_on: [T-0168]` is untouched and the header still reads `state: claimed`, `reviewer: null`.

  GATES, run bare at this commit:
    bash ops/lib/check-line-cap  -> P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines   EXIT 0
    bash ops/queue-check         -> QUEUE OK (175 tasks)   EXIT 0
    bash ops/check-pins --source-only -> PINS ok=11 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only   EXIT 0
      Run twice, both green with exactly that line and exit 0: once over the tree this commit was made from,
      and once again, to completion, after PR #105 was opened. The only files written between the two runs are
      services/routing/README.md and this task file, and no pin anchors on either. CI runs the same gate on the
      PR as `pins-source-only`.
  The new files' own lengths, `wc -l`: ScenicRouterMain.java 122, ScenicScoreParser.java 42,
  ScenicScoreImportRegistry.java 24, test_lambda_monotone.py 141, synthetic_scenic_tags.py 67,
  config.yml 32, Dockerfile 24, Dockerfile.tagger 18 - all under the 300-line cap.
- 2026-09-19T02:53:32Z correction by agent/claude-opus-5: the check-pins line in the entry above carried two
  numbers no command printed - a "~35 min" duration and an inferred launch time. Both are gone; what is left is
  what ran: the same PINS line twice, exit 0 both times, the second run finishing after PR #105 was opened.
- 2026-09-19T02:55:03Z mutation-population rule, ruled by agent/claude-opus-5: CLAUDE.md requires a mutation population under
  ops/mutate/ for "a new numeric module (under `services/etl/etl/` or `Sources/`)". Nothing in this slice is
  either: the new code is Java under services/routing/ plus one pyosmium copier, and the numeric content is a
  4-bit encoded value and a five-row multiplier table, both already pinned by literals in the tests. ops/ is
  also outside this task's touches:, so a population could not be committed here. STILL OPEN for the task that
  owns the real scenic_score arithmetic (T-0168/T-0146), where the numbers are actually computed.
- 2026-09-19T03:13:28Z **Record corrections from the read-only verification of this slice, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier found both images in WSL with RepoDigests matching the Dockerfile
  FROM lines and the Log verbatim, the pom pinned to graphhopper 11.0, ran the slice's test ONCE (`3 passed in
  18.66s`, no skip section - the container ran) with the five durations identical to the Log's GREEN and the
  PR body and non-decreasing, and found the tree clean at 2f48373 with CI green; these are text.** (a) The
  02:10:09Z entry quotes the tagger's line `TAGGED ways=434265 tagged=161240 stamp=SYNTHETIC-T-0031-wayid-mod-11`;
  the only surviving output (`services/routing/work/build-slice.log`) says "kept existing vermont-scenic.osm.pbf"
  and carries the header stamp, not that line - the tagged PBF is real (46,171,990 bytes), `tagged=161240` rests
  on the author's word. (b) R4's "verified against the 11.0 jar with javap this session" quotes no javap output;
  ScenicRouterMain.java calls `hopper.setImportRegistry` and the import succeeded, which is the evidence that
  exists. (c) The two RED runs (attempt 1 not red on the property; attempt 2 red by name) were not repeated by
  the verifier - their message format matches tests/test_lambda_monotone.py exactly. (d) DESIGN CAVEAT for
  STILL OPEN, not a false claim: tests/test_lambda_monotone.py skips the two routed tests when the graph-cache or
  the docker image is absent, so CI's core job passes with `1 passed / 2 skipped` and never checks the property;
  the real gate is `ops/test-routing` (plan line 199: container + goldens), which this slice leaves unwritten and
  names as open.
- 2026-09-19T03:34:33Z REVIEW FAIL of PR #105 at 7b7401a by agent/rv1-pr105 (reviewer, not the owner and not the
  orchestrator). Reviewed in .worktrees/rv1-pr105, removed at the end; nothing written in .worktrees/T-0031.
  RE-RUN AT THIS HEAD. The routed acceptance line, once, reusing the existing WSL image and a COPY of the
  graph-cache (no image rebuild, no re-import): `cd services/routing && python -m pytest tests -rs -s` ->
    T(lambda) ms: lambda=0: 5945246, lambda=1: 6015807, lambda=2: 6908455, lambda=4: 7664327, lambda=8: 8491177
    car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m
    3 passed in 25.30s
  identical to the Log's GREEN, no skip section. `bash ops/check-pins --source-only` ->
  `PINS ok=11 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only` EXIT 0, the quoted line exactly.
  `wc -l` re-measured: 122 / 42 / 24 / 141 / 67 / 32 - the 02:47:15Z numbers are right. `gh pr checks 105`:
  core pass, pins-source-only pass. Only PR #105 touches services/routing, so the serial-only files needed no
  lock. The band table RE-DONE by hand at 6 dp: lambda=2 mid 1/2 = 0.5 and low 1/3 = 0.333333; lambda=8 mid
  1/5 = 0.2 and low 1/9 = 0.111111 - the file's five rows are the plan's numbers. R4 and R5 upheld.
  BLOCKING, one. The thresholds in profiles/car_scenic_request.json are load-bearing and nothing checks them.
  Mutant, alone, control green: `"scenic_score >= 7"` -> `"scenic_score >= 0"` puts every edge in the `high`
  band, whose multiplier is "1" at every lambda, so the per-request model does nothing - and the suite is
  green, `3 passed in 25.16s`, with
    T(lambda) ms: lambda=0: 5945246, lambda=1: 5945246, lambda=2: 5945246, lambda=4: 5945246, lambda=8: 5945246
  No NAMED test red: the band test never reads this file's expressions, a constant IS non-decreasing, and
  lambda=0 == car_fast is then trivially true. A second mutant sharpens it: growing BOTH penalized bands with
  lambda (mid 1,1.5,2,3,5 and low 1,2,3,5,9 - the Brief's inversion applied to both bands, not one) leaves both
  routed tests green at 5945246, 6366659, 6636548, 6657975, 7708833; only the literal table test goes red. So
  at this head the routed property distinguishes neither a dead model nor an inverted one from the plan's.
  One assertion closes it - that the penalty bites, e.g. T(8) > T(0) - demonstrated red under the mutant above
  and green restored.
  A third mutant, for the record, was CAUGHT: hard-excluding motorway/trunk in the request model (the invariant
  CLAUDE.md forbids optimizing away) makes Burlington->Rutland unroutable -
  `ConnectionNotFoundException`, `1 passed, 2 errors`. Caught by unroutability, not by a named assertion.
  RECORDABLE: A3's "nothing in the diff mentions rsync, a symlink, a VPS or a region" is loose (README.md and
  Dockerfile both mention them, to say they are not here) - the substance holds; the parser's no-tag and
  clamp-at-10 branches are not merely untested but unreachable on this fixture (way_id % 11 never exceeds 10,
  and the tagger tags every highway way); scenic_lambda_bands.json is a test fixture living in the image's
  custom-model directory; and pins/PINS.yaml P-ROUTE-01 (`pending: T-0135`) loses its stated reason once
  services/routing exists - the release now has one anchor, pom.xml's `<graphhopper.version>11.0</graphhopper.version>`.
- 2026-09-19T04:01:08Z FIX for the review FAIL of PR #105, by agent/claude-opus-5 (OWNER and FIXER; the reviewer's entry is
  directly above, verbatim, appended before any code was written). ONE blocking finding, B1, plus the two
  recordables the reviewer asked to be carried.

  REPRODUCED FIRST, the reviewer's mutant alone, in .worktrees/T-0031 at 7b7401a: in
  profiles/car_scenic_request.json `"scenic_score >= 7"` -> `"scenic_score >= 0"`, nothing else
  (`git diff --stat`: 1 file changed, 1 insertion(+), 1 deletion(-)), then
    cd services/routing && python -m pytest tests -rs -s
    T(lambda) ms: lambda=0: 5945246, lambda=1: 5945246, lambda=2: 5945246, lambda=4: 5945246, lambda=8: 5945246
    car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m
    3 passed in 27.50s
  The constant table, the whole suite green, no skip section: confirmed exactly as reported. Restored with
  `git checkout -- services/routing/profiles/car_scenic_request.json`; `git status --short` shows no profile.

  RULINGS BEFORE CODE (the author rule), all four:
  R6 THE PROFILES' VALUES DO NOT CHANGE. B1 is a hole in the TESTS, not in the model: the thresholds 7 and 4
     and the five-row table are the plan's numbers, and the reviewer re-derived the table at 6 dp and upheld
     it. The fix is assertions plus one new test file. No profile, no config, no Java, no Dockerfile, no
     image rebuild and no re-import.
  R7 THE MARGIN. "the penalty bites" needs a number, not a bare `>`, which a 1 ms difference would satisfy.
     Ruled from the five measured durations on this fixture: 8491177 vs 5945246 is +42.8%. BITE_FLOOR = 0.05
     (5%) - an order of magnitude of headroom below what the model delivers, and the router is deterministic
     over a fixed graph (the five integers reproduce run to run, three sessions now), so the floor survives
     another region without admitting a dead model.
  R8 WHERE THE CHECKS LIVE. The band thresholds, the table's digits and the motorway/trunk invariant are
     properties of FILES, and they must not sit behind the docker skip - which is every CI runner this repo
     has. They go in a new container-free tests/test_profiles_static.py, one concern (the shipped profiles
     and config read as files). The bite assertion is a property of the routed durations, so it belongs in
     tests/test_lambda_monotone.py beside the monotonicity it strengthens.
  R9 ANCHORS. The invariant check anchors on the profiles' own expression strings and on config.yml's
     `import.osm.ignored_highways` key - identifiers and a config key, never a comment (CLAUDE.md).

  WHAT CHANGED, two files, both under services/routing/tests/:
  - tests/test_lambda_monotone.py 141 -> 174 lines: `BITE_FLOOR = 0.05` and `test_lambda_penalty_bites` -
    T(lambda=8) strictly above T(lambda=0) by that floor, the message naming both lambdas and both
    durations, and at least one of the five steps strictly rising.
  - tests/test_profiles_static.py, NEW, 141 lines, no container and no graph, so it runs in CI where the
    routed tests skip: the three bands' thresholds are exactly [7, 4] read off `scenic_score >= N` with the
    ${high}/${mid}/${low} placeholders and the else band; the five lambdas are present; the table matches
    TYPED LITERALS (deliberately not a second re-computation of the formula -
    test_band_multipliers_match_the_plan already checks it against `1/(1+0.5*lambda)`, so this one checks
    the digits the file actually carries); every band's multiplier is non-increasing across 0,1,2,4,8;
    neither profile gates on MOTORWAY or TRUNK; config.yml's import.osm.ignored_highways names neither.

  RED BY NAME, each mutant alone, each restored with `git checkout --` and `git status --short` checked
  after it:
  (a) B1's own mutant (`scenic_score >= 0`), whole suite, `python -m pytest tests -rs -s --tb=line -rf`:
        FAILED tests/test_lambda_monotone.py::test_lambda_penalty_bites
        FAILED tests/test_profiles_static.py::test_request_model_bands_are_the_plan_thresholds
        2 failed, 7 passed in 34.43s
      AssertionError: the scenic penalty does not BITE: lambda=8 is 5945246 ms against lambda=0 at 5945246
      ms, short of the +5% (6242508 ms) this asserts. A per-request model that matches every edge at
      multiplier 1 gives a constant T(lambda) and passes every other check in this file.
      AssertionError: car_scenic_request.json: band thresholds are [0, 4], the plan's are [7, 4]. A first
      threshold of 0 puts every edge in the never-penalized band and the whole per-request model dies with
      every routed test still green.
  (b) M1, the reviewer's generalisation of this Log's own 02:10:09Z disclosure - BOTH penalized bands grown
      with lambda (mid 1, 1.5, 2, 3, 5 and low 1, 2, 3, 5, 9), container-free run:
        FAILED tests/test_profiles_static.py::test_band_table_matches_the_plan_literals
        FAILED tests/test_profiles_static.py::test_band_multipliers_never_grow_with_lambda
      AssertionError: scenic_lambda_bands.json: the mid band's multiplier GREW from lambda=0 (1.0) to
      lambda=1 (1.5) - a larger lambda must never make a band cheaper
      RECORDED as the reviewer asked: this Log had measured only the ONE-band inversion and reported it as
      not red on the property; the reviewer measured both bands inverted and got T(lambda) = 5945246,
      6366659, 6636548, 6657975, 7708833 with BOTH routed tests green. So the routed property tells neither
      a dead model nor an inverted one from the plan's - only the table's digits do, and now two named
      tests read them.
  (c) M3, the CLAUDE.md invariant, attacked twice, each alone, each container-free:
      a fourth rule `{ "if": "road_class == MOTORWAY || road_class == TRUNK", "multiply_by": "0" }` in
      profiles/car_scenic_base.json ->
        FAILED tests/test_profiles_static.py::test_no_profile_hard_excludes_motorway_or_trunk
        AssertionError: car_scenic_base.json gates on 'road_class == MOTORWAY || road_class == TRUNK':
        motorway and trunk are penalized by the band model, never hard-excluded. Hard gates are safety only
        - unpaved, private/no access, track.
      and `import.osm.ignored_highways: motorway, trunk, footway, ...` in config.yml ->
        FAILED tests/test_profiles_static.py::test_ignored_highways_keeps_motorway_and_trunk
        AssertionError: config.yml drops ['motorway', 'trunk'] at import: motorway and trunk must reach the
        graph and be penalized there (scenic_score 0), never hard-excluded.
      RECORDED: before this commit the invariant was guarded on this fixture only by Burlington->Rutland
      becoming unroutable (the reviewer's ConnectionNotFoundException, `1 passed, 2 errors`) - an accident
      of the pair chosen, not an assertion. Both new checks need no container, so they hold on every fixture
      and in CI.

  ACCEPTANCE RE-RUN at this final commit, the whole block, each line answered by a command re-run now.

  A1 "the digest-pinned GraphHopper image imports ... vermont-osm.pbf (45,880,330 bytes == manifest.yaml) in
     WSL with the scenic_score TagParser plugin and the car_scenic_base profile; the import log's way/edge
     counts quoted" - MET, unchanged by this commit and deliberately NOT re-imported: no profile, config,
     Java, pom or Dockerfile byte changed, so the graph-cache and both images are the same artifacts the
     02:10:09Z entry and the reviewer both ran against. `ls -l` on the input now: 45880330 bytes, the
     manifest's own `bytes:`. The import log's counts stand as quoted there (processed ways: 434,265,
     accepted ways: 126,856; nodes: 212,912, edges: 240,968; `SCENIC_EV present=true bits=4 max=10`), and
     the wording correction ruled at R3 (our image, built from digest-pinned maven/temurin bases, not a
     published GraphHopper image) still applies.

  A2 "RED BY NAME: T(lambda) non-decreasing over {0,1,2,4,8} on every fixture (plan line 215) - red with a
     deliberately inverted band multiplier, then green; the five durations per fixture printed and quoted" -
     MET, and materially stronger than at 7b7401a: the property no longer passes on a constant. Green,
     `cd services/routing && python -m pytest tests -rs -s`:
       .T(lambda) ms: lambda=0: 5945246, lambda=1: 6015807, lambda=2: 6908455, lambda=4: 7664327, lambda=8: 8491177
       ..car_fast: 5945246 ms / 107153.8 m   lambda=0: 5945246 ms / 107153.8 m
       ......
       9 passed in 33.29s
     5945246 <= 6015807 <= 6908455 <= 7664327 <= 8491177, identical to the 02:47:15Z GREEN and to the
     reviewer's own re-run at this head; lambda=8 is +42.8% over lambda=0; lambda=0 reproduces car_fast to
     the millisecond and the metre. 9 = 3 routed tests (monotone, bites, lambda=0 == car_fast) + 6 that need
     no container. "every fixture" is still one fixture here; see STILL OPEN.

  A3 "the second half (the Bay Area graph, rsync, the atomic symlink flip, N-1 kept) stays behind T-0168 and
     is not claimed by this slice" - MET, with the reviewer's correction taken: the 02:47:15Z sentence
     "Nothing in the diff mentions rsync, a symlink, a VPS or a region" is LOOSE and is withdrawn -
     README.md carries the row "Serving, rsync, symlink flip, LA and Bay Area graphs | Not here." and the
     Dockerfile says "the VPS in this task's second half has 4 GB for everything"; both mention them to say
     they are not here. The substance holds: none of the second half is implemented, `depends_on: [T-0168]`,
     `state: claimed` and `reviewer: null` are untouched, and this commit adds only tests.

  GATES, run bare at this commit (no pipe; the exit status is the command's own):
    bash ops/lib/check-line-cap  -> P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines   EXIT 0
    bash ops/queue-check         -> QUEUE OK (175 tasks)   EXIT 0
    bash ops/check-pins --source-only -> PINS ok=11 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only   EXIT 0
  `wc -l` re-measured over every tracked file of services/routing at this commit, not just the changed ones:
    .dockerignore 4, .gitignore 4, Dockerfile 24, Dockerfile.tagger 18, README.md 23, build-slice.sh 56,
    config.yml 32, pom.xml 72, ScenicRouterMain.java 122, ScenicScoreImportRegistry.java 24,
    ScenicScoreParser.java 42, car_scenic_base.json 12, car_scenic_request.json 7,
    scenic_lambda_bands.json 7, pyproject.toml 9, test_lambda_monotone.py 174,
    test_profiles_static.py 141, synthetic_scenic_tags.py 67 - 838 total, none over the 300-line cap.

  STILL OPEN, plainly, after this fix:
  - The routed tests still SKIP without docker, so CI still never runs the T(lambda) property itself;
    `ops/test-routing` (plan line 199: container + 20 goldens) is still unwritten and ops/ is outside this
    task's touches:. What CI gained here is the FILES (thresholds, table, invariant), not the ROUTE.
  - The bite floor is one number ruled on one fixture: 5% comes from Vermont's +42.8%. A region whose
    scenic detour is genuinely cheaper than 5% needs the floor re-ruled in the Log, not deleted.
  - Unchanged from 02:10:09Z: the scores are SYNTHETIC (way id % 11); Vermont only, one pair, one direction;
    no VPS, rsync, symlink flip, N-1 or `/info` hash; no HTTP surface; no Java unit test for
    ScenicScoreParser.parse; this pytest is still outside the `ops/test` count.
  - The reviewer's remaining recordables, for the tasks that own them: the parser's no-tag and clamp-at-10
    branches are UNREACHABLE on this fixture (way_id % 11 never exceeds 10, and the tagger tags every
    highway way), not merely untested; scenic_lambda_bands.json is a five-row fixture living in the shipped
    custom-model directory (/app/profiles in the image) and could be named or placed as one;
    pins/PINS.yaml P-ROUTE-01's `pending: T-0135` reason ("services/routing/ does not exist yet") expires
    when this merges, with pom.xml's `<graphhopper.version>11.0</graphhopper.version>` the single release
    anchor - pins/ is outside this task's touches:, so not this PR's job.
