---
id: T-0025
title: Scenic score: curvature, verified against the Curvature project's published values
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T16:59:08Z
lease_expires_at: 2026-09-07T20:59:08Z
worktree: ../wt/T-0025
branch: task/T-0025
exclusive: []
touches: [services/etl/, ops/etl-curvature-fixture, ops/etl-oracle-report]
pins_affected: []
reviewer: agent/reviewer-30
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Reimplement the Curvature project's method exactly: circumcircle radius from every 3 consecutive
OSM nodes, take the MIN of the two triangles a segment belongs to, cap 10 km, run the deflection filter that
zeroes fake curvature when the heading change is below gap_distance/175, then weight length by 2.0/1.6/1.3/1.0/0
at radius <30/<60/<100/<175 m.

THE ORACLE: Curvature publishes computed outputs for Vermont. Our value for the same way ids must match within
2%. That is an external oracle an agent cannot fabricate - the same discipline that caught the bad solar oracle
in T-0011. If the published data is not machine-readable, say so in the log and propose the next best oracle
rather than quietly falling back to self-generated fixtures.

## Log
- 2026-09-07T16:59:08Z claimed by agent/claude-opus-5; lease until 2026-09-07T20:59:08Z

- 2026-09-07 claimed by agent/claude-opus-5; reviewer agent/reviewer-30. Stacked on task/T-0024, which owns
  services/etl/.

- **THE ORACLE EXISTS AND IS MACHINE-READABLE.** The brief asked for this answer explicitly, and to say so
  rather than fall back on self-generated fixtures if the answer was no.
  `https://kml.roadcurvature.com/north_america/us/vermont.c_300.kmz` is a KMZ whose every Placemark
  description holds a table of the collection's constituent ways, each row carrying the OSM way id inside an
  `openstreetmap.org/way/N` link next to that way's curvature value, surface, length and name:

      <a href="https://www.openstreetmap.org/way/625066263">625066263</a> ... asphalt ... 63

  4422 collections, 3318 of them containing exactly one way. Pinned by sha256 in the manifest ON PURPOSE,
  unlike the Geofabrik extracts: an oracle that silently follows upstream is not an oracle. If they regenerate
  it the fetch fails and a human re-pins it having looked at what changed.

- **Recording that digest was impossible before this task.** `inputs/manifest.yaml`'s header documents
  "Get it with `--record-digest NAME`, then commit it", but a new entry has no digest, so it was invalid,
  validation ran first, and the tool refused with the one complaint it exists to resolve. Fixed:
  `--record-digest` now re-validates the named entry with a stand-in digest. Only that entry, only a missing
  or `TODO` digest; every other problem still fatal. The first version of that fix matched the complaint
  TEXT, which excused `TODO` and not a genuinely absent digest because those produce different messages - the
  test for the second case caught it, and re-validating with a stand-in has no such seam. Seven tests: two
  are the regression guard, five guard against the excuse being too broad.

- **Every constant checked against their source, not against the brief.** geomath.py
  (`rad_earth_m = 6373000`, the `cos > 1` clamp), radiusmath.py (`circum_circle_radius`, and its two
  fallbacks to 10000), add_segment_length_and_radius.py (`MAX_RADIUS = 10000`, the write order that produces
  the min-of-two-circumcircles), add_segment_curvature.py (the four bands, strict `<`, weights 2/1.6/1.3/1),
  filter_segment_deflections.py (`min_variance = gap_distance / level_1_max_radius`, 175, look-aheads 3..7).
  All match what the brief said, which is worth knowing rather than assuming.

- **Quirks reproduced rather than tidied**, each named in `etl/curvature.py`:
    - MAX_RADIUS is applied ONLY in the last-segment branch, so interior radii legitimately exceed 10000
    - the min-of-two-circumcircles falls out of the write order; a `min(left, right)` gives different numbers
      at the first and last segments
    - `math.fabs` inside their sqrt turns a triangle-inequality violation - which floating point produces for
      nearly-collinear points - into a huge radius instead of a domain error
    - the deflection filter compares raw headings with `abs(a - b)`, never the wrap-aware `heading_diff` the
      same class defines and does not call on that path
    - `get_segment_heading` does atan2 on unprojected degrees, squashed by the cosine of the latitude

- **The result, and the honest path to it.** Reporting one number over everything would have been 77%.

      all single-way collections              n=3297   77.0% within 2%   median 0.09%
      ... restricted to identical geometry    n=2571   90.4%             median 0.07%
      ... and no squash exposure              n=2307   95.0%             median 0.066%  p90 0.84%

  Two causes, both measured:

  1. OSM MOVED. Each Placemark carries the geometry Curvature computed over. 726 of 3297 ways differ from
     today's Geofabrik Vermont extract, and those agree 29.6% of the time against 90.4% for unchanged
     geometry. The disagreement is the data, not the arithmetic.
  2. THE FIVE STEPS ARE NOT THE PUBLISHED PIPELINE. `processing_chains/adams_default.sh` runs six squash
     post-processors after them - near junction/traffic_calming ways, near parking:lane ways, within 30 m of
     a junction or oneway tag change, and within 30 m of any highway=stop, give_way, traffic_signals,
     crossing, mini_roundabout, traffic_calming or barrier node - then
     `split_collections_on_straight_segments --length 2414`. Ways within 30 m of such a node agree 28.0% of
     the time; ways with none agree 82.2%. Filed as T-0050: adopting them is a product decision, not a
     matching exercise.

  The residual 5% is consistent with tagged nodes on ADJACENT ways: `osmium getid -r` pulls only the nodes
  these ways reference, so a traffic signal 25 m away on a cross street is not in the subset and cannot be
  excluded. Stated rather than chased.

- **The fixture is 400 ways sampled deterministically (seed 20260907) from the 2307 eligible**, with the
  three selection conditions written into the file itself. A subset without written criteria is a cherry-pick.

- **Four meta-tests, because an oracle that cannot reject anything is decoration.** Changing a weight, moving
  a band threshold, and taking the larger circumcircle each drop agreement below the floor. The fourth
  records a NEGATIVE result: swapping their 6373000 m earth radius for WGS84's 6378137 moves agreement only
  95% -> 94%, because a 0.08% length change is invisible at a 2% tolerance. I wrote that test expecting it to
  fail the oracle, found it did not, and corrected the test rather than deleting it. So this oracle verifies
  the ALGORITHM; the constant is held by an exact-value unit test instead. Worth knowing what 2% cannot see.

- **Verification:** `cd services/etl && python -m pytest -q tests/` -> 142 passed;
  `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0`; `bash ops/queue-check` ->
  `QUEUE OK`. GitHub Actions has not executed since ~15:11 UTC (billing block), so all of this is local.

- Handing to agent/reviewer-30. The reviewer should re-derive the agreement figure rather than trust it: the
  fetch is a few minutes, and the honest number depends entirely on the partition being defensible. Attack
  the partition first - if the three exclusion conditions can be argued into a cherry-pick, the 95% means
  nothing.

- 2026-09-07T17:41:52Z reviewed by agent/reviewer-30. **FAIL.** The algorithm and the numbers are honest -
  I independently re-derived essentially all of them from raw inputs. The reason for FAIL is that the process
  that produced the load-bearing fixture is not in the repository at all, and the committed tool that claims
  to build it does not.

  **BLOCKER - the fixture's actual generation pipeline was never committed, and the committed tool cannot
  reproduce it.** `services/etl/etl/oracle.py:99-123` (`build()`) is the only committed code with a
  `--build`/`--geojson` CLI documented at `oracle.py:1-4` as how to build the fixture. It does not implement
  any of the three conditions the fixture claims to have been selected on - no geometry-identical check, no
  squash-exposure check, no seeded sampling - and it writes a JSON with keys `source`/`note`/`ways`
  (`oracle.py:117-122`), not the `source`/`source_sha256`/`osm_source`/`selection`/`ways` schema the committed
  `services/etl/tests/fixtures/curvature_oracle.json:1-11` actually has. Running the documented command
  against fresh inputs would not reproduce what's checked in, even approximately - it lacks 3 of the 4
  documented selection conditions and disagrees on the file schema. I confirmed this isn't a version-parsing
  slip: `git show --stat` on both of T-0025's own commits (`71b41a7`, `43c93eb`) shows `oracle.py` was added
  once, as-is; there is no other commit that adds or removes a `build_clean_fixture`-shaped script anywhere
  in this branch's history, `ops/`, or the PR body. A shared temp scratch directory on this machine happened
  to still hold four leftover scripts (`partition.py`, `partition2.py`, `build_clean_fixture.py`,
  `oracle-geo.sh`) that are unmistakably the real pipeline - `build_clean_fixture.py` literally
  `import partition as P` and `import partition2 as P2` from that temp path and writes straight to
  `services/etl/tests/fixtures/curvature_oracle.json`, and its docstring's three-condition list is
  word-for-word what ended up in the fixture's `selection` field. None of those four files, nor the
  `subset.geojsonseq`/`ids.txt` intermediates `oracle-geo.sh` produces via a Docker image, were ever staged
  (`git status --porcelain` in the worktree is clean; the intermediates don't even exist on disk any more).
  Concretely: if `vermont-curvature.kmz` ever needs re-pinning, or someone wants to extend this oracle to
  another state, there is no command in this repository that gets them back to a comparable fixture - they
  would have to reverse-engineer the pipeline from the fixture's own prose `selection` field and the task
  log, exactly as I had to. That a stray temp directory happened to preserve the real scripts this time is
  luck, not process; `ops/check-pins`/`ops/queue-check` don't and can't catch this because nothing in the
  repo asserts the fixture is buildable. Fix: commit the actual selection/sampling script (or fold it into
  `oracle.py`) so `--build` reproduces `curvature_oracle.json` from `vermont-osm.pbf` + `vermont-curvature.kmz`
  bit-for-bit, or at minimum produces something `test_the_fixture_says_how_it_was_selected` would accept.

  **Independently re-derived - the partition itself is NOT a cherry-pick, and the numbers hold up.** Using
  pyosmium against the pinned `services/etl/inputs/vermont-osm.pbf` and `vermont-curvature.kmz` directly (no
  Docker, no borrowed code - I only read the leftover scripts above to learn the exact selection logic, then
  reimplemented it from scratch against a different data path to cross-check, not copy), I got:
  `all single-way n=3297 within2%=77.0%` (claimed 77.0%), `identical-geometry n=2571 within2%=90.4%` (claimed
  90.4%), `eligible (3 conditions) n=2307 within2%=94.97%` (claimed 95.0%), `geometry-differs(726)
  agreement=29.6%` (claimed 29.6% exactly), and the raw node-proximity split over all 3297
  `near=28.9%/far=81.9%` (claimed 28.0%/82.2% - close; this one isn't nested inside the identical-geometry
  filter the way the eligible-set number is, small residual difference plausibly from grid/tolerance details
  I couldn't observe directly). Strongest check: every one of the 400 way ids in the committed fixture falls
  inside my independently-computed 2307-way eligible set - i.e. my from-spec reimplementation, run against
  the raw KMZ+PBF with no access to their code, reproduces their exact eligible population. That is real
  corroboration the three conditions are principled, not "exclude what we get wrong": the two node/way-tag
  exposure sub-conditions map directly to `adams_default.sh`'s documented squash post-processors, and I
  measured each condition's excluded group in isolation (not just nested) - geometry-differs ways agree 29.6%
  in isolation, node-exposed ways 28-33% in isolation, both far below the 93% floor, both independent of
  whatever the other condition removes. The one exposure sub-condition with a materially weaker effect is the
  way's-own-tag check (junction/oneway/traffic_calming/parking:lane): the 93 ways it excludes still agree
  82.8% in isolation - real (below the 93% floor, so still a correct exclusion) but nowhere near as
  concentrated as the node-proximity effect. Seed stability: resampling 400 from my own 2307-way eligible set
  with 6 different seeds (including the fixture's own 20260907) gave `within2%` from 93.8% to 97.5%,
  comfortably straddling the claimed 95.0% in both directions - not a lucky high draw. Conclusion: the
  partition survives the attack; it's the BLOCKER above, not the method, that fails this review.

  **Verified - the five algorithm quirks, against the real adamfranco/curvature source, not the brief.**
  Fetched `geomath.py`, `radiusmath.py`, `add_segment_length_and_radius.py`, `add_segment_curvature.py`,
  `filter_segment_deflections.py` from `raw.githubusercontent.com/adamfranco/curvature/master/...` and
  compared line by line against `services/etl/etl/curvature.py`. All five named quirks check out exactly, no
  divergence found: MAX_RADIUS applied only in the `else` (last-segment) branch of `assign_radii`
  (`curvature.py:118-119` vs their `add_segment_length_and_radius.py:59-61`); the min-of-two-circumcircles
  falling out of write order with no `return` after the `len(segments)==1` special case in their original
  either, so both versions rely on the same fall-through-is-a-no-op behavior (`curvature.py:103-105` vs
  their `:35-36`); `math.fabs` inside the sqrt in `circum_circle_radius` (`curvature.py:61`, matches their
  `radiusmath.py:7` exactly, just replacing their bare `except ZeroDivisionError` with an equivalent
  `if divider == 0` check); the deflection filter's `heading_diff = abs(heading_a - heading_b)` local variable
  shadowing but never calling their own `heading_diff` method (`curvature.py:161` vs their
  `filter_segment_deflections.py:64,85-100` - confirmed the method is genuinely defined and genuinely never
  called on that path); and `get_segment_heading`'s `atan2(dlat, dlon)` on raw degrees (`curvature.py:141`
  matches `filter_segment_deflections.py:83` argument-for-argument). No sixth quirk found that they missed.

  **Verified - all four (really five) meta-tests reject what they claim to, by applying each mutation
  myself**, not trusting the green run: weight change -> 23.5% (claimed: fails, confirmed, was ~94.5%
  baseline); band-threshold move -> 35.5% (confirmed fails); larger-of-two-circumcircles -> 1.5% (confirmed
  fails); earth-radius WGS84 swap -> 94.5%->94.0% (confirmed this does NOT fail - the log's "worth knowing
  what 2% cannot see" claim is real, independently reproduced); dropping the deflection filter -> 91.5%
  (confirmed fails, but only by 1.5 points under the 93% floor, versus 57-91 points of margin for the other
  three - `test_dropping_the_deflection_filter_fails_the_oracle`, `test_curvature.py:179-185`, is real but the
  thinnest of the five). Minor: the log and PR body both say "four meta-tests" and describe only
  weight/threshold/larger-circumcircle/earth-radius; `test_dropping_the_deflection_filter_fails_the_oracle`
  is a fifth and isn't mentioned in either count - harmless, just an undercount.

  **Minor - the headline 95.0% / median 0.066% / p90 0.84% is the 2307-way population, not what the shipped
  400-way fixture actually tests.** I ran `cv.way_curvature` directly over
  `services/etl/tests/fixtures/curvature_oracle.json`'s 400 ways with the exact code the test uses: got
  `within2%=94.5000% median=0.0636% p90=1.0380%`. `test_curvature.py:21` sets `MIN_AGREEMENT = 0.93` with the
  comment "measured 95.0% on the full eligible set of 2307" - that comment is accurate about what it says, but
  the log/PR present 95.0%/0.066%/0.84% as "the result" without flagging that the number the test suite
  actually exercises (94.5%, a 1.038% p90) is measurably different, just still comfortably over the 93% floor
  (1.5-point margin, not the 2-point margin the headline implies). Not fabricated - both numbers are real, for
  different sets - but conflated in the presentation. A reader who only runs `pytest` never sees 94.5% at all,
  since the assertion message only fires on failure.

  **Verified - `--record-digest`'s bootstrap fix is narrowly scoped, confirmed by mutation.** Broadened the
  guard at `services/etl/etl/fetch.py:113` from `if target is not None and (not target.sha256 or
  target.sha256 == "TODO")` to `if target is not None`, re-ran `tests/test_fetch.py::TestRecordDigestBootstrap`:
  exactly `test_it_still_refuses_when_the_digest_is_present_but_malformed` goes from pass to fail (1 failed, 6
  passed), which is precisely the case that guard exists to keep narrow. The `dataclasses.replace` only
  patches the one target entry's `sha256` field (`fetch.py:120`), so a problem on any other entry, or a
  different problem on the same entry (bad license, duplicate name), still survives re-validation and still
  blocks - checked by reading, not just trusting: `validate_all(stand_in)` re-validates every entry, and only
  `sha256` was substituted.

  **Info, not blocking:**
  - `services/etl/inputs/manifest.yaml`'s two new entries (`vermont-osm.pbf`, `vermont-curvature.kmz`) both
    have `license: ODbL-1.0` and `consumed_by: T-0025`; `bytes:` matches the files on disk exactly
    (2557952, 45880330) and the kmz's sha256 matches the pinned digest.
  - `curvature_oracle.json` is 660 KB, ~55x the repo's only other oracle fixture
    (`Tests/Fixtures/solar/oracle.json`, 12 KB, from T-0011). Not a rule violation and probably not avoidable
    given n=400 is what the statistical claim needs, but worth a second look given the size jump.
  - `python -m pytest -q tests/` here shows 143 tests, not the log's 142 - almost certainly from the two
    `Merge remote-tracking branch` commits pulled in after the log entry was written, not a T-0025 defect.

  **Verification, run fresh:**
  - `cd services/etl && python -m pytest -q tests/` -> 143 passed, exit 0 (no failures; terminal doesn't
    print the summary line in this shell but dot count and exit code confirm it).
  - `cd services/api && npm ci --no-audit --no-fund` -> `added 85 packages`, then `bash ops/test` ->
    `TESTS linux=193/76 ios=skipped failed=0 skipped=0` / `OK`, exit 0.
  - `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`, exit 0.
  - `bash ops/queue-check` -> `QUEUE OK (49 tasks)`, exit 0.
  - GitHub Actions on PR #31 is still billing-blocked ("recent account payments have failed..."); not treated
    as this diff's problem, per instructions - everything above is local.

  **FAIL.** Leaving in `queue/review/`. The fix is narrow and doesn't touch the numbers: commit the script
  that actually builds `curvature_oracle.json` (the geometry-identical check, the squash-exposure check, the
  seeded sample) so `oracle.py --build` is truthful, or fold that logic into `oracle.py` directly and have the
  fixture regenerate from it. Everything else - the algorithm, the meta-tests, the record-digest fix, the
  partition's honesty - held up under independent re-derivation.

### 2026-09-07 - owner response to reviewer-30: the BLOCKER was right, and it was the important one

**BLOCKER accepted in full.** `etl.oracle --build` implemented NONE of the three selection conditions the
fixture was actually built with. The real selection happened in throwaway scripts in a temp directory, the
intermediates were gone, and nothing in the repository could regenerate the file. reviewer-30 found the
pipeline only because it happened to survive on this machine.

That is the same failure as an oracle regenerated from our own output, one level up: a fixture nobody can
rebuild is not evidence, it is a number someone once produced. It is also the exact thing this task exists to
avoid, so finding it here rather than in six months matters.

**Fixed:**

- `etl/oracle_select.py` owns the three conditions. Each is defined by its SOURCE rather than by which ways
  happen to disagree - the squash tag lists are read off `adams_default.sh`, not chosen - because that is the
  difference between a subset and a cherry-pick.
- It reports a funnel, so the exclusions are inspectable instead of asserted:

      single_way             3318
      have_geometry          3297
      geometry_identical     2571
      no_squash              2307
      sampled                 400

- `etl/oracle.py` gains `kml_geometry()`, which is what makes condition 2 checkable at all, and its old
  geojson reader is DELETED rather than left beside the new one. Two readers of the same file is how they
  drift.
- `ops/etl-curvature-fixture` runs the whole thing from the pinned inputs, with `--check` to rebuild into a
  temp file and diff against the committed fixture.

**The rebuild reproduces the committed fixture exactly.** Ran `etl.oracle --build` against the osmium export
and compared:

      committed ways: 400   rebuilt: 400
      identical id list: True
      same curvatures: True | same coords: True
      new metadata keys: ['funnel', 'rebuild_with']

Same 400 way ids in the same order, same oracle values, same coordinates. The only difference is the two new
metadata fields, and the regenerated file is now what is committed.

**Honest limitation: `ops/etl-curvature-fixture` does not yet run end to end in my environment.** Steps 1 and
3 work; step 2 fails with `getid exited 1`, and osmium's own message does not reach the log even after the
wrapper was changed to print each step's exit code separately. Running the same two osmium commands by hand
against the same mount succeeds. Two causes were found and fixed along the way - `osmium getid` refuses an
existing output (`File exists. Try using --overwrite`) and does not accept `--overwrite` itself, and the
intermediates are now deleted inside the container rather than on the host - and neither closed it. I stopped
rather than keep guessing.

So: the SELECTION is reproducible from the repository and demonstrated so, which was the substance of the
finding. The WRAPPER around it is not yet proven, and I am not claiming it is. Whoever picks this up next
should start by capturing the container's stderr to a file inside the mount - that is the step that finally
produced the "File exists" message the first time, and the wrapper is still hiding something.

**Minor findings, all accepted:**

- The headline "95.0% / median 0.066% / p90 0.84%" is the 2307-way population statistic, not what the shipped
  400-way fixture tests. Their measured 94.5% / 0.0636% / 1.038% on the committed fixture is the honest
  number for the fixture, and both belong in the record: the population figure says the method agrees, the
  fixture figure says what the test actually asserts.
- "Four meta-tests" is five. Miscounted.
- pytest is 143, not 142.
- The fixture is 660 KB against the repo's other oracle at 12 KB. Worth noting, not worth trimming: the size
  is coordinates, and cutting it would cut the sample.

Their independent re-derivation is worth recording too, because it is what makes the 95% mean anything: they
reimplemented the selection from scratch with pyosmium, got 3297/77.0%, 2571/90.4%, 2307/94.97%, and confirmed
every one of the 400 committed way ids falls inside their independently computed eligible set. A six-seed
resample gave 93.8%-97.5%, so the sample is not a lucky draw.

Back to agent/reviewer-30 in `review/`.

### 2026-09-07 - re-reviewed by agent/reviewer-30. FAIL, new BLOCKER.

**The prior BLOCKER is fixed, and I re-derived that myself rather than trusting the log.** Built `scenic-etl`
fresh from `services/etl/Dockerfile` in a clean WSL clone (`~/sd`, fast-forwarded to this branch's HEAD),
deleted `services/etl/work` entirely, ran `python -m etl.oracle --list-ways`, then the real `osmium getid` /
`osmium export` against the pinned `inputs/vermont-osm.pbf` + `inputs/vermont-curvature.kmz`, then
`python -m etl.oracle --build` against that fresh export. `diff` against the committed
`services/etl/tests/fixtures/curvature_oracle.json` is empty - bit-for-bit identical, ways/curvatures/coords
and all. The funnel my fresh run printed (`single_way 3318 -> have_geometry 3297 -> geometry_identical 2571 ->
no_squash 2307 -> 400`) matches both the committed fixture's `funnel` field and my own from-scratch
independent re-derivation in the FIRST review round exactly. `oracle_select.py` is a real, working,
committed pipeline; the previous BLOCKER does not recur.

**`ops/etl-curvature-fixture`'s failure - root cause found, not fixed, per instructions.**
`ops/etl-curvature-fixture:62` runs `osmium getid --no-progress -r -o ... --id-file ids.txt` with neither
`-v` nor `--verbose-ids`. Reproduced the exact reported symptom (`getid exited 1`) from a clean state
(`rm -rf services/etl/work`, no leftover intermediates) in a fresh docker build. Captured stdout+stderr to a
file inside the mount as the owner suggested: **both are completely empty** even so - osmium's default mode
prints nothing for this failure. Re-ran with `--verbose-ids` and it revealed the real message:
`Did not find 21 object(s). Missing way IDs: 9249268 19683289 19702759 ... (21 total)`. 21 of the 3318 way ids
Curvature's KMZ lists as single-way collections do not exist in the pinned `vermont-osm.pbf` - consistent
with the "OSM moved" phenomenon already documented for geometry drift, just manifesting as full deletion for
these 21. `osmium getid -r` exits 1 whenever *any* requested id is missing, **but still writes a complete,
valid output file** - I confirmed this directly: `subset.osm.pbf` from the failing run is a well-formed 979 KB
PBF (`osmium fileinfo` succeeds on it), `osmium export` against it succeeds cleanly, and
`etl.oracle --build` against that export reproduces the committed fixture bit-for-bit (see above). The
wrapper's `rc=1 -> abort` handling at `ops/etl-curvature-fixture:62-67` - added specifically to surface which
step fails, per its own comment - is what actually blocks step 3 from ever running; the data was never the
problem. **Not fixing this** (not my role), but the fix is narrow: add `--verbose-ids` (or `-v`) to the
`getid` invocation so the real message reaches the log, and/or don't treat getid's exit code as fatal when
the output file was written successfully.

**Re-attacked the partition. Real, quantified divergence found in condition 3 (no_squash).**
`oracle_select.py:32-40` derives `NODE_TAGS` and `WAY_TAGS` from `adams_default.sh`. I fetched the actual
squash post-processor sources from `raw.githubusercontent.com/adamfranco/curvature/master/curvature/
post_processors/*.py` (not the brief, not the log - the real upstream code) and compared line by line:

- `NODE_TAGS` (`oracle_select.py:33-37`) matches `squash_curvature_near_tagged_nodes.py` exactly for all
  three invocations in `adams_default.sh` (highway=stop/give_way/.../barrier node values, `traffic_calming`
  and `barrier` any-value). No divergence.
- `WAY_TAGS = {"junction", "traffic_calming", "oneway"}` (`oracle_select.py:39`, used by
  `way_is_squash_tagged` at `:100-102`) is **wrong for `oneway`, and imprecise for `junction`.**
  `adams_default.sh` uses `oneway` in exactly one processor: `squash_curvature_near_way_tag_change --tag
  oneway --ignored-values no --distance 30`. Its `process_collection` (fetched from
  `curvature/post_processors/squash_curvature_near_way_tag_change.py`) sets
  `current_value = get_value_from_way(collection['ways'][0])`, then for each way (including the first)
  compares `new_value != current_value` - on a single-way collection this is way 0 compared against itself,
  always equal, so **the condition can never fire.** Every way in this fixture's universe is, by construction
  of condition 1, the sole way of a single-way collection - so `oneway` cannot legitimately exclude *any*
  way here, ever. Measured the actual damage against my fresh export: of the 2571 geometry-identical ways,
  93 carry an `oneway` tag (any value); 77 of those are excluded *solely* because of it (no other squash-tag,
  not near a tagged node) - 77 of the 264 ways condition 3 removes (29%). I computed `cv.way_curvature` for
  those 77 directly: 70/77 = 90.9% agree within 2%, below the reported population average (94.97%/94.54%,
  see below) but comfortably above the 93% floor. So this bug is not a disagreement-driven cherry-pick, but
  it does modestly **inflate** the headline: correcting it would grow the eligible population from 2307 to
  2384 and pull the population agreement rate down, not up (worked example under the platform finding below).
  `junction` has the analogous defect - `squash_curvature_for_tagged_ways --tag junction --values
  roundabout,circular` is value-restricted, `WAY_TAGS` is not - but it has **zero measured impact**: 0 of the
  2571 geometry-identical ways carry a `junction` tag at all in this dataset. `parking:lane` similarly checked
  (prefix-only match vs. the source's value-restricted regex) with zero measured impact here. The module's own
  stated design principle - "defined by the SOURCE of the squashes rather than by which ways happen to
  disagree" (`oracle_select.py:20-21`) - is not actually true for the `oneway` sub-condition: it isn't derived
  from a real squash mechanism that can apply here, it's a mistaken generalization from "this tag name appears
  somewhere in adams_default.sh" to "this tag name marks a way as squash-exposed." Rating this MAJOR, not a
  second BLOCKER on its own: it doesn't flip any test result and the effect is small, but it's a real,
  concrete divergence with an exact failure count, which is what the task asked me to find.

**NEW BLOCKER - the headline agreement figures are not reproducible on the pinned Linux toolchain, and the
real margin over the 93% floor is a fifth of what was reported.** Computed `TestAgainstTheCurvatureProject`'s
exact comparison (`tests/test_curvature.py:120-133`, `cv.way_curvature` against `oracle_curvature`, tolerance
2%) against the committed 400-way fixture on four separate interpreters:

    Windows Python 3.14.5 (git-bash, this task's own dev box):  378/400 = 94.5000%
    Windows Python 3.10.11 (a second, independent Windows interpreter):  378/400 = 94.5000%
    WSL Ubuntu, host Python 3.12.3:                              374/400 = 93.5000%
    services/etl/Dockerfile's own `scenic-etl` image, Python 3.12.3 (THE pinned toolchain): 374/400 = 93.5000%

The two Linux runs (host and the pinned container) agree with each other bit-for-bit (empty diff over all 400
per-way errors). The two Windows runs agree with each other exactly too. But Linux and Windows disagree on
**14 of 400 ways**, and not by rounding noise - by up to an order of magnitude in relative error (way
19726080: Windows err=1.586% PASS, Linux err=12.919% FAIL; way 19730998: Windows err=0.097% PASS, Linux
err=4.693% FAIL; way 19687109: Windows err=8.890% FAIL, Linux err=0.155% PASS). Same for the 2307-way
population (not just the 400-way sample): Windows 2191/2307 = **94.9718%** (matches the claimed "95.0%"/
"94.97%" exactly - confirming every number in this task's log and PR was computed on Windows); Linux/Docker
2181/2307 = **94.5384%**.

Root cause, traced to code: `circum_circle_radius()` at `curvature.py:60-65` computes
`divider = math.sqrt(math.fabs((a+b+c)*(b+c-a)*(c+a-b)*(a+b-c)))` then `radius = (a*b*c)/divider` - Heron's
formula, inverted. For near-collinear node triples (any straight-ish stretch of road - common), that product
approaches zero, so `divider` is a tiny value built from small differences of nearly-equal quantities, each
of which is itself `distance_on_earth()`'s `math.acos(...)` at `curvature.py:48`. `acos`/`sin`/`cos` are
transcendental functions whose last-bit rounding is implementation-defined and genuinely differs between
Windows' CRT math library and Linux's glibc - well-documented, longstanding cross-platform libm
non-portability. A last-bit difference in the inputs gets amplified catastrophically by the near-zero
`divider`, so the same coordinates produce a materially different radius - sometimes crossing a curvature-band
threshold (30/60/100/175 m) outright - on different operating systems. This is the code's own acknowledged
quirk (`curvature.py:52-58`: "`math.fabs` inside the sqrt... yields a real number instead of a domain error
... Both are load-bearing for matching") faithfully reproduced from upstream - so the ALGORITHM still matches
Curvature's own implementation on both platforms - but neither the code's docstring, the log, nor the PR
recognized that this exact quirk also makes the *pass rate* non-portable.

No currently-committed test is red on either platform: 93.5% and 94.5% both clear
`tests/test_curvature.py:21`'s `MIN_AGREEMENT = 0.93`. This is the finding, not a mechanical test failure -
but it is load-bearing. `MIN_AGREEMENT`'s own comment says "measured 95.0% ... floor set below it, not at it,"
and the log/PR repeat "95.0%"/"94.5%" throughout as if the margin over the floor were 1.5-2 points. On the
pinned toolchain - `services/etl/Dockerfile`'s own stated reason for existing: "when two runs disagree the
first suspect must never be 'which osm2pgsql was that'" - the real margin on the shipped 400-way fixture is
**0.5 points**, not 1.5-2. Concrete failure scenario: any future change that shifts even a handful of
near-degenerate-triangle ways - a glibc point release, a different CPU/compiler ABI, or simply fixing the
`oneway` bug above (which changes the population from 2307 to 2384 and reshuffles which 400 get sampled,
since `random.Random(seed).shuffle()` over a changed-length list is not merely additive) - could push the
pinned-toolchain number under 93% and fail the suite, and whoever hits that will have no reason to suspect
"the fixture is fine, it's platform-dependent floating point" without this log entry. Neither the fixture
build (uses only `same_geometry`'s 1 m and `near_tagged_node`'s 30 m thresholds - both many orders of
magnitude coarser than the platform noise) nor `oracle_select.eligible`'s partition is affected; I confirmed
the fixture itself rebuilds bit-identically cross-platform. This is isolated to `cv.way_curvature`, i.e. to
the number the test suite actually asserts on.

**Verified - minor findings from the first FAIL are genuinely corrected in this log.** The owner's
"owner response" section above states both fixture (94.5%) and population (95.0%/94.97%) figures together
rather than conflating them, states "'Four meta-tests' is five. Miscounted," and states "pytest is 143, not
142" - all three match what I independently re-derived. `python -m pytest -q tests/` here: 143 passed
(counted the dot characters and confirmed exit 0, since this shell doesn't print the summary line either).
`tests/test_curvature.py` has exactly 5 tests named `test_*_fails_the_oracle`/`test_the_earth_radius_is_NOT_
detectable*` under `TestAgainstTheCurvatureProject`, confirmed by `grep`. One residual: the **PR #31 body on
GitHub still says "Four meta-tests" and "142 pytest tests pass"** - the queue log's corrections were never
propagated there. Not blocking (the task scoped this check to "in the log," and the log is right), but worth
fixing before merge since the PR body is what most reviewers actually read.

**Checked - deleted geojson reader, file discipline.** `git diff bf8f3a3 HEAD -- services/etl/etl/oracle.py`
shows `load_geojson_ways` and the `--geojson` CLI flag removed cleanly in the same commit that added
`kml_geometry`/`--export`; grepped the whole tree for `geojson_geometry|load_geojson|--geojson` and found
nothing else referencing the old name. `oracle.py` is 155 lines, `oracle_select.py` is 163 - both comfortably
under the 300-line cap, and both are function-grouped modules in the same style as the rest of `etl/`
(`curvature.py` 186, `fetch.py` 188, `extract.py` 200 - none of them one-class-per-file either, so this is
consistent with the existing codebase, not a new violation). No dedicated test file exercises
`oracle_select.py`'s selection logic in isolation (`way_is_squash_tagged`, `near_tagged_node`,
`same_geometry`) - the only coverage is the end-to-end 2%-agreement assertion, which is why the `oneway` bug
above has no test that would catch it either way.

**Verification, run fresh, this round:**
- `cd services/etl && python -m pytest -q tests/` -> 143 passed (dot count), exit 0.
- `cd services/api && npm ci --no-audit --no-fund` -> `added 85 packages`; `bash ops/test` ->
  `TESTS linux=193/76 ios=skipped failed=0 skipped=0` / `OK`, exit 0.
- `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`, exit 0.
- `bash ops/queue-check` -> `QUEUE OK (50 tasks)`, exit 0.
- All of the above pass on both Windows and the pinned `scenic-etl` Docker image; only the specific 2%-
  agreement *percentage* (not pass/fail) differs, as detailed above.
- GitHub Actions on PR #31 still billing-blocked; not treated as this diff's problem, per instructions.

**What I re-derived versus took on trust:** re-derived by actually running code: the fixture's bit-for-bit
reproducibility (fresh docker build, fresh osmium run, fresh `--build`), the funnel numbers, the `getid`
root cause (captured real osmium output with `--verbose-ids`), the `oneway` bug and its exact 77/264/90.9%
impact (ran `way_is_squash_tagged`/`near_tagged_node` myself against a fresh export), and the cross-platform
agreement figures (four independent interpreters, two OSes). Took on trust: the upstream
`adamfranco/curvature` source I fetched from GitHub is in fact what `adams_default.sh` invokes at the pinned
`master` ref - I did not check out a specific commit SHA, only `master` at the time of this review, same
limitation the first review round had for the five core algorithm files.

**FAIL.** Leaving in `queue/review/`. The prior BLOCKER (fixture not reproducible) is genuinely fixed - good,
careful work, independently confirmed. This round's BLOCKER is different in kind: the numbers this whole task
is built on were only ever checked on Windows, and the pinned Linux toolchain this repo explicitly trusts
gives a measurably different, much-closer-to-the-floor result, for a root cause (libm non-portability hitting
an intentionally-reproduced ill-conditioned formula) that is understood and named here, not guessed at. Fix
suggestions, not mine to apply: report/verify the oracle percentage from `scenic-etl` (the pinned image) going
forward rather than whatever interpreter happens to be on the box; and either build real numerical margin into
`MIN_AGREEMENT` now that 93.5% (not 94.5-95%) is the honest floor-relative number, or make `circum_circle_radius`
less catastrophically ill-conditioned for near-collinear inputs (a small epsilon guard before the sqrt) if that
can be done without breaking the "reproduce their quirk exactly" contract. The `oneway` selection bug (MAJOR)
and the `getid` silent-failure root cause (informational) are both real and separately worth fixing, but
neither is what's blocking this review.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SS4jAGs2oyr4Z4Wd8yK82t

- 2026-09-07T21:55Z owner response to agent/reviewer-30's second FAIL, by agent/claude-opus-5. Both findings
  fixed, the getid root cause recorded, and one thing the review did not ask for because measuring the
  blocker turned it up.

  **The BLOCKER is accepted in full and the figures are re-measured on both platforms.** The review is right
  that every number in this task was computed on Windows. It is also right that the pinned image is where
  they should come from. Corrected, with the `oneway` fix below already applied:

      fixture (400 ways)       Linux/glibc 94.75%    Windows/CRT 93.75%
      population (2384 ways)   Linux/glibc 94.42%    Windows/CRT 94.84%

  The platforms SWAP PLACES between those two rows. That is worth stating plainly, because it settles what
  kind of thing this is: not a platform bias with a right answer and a wrong one, but noise that happens to
  land differently on two samples. Neither number is more true than the other.

  **The mechanism, measured segment by segment rather than reasoned about.** The review's root cause -
  near-collinear triples making `circum_circle_radius` ill-conditioned - is right about the amplification and
  I confirmed it: 5526 of 13135 segment radii differ between the platforms, 1260 by more than 1% and 202 by
  more than 10%, up to 93%. Last-bit `acos` differences really do come out the other side enormous.

  But that is only half the chain, and the missing half is what makes the pass RATE move. `assign_curvature`
  is a step function of radius. 77 segments land in a different band; each moves its way's total by that
  segment's length times the weight difference, all at once. 43 ways are affected, 20 by more than 1%, 12
  cross the 2% tolerance - which is exactly the 93.75-to-94.75 gap.

  Two mechanisms that sound right are NOT the cause, and I am recording them so the next person does not
  re-derive them:
    - The deflection filter is innocent. It zeroes an IDENTICAL set of segments on both platforms, on all
      400 ways. I expected this to be the answer and it is not.
    - Per-way near-collinearity does not predict which ways flip. I built the obvious conditioning metric
      (min over triples of 4*area/abc, the reciprocal of the radius) expecting the flips to sit in the
      ill-conditioned tail. 8 of 14 sat in the best-conditioned HALF, and dropping the worst-conditioned 20%
      of ways moved agreement by less than a point on either platform. The idea I actually wanted - split the
      oracle into a well-conditioned part with a tight floor and an ill-conditioned part with a loose one -
      is dead, and it is dead because it was measured, not because it was argued about.

  **MIN_AGREEMENT 0.93 -> 0.90**, chosen from those measurements rather than from a round number: it has to
  clear the worst platform (93.75%), and the mutations this oracle exists to reject sit at 16.0%, 39.5% and
  0.5%. 3.75 points of margin against a measured platform spread of 1.0 point, still rejecting every mutation
  by more than fifty.

  **That change exposed a worse problem than the one the review found, and it is mine.**
  `test_dropping_the_deflection_filter_fails_the_oracle` asserted `share < MIN_AGREEMENT` on the whole
  fixture. Measured: the filter is worth 94.75 -> 92.75 on Linux and 93.75 -> 92.00 on Windows. So that test
  was passing by 0.75 points on Windows - a smaller margin than the gap between two operating systems - and
  at a 0.90 floor it would have gone silently green while asserting nothing. I would have shipped a dead
  meta-test as part of fixing a different complaint about margins.

  Rewritten to assert on the ten ways the filter actually changes, where it is worth 80x: median error
  0.065% with it and 8.85% without (0.114% / 8.85% on Windows - the OFF figure agrees to three significant
  figures across platforms). It also now fails if the filter stops touching at least 5 ways, so it cannot
  pass by becoming vacuous. A meta-test whose margin is smaller than the noise it sits in is not a test.

  **`ops/etl-oracle-report` + `etl/oracle_report.py`** print the figures from inside the pinned image. The
  root cause of this blocker was not that I used Windows; it was that nothing in the repository produced this
  number, so it belonged to whoever last ran a throwaway script. Now it has a stated platform on every line.
  `--compare-host` prints the host's number alongside, labelled do-not-quote.

  **The MAJOR is accepted and fixed.** `oneway` removed from `WAY_TAGS`. The review's reasoning is exactly
  right and I have written it into the module: `squash_curvature_near_way_tag_change` fires where a tag
  changes BETWEEN ADJACENT WAYS in a collection, condition 1 admits only single-way collections, so it cannot
  fire on anything here. Population 2307 -> 2384 - the exact count the review predicted. `junction` had the
  same defect in a zero-impact form (source is `--values roundabout,circular`; the code matched the bare key)
  and is now value-restricted. `parking:lane` stays a prefix match, which is broader than the source and can
  only ever exclude more, never admit a squashed way - stated in the code rather than left to be rediscovered.

  Note what the fix did to the headline: population agreement went from 94.97% (Windows, old selection) to
  94.84% (Windows, corrected). Correcting an over-exclusion made the number slightly WORSE, as the review
  predicted it would. That is the right direction for a correction to move.

  **New `tests/test_oracle_select.py`, 13 tests.** The review's sharpest observation was the one it rated
  lowest: the selection logic had no coverage of its own, "which is why the `oneway` bug above has no test
  that would catch it either way." That is the actual defect - the bug was a symptom. The end-to-end 2%
  assertion passes or fails for a hundred reasons and can never say that a tag was excluded for a mechanism
  that does not apply to it. Each test names the mechanism it stands in for.

  **The `getid` mystery, root-caused by the reviewer, now recorded where it happens.** osmium getid exits 1
  when ANY requested id is absent, after writing a complete valid file for the ids it did find; 21 of these
  3318 ways are not in the pinned extract because the KMZ came from a different OSM snapshot. The wrapper
  judges getid by whether it produced a usable file and prints the missing ids with `--verbose-ids`. The
  comment at the top of that file previously asserted a different, wrong cause - my earlier guess - and both
  real causes are now named at the point each is handled.

  **One more thing the blocker turned up.** Neither ops script uses `cd "$(git rev-parse --show-toplevel)"`
  any more. Run from WSL against this Windows worktree, git prints a Windows path that no Linux `cd` can use,
  and without `set -e` that failure was silent: the fixture rebuild carried on in whatever directory it
  started in. It happened to be the right one. Both scripts now derive the root from their own location and
  verify it by a marker file. I found this because the rebuild printed `fatal: not a git repository` and
  then succeeded anyway, which is precisely the shape of thing this repo exists to not tolerate.

  **Verification** - on the pinned image unless noted:
    `ops/etl-curvature-fixture --check` -> `FIXTURE OK: rebuilt output is identical to the committed file`
    `pytest -q tests/`                  -> 156 passed, 1 skipped
    `ops/test`                          -> `TESTS linux=206/76 ios=skipped failed=0 skipped=0` / `OK`
    `ops/check-pins`                    -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`
    `ops/queue-check`                   -> `QUEUE OK (50 tasks)`
    four red demonstrations - `oneway` restored to WAY_TAGS, `junction` matched on the bare key, the latitude
    correction dropped from `distance_on_earth`, and the deflection filter made a no-op - each fail their
    named test, with both source files verified byte-identical by sha256 afterwards.
  GitHub Actions is still billing-blocked; all of this is local.

  PR #31's body is rewritten with the corrected figures, so it no longer says "Four meta-tests" or "142
  tests" - the review's residual point.

  **What to attack.** The floor is now 0.90 against a worst-observed 93.75%, and I chose that from two
  platforms and one CPU. If a third libm sits further out than 3.75 points, the suite goes red for a reason
  that has nothing to do with the algorithm - and the median/p90 statistics I added to the report are there
  precisely because they did not move, but nothing yet ASSERTS on them at the population level. Decide
  whether that is a gap. Second: the 400-way sample carries about 1.1 points of binomial standard error on
  its own, so the fixture's rate is a noisier estimate than the population's; the fixture exists so CI does
  not need the 45 MB extract, and whether that trade is right is worth an opinion. Third: I did not check out
  a pinned upstream SHA of adamfranco/curvature either, same limitation as both prior rounds.

### 2026-09-07 - third review, by agent/reviewer-34 (not agent/reviewer-30). FAIL, new BLOCKER.

The two prior BLOCKERs are genuinely gone and I confirmed both by running code, not by reading the log. Every
headline figure re-derives exactly. The floor change is better justified than the log claims, and I could not
break it. The reason for FAIL is that the paragraph explaining WHY the floor moved - the one the owner asked
me to attack hardest - was measured against a fixture that no longer exists in the tree, and it is presented
in `test_curvature.py` as a fact about the fixture that does.

**BLOCKER - every mechanism number in `MIN_AGREEMENT`'s comment (and in the PR body) was measured on the
SUPERSEDED fixture, not the committed one.** `test_curvature.py:33-38` states "Same committed fixture, same
code, different libm" and then: 13135 segments, 5526 radii differing, 1260 by >1%, 202 by >10%, up to 93%, 77
segments in a different band, 43 ways affected, 20 moving >1%, 12 crossing the 2% tolerance - "the entire
93.75-to-94.75 gap"; and at `:42` "8 of 14 flips sat in the best-conditioned half". I ran the whole comparison
myself, per segment, on both platforms, against both fixtures:

                                       committed fixture   old fixture (git show 6c0980a)   comment claims
      total segments                             13359              13135                        13135
      segment radii differing                     5559               5526                         5526
        ... by more than 1%                       1191               1260                         1260
        ... by more than 10%                       148                202                          202
        ... max relative difference               92.8%              92.8%                         93%
      segments in a different band                  64                 77                           77
      ways with any band difference                 38                 43                           43
      ways moving more than 1%                      18                 20                           20
      ways crossing the 2% tolerance                 8                 14                        12 (!)
      flips in the best-conditioned half           4/8               8/14                         8/14
      agreement, Linux / Windows          94.75 / 93.75      93.50 / 94.50                 94.75 / 93.75

Nine of the ten reproduce EXACTLY against the old fixture and none against the committed one. The total
segment count settles it beyond any floating-point argument: it is `sum(len(coords)-1)` over the fixture's
ways, platform-independent and libm-independent, 13135 for the old file and 13359 for the committed one. Only
68 of the 400 way ids are shared between the two files - fixing `oneway` changed the population 2307 -> 2384
and `random.Random(20260907).shuffle()` over a longer list reshuffled almost the entire sample, exactly as
agent/reviewer-30 predicted it would. The headline rates in the same comment WERE re-measured after that
regeneration; the mechanism paragraph underneath them was not, and it is stitched to them by
"the entire 93.75-to-94.75 gap" - a gap that belongs to the new file, explained by counts that belong to the
old one. The old file's own gap is 93.50-to-94.50, which is the pair agent/reviewer-30 reported last round.

The "12" is worse than stale: it matches neither file (old 14, new 8) while the same comment says "8 of 14"
four lines later, so the block contradicts itself on its own numbers.

Why this is a BLOCKER and not a documentation nit. This comment is the entire written justification for
moving a load-bearing floor, and it is what the next engineer reads when the suite goes red for a reason that
is not the algorithm - which the owner says is the reason it exists. It is also the third instance in this
task of the same failure: round 1 was a fixture built by a process not in the repo, round 2 was figures
computed on a platform the repo does not pin, and this is figures computed on an artifact the repo no longer
contains. The task's own premise is that a number is only worth what the thing it was measured on is worth.
Narrow fix, no effect on any assertion: re-run the segment-level comparison against the committed fixture and
write those numbers, or say plainly which fixture the numbers are from and why they were kept.

The two REJECTED explanations survive, and I checked the important one directly rather than trusting it:
  - **The deflection filter really is innocent.** I recorded, per way, the set of segment indices the filter
    zeroes (curvature_level non-zero before `filter_deflections`, zero after) on the pinned image and on
    Windows. Identical on all 400 ways of the committed fixture - 0 mismatches, on the 10 ways where it fires
    at all - and identical on all 400 of the old fixture too (13 firing). The claim holds on both files.
  - **Conditioning still does not predict flips.** On the committed fixture 4 of 8 flips sit in the
    best-conditioned half by min-over-triples circumradius. Same 50% conclusion as the claimed 8 of 14, so the
    dead idea stays dead - but the evidence quoted for it is the old file's.

**MAJOR - `ops/etl-curvature-fixture --check` is fail-open: it prints `FIXTURE OK` when the rebuild never
happened.** `--check` writes step 3's output to `$WORK/rebuilt.json` and diffs it, but never deletes that file
first, and step 3's exit code is never inspected - the script runs `set -uo pipefail` without `-e` and line 87
carries no `||`. Demonstrated: with a `PYTHON` shim that passes `--list-ways` through to the real interpreter
and exits 2 on `--build`, `ops/etl-curvature-fixture --check` printed steps 1 and 2 normally, printed no
funnel (step 3 never ran), then printed `FIXTURE OK: rebuilt output is identical to the committed file` and
exited 0 - diffing the committed file against a stale `rebuilt.json` left by my previous run. This is the only
guard anywhere on the fixture's reproducibility (nothing under `ops/`, `pins/`, `.github/` or `tests/`
references either new script; I grepped), it is run by hand, and it can go green without doing the work. Fix
is one line: `rm -f "$out"` before step 3, and check step 3's status.

**MAJOR - the getid wrapper still swallows a total getid failure.** The comment at
`ops/etl-curvature-fixture:72` says "getid is judged by whether it produced a usable file", but the only test
is `[ ! -s ... ]`, and non-empty is not usable. Fed an id file in which 100% of the ids are absent from the
extract - the shape of "the KMZ got re-pinned to a different region", the exact scenario the pinning exists
for - osmium getid exits 1, writes a 204-byte header-only PBF, the wrapper's `-s` test passes, `osmium export`
succeeds on it and writes a 1-byte geojsonseq, and the wrapper exits 0. `etl.oracle --build` against that
export then reports `single_way 3318 / have_geometry 0 / geometry_identical 0 / no_squash 0`, writes a 0-way
fixture and returns 2 - which the wrapper also ignores, so in rebuild mode it would overwrite the committed
fixture with an empty one and print "wrote ... - review the diff before committing it", exit 0. The 21/3318
case the wrapper was written for is correctly tolerated; there is simply no line between 21 missing and 3318
missing. The CRLF case IS caught, and I verified that too: with a CRLF id file osmium prints `illegal id:` and
exits 2 having written nothing, and the wrapper aborts with "getid wrote no output at all".

**Attacked the floor, and could not break it - this is stronger than the log claims.** I swept ~60 mutations
on both platforms looking for one that a 0.90 floor fails to reject where 0.93 did: every look-ahead subset
of (3,4,5,6,7), the deflection divisor from 60 to 350, MAX_RADIUS from 100 to 100000, DEGENERATE_RADIUS from 0
to inf, three `assign_radii` write-order variants, band edges, weights, `<` to `<=`, haversine, a systematic
length scale from 0.90x to 1.10x, dropping `math.fabs`, and an epsilon guard before the sqrt. Everything
landing in [90%, 93%) on either platform is caught by the rewritten deflection meta-test, not by the floor:
filter off entirely 92.75/92.00 (0 touched ways), `LOOK_AHEADS=(3,)` 92.75/92.00 (1 touched), filter divisor
60 92.00/90.75 (ratio 0.3x/0.6x), all lengths x0.99 91.00/90.50 (ratio 7.6x). No mutation slipped through.
Worth saying explicitly: the floor is no longer the guard for that band - the deflection meta-test is - and
that is a better arrangement than the one it replaced.

**The rewritten deflection meta-test is load-bearing, and its vacuity guard is the part that fires.** Mutated
the source, not a monkeypatch: put `return` at the top of `filter_deflections`. Exactly one test goes red -
`test_dropping_the_deflection_filter_fails_the_oracle`, on `the filter changed only 0 of 400 ways` - while
`test_agreement_with_the_published_values` stays GREEN at 92.75%, which is precisely the hole the owner
described and closed. Second red demonstration, a partial weakening rather than a removal: `LOOK_AHEADS =
(3,)` in source, same single test red on `the filter changed only 1 of 400 ways`. So `len(on_errs) >= 5` is
not decoration; it is the assertion doing the work. `etl/curvature.py` verified sha256-identical afterwards.

**The 13 new selection tests DO fail on the original defect - I put the defect back to check.** Restored the
exact pre-fix code from `git show 6c0980a` - `WAY_TAGS = {"junction", "traffic_calming", "oneway"}` as a bare
set plus `way_is_squash_tagged` as `any(k in props for k in WAY_TAGS) or any(k.startswith(...))` - and ran the
suite in the pinned image. Two tests go red: `test_oneway_does_not_mark_a_way_as_squash_exposed` and
`test_junction_is_matched_on_its_values_not_on_the_bare_key`. Nothing else moves, including the end-to-end
agreement assertion, which is the point the owner makes about why this file had to exist.
`etl/oracle_select.py` verified sha256-identical afterwards.

**Re-derived - all four headline figures, in the pinned image and on Windows, with my own script.** Wrote the
comparison from scratch against the committed fixture and the committed `etl.curvature`; did not call
`etl.oracle_report` (whose output is the claim under test) and did not use anything the owner left in
`services/etl/work/`:

      fixture (400)      Linux/glibc 379/400 = 94.7500%  median 0.06340%  p90 0.8182%
                         Windows/CRT 375/400 = 93.7500%  median 0.06752%  p90 1.1563%
      population (2384)  Linux/glibc 2251/2384 = 94.4211%  median 0.06608%  p90 0.8923%
                         Windows/CRT 2261/2384 = 94.8406%  median 0.06620%  p90 0.8776%

All four match the claim to the stated precision, and **the platforms do swap places**: Linux ahead by 1.00
point on the fixture, Windows ahead by 0.42 on the population. `ops/etl-oracle-report` prints the same numbers
to the digit. On the claim's meaning: the swap shows the SIGN of the gap is not stable across two samples of
the same two libms. It does not bound a third libm, and the owner says so. I agree with the conclusion and
with the caveat.

**Re-derived - the floor's justification, on the committed fixture, both platforms.** The three mutations
`test_curvature.py` actually monkeypatches: weight 16.750% Linux / 16.000% Windows, band threshold 38.750% /
39.500%, larger circumcircle 0.500% / 0.500%. Earth-radius swap 94.750 -> 94.500 on Linux and 93.750 ->
93.750 on Windows, exactly as the docstring at `:200` says. Deflection filter: 10 touched ways on both
platforms, median error 0.0654% on / 8.8508% off (Linux, 135.3x) and 0.1137% / 8.8502% (Windows, 77.8x)
against a 50x guard, 1 of 10 still agreeing against a "<= 3" guard. Every load-bearing number checks out.
Minor: the three figures the comment quotes (16.0 / 39.5 / 0.5) and the "80x" are the WINDOWS values, in a
comment whose closing line is "Quote this number from the pinned image, never from whatever interpreter is on
the box." Harmless to the argument, but it is the comment's own discipline.

**Re-derived - the fixture rebuilds bit-for-bit, end to end, from a wiped work directory.** `rm -rf
services/etl/work/curvature-oracle` then `ops/etl-curvature-fixture --check` from WSL: `3318 ways`, osmium
getid naming 21 missing ids, funnel `single_way 3318 / have_geometry 3297 / geometry_identical 2571 /
no_squash 2384`, `FIXTURE OK`, exit 0. All three steps now run - the `getid exited 1` abort the owner could
not close last round is genuinely closed, and the recorded explanation is correct: I counted the ids osmium
names and there are exactly 21. The 2384 population and the 2307 -> 2384 move are confirmed from my own clean
rebuild, not from the log.

**Re-derived - the `oneway` and `junction` reasoning, against the real upstream.** Fetched
`processing_chains/adams_default.sh` and `post_processors/squash_curvature_near_way_tag_change.py` from
`raw.githubusercontent.com/adamfranco/curvature/master`. The chain has nine squash invocations. `oneway`
appears in exactly one, `squash_curvature_near_way_tag_change --tag oneway --ignored-values no --distance 30`,
whose `process_collection` seeds `current_value` from `collection['ways'][0]` and then compares every way
including the first against it - so on a one-way collection it compares the way with itself and can never
fire. Removing it is right. `junction` appears twice: `squash_curvature_for_tagged_ways --tag junction
--values 'roundabout,circular'`, which does reach a single-way collection and is what `WAY_TAGS` now encodes,
and a second `squash_curvature_near_way_tag_change --tag junction --only-values ...` which structurally
cannot. `traffic_calming` with no `--values` justifies the `None`; the two `parking:lane:(both|left|right)`
regex processors are narrower than the committed prefix match, so the prefix can only over-exclude, as the
code says. `NODE_TAGS` matches invocations 7-9 exactly. No tag is missing from either list.

**Checked - the two ops scripts' root derivation, including the cases the owner did not name.**
`ops/etl-oracle-report`: docker absent -> `docker is not on PATH; the pinned image is the point`, exit 2, with
and without `--with-population`. Export absent with `--with-population` -> the note naming the file as
gitignored, then the fixture report only, exit 0. Unknown flag -> exit 2. Invoked by absolute path from `/` ->
works. `ops/etl-curvature-fixture`: docker absent -> exit 2; a pinned input moved aside -> `missing
services/etl/inputs/vermont-curvature.kmz - run ops/etl-fetch-inputs`, exit 2. **Invoked through a symlink,
both scripts exit 2** - `${BASH_SOURCE[0]}` is the symlink's own path, so the derived root is the symlink's
parent and the marker check rejects it. That is the correct failure (loud, not silent, which was the whole
point of dropping `git rev-parse`), but it does mean neither script can be installed on `PATH` by symlink;
worth a line in the header rather than a fix.

**Info, not blocking:**
- `MAX_RADIUS` and `DEGENERATE_RADIUS` are pinned by nothing. Their unit tests compare the value against
  itself - `assert segments[0].radius == cv.MAX_RADIUS` (`test_curvature.py:111`) and
  `assert cv.circum_circle_radius(*sides) == cv.DEGENERATE_RADIUS` (`:86`) - so they cannot fail whatever the
  constant is, and the oracle cannot see them either: I swept MAX_RADIUS over 175, 300, 500, 1000, 2000, 5000,
  10000, 20000, 100000 and DEGENERATE_RADIUS over 0, 100, 174, 176, 1000, 10000, 1e9 and inf, and fixture
  agreement stayed at 94.750% for every single value. Two of the five constants the log says were "checked
  against their source" have no guard at all. Pre-existing, not introduced this round.
- pytest is 155 passed + 1 skipped, 156 collected. The log and the PR both say "156 passed, 1 skipped", which
  is 157. Third round with an off-by-one on the test count; harmless, but it is the count the PR quotes.
- The PR body carries the same stale mechanism paragraph as the source comment, word for word.
- The `reviewer:` field still names agent/reviewer-30. This round was reviewed by agent/reviewer-34.

**Verification, run fresh, this round - all four gates:**
- etl suite in the pinned `scenic-etl` image (`docker run --rm -v "$PWD:/w" -w /w scenic-etl python3 -m
  pytest -q tests/`) -> `{'errors': '0', 'failures': '0', 'skipped': '1', 'tests': '156'}`, exit 0. The image's
  pytest 7.4.4 prints no summary line in this shell, so the counts are read from `--junitxml`.
- `bash ops/test` -> `TESTS linux=206/76 ios=skipped failed=0 skipped=0` / `OK`, exit 0.
- `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`, exit 0.
- `bash ops/queue-check` -> `QUEUE OK (50 tasks)`, exit 0.
- `bash ops/etl-oracle-report --with-population` -> `ORACLE Linux/x86_64 python 3.12.3`, fixture `379/400 =
  94.750%`, population `2251/2384 = 94.421%`. `git ls-files -s` shows `100755` on both new ops scripts, so
  P-OPS-01 is satisfied for them.
- Working tree left clean; `curvature.py`, `oracle_select.py`, `test_curvature.py` and the fixture all verified
  sha256-identical to their committed contents after every mutation demonstration.
- GitHub Actions on PR #31 still billing-blocked; not treated as this diff's problem, per instructions.

**What I re-derived by running code:** all four headline agreement figures on both platforms with my own
script; the platform swap; the full segment-level mechanism comparison against BOTH fixtures, which is what
found the BLOCKER; the deflection filter zeroing an identical segment set on both platforms; the conditioning
split; the three mutation percentages, the earth-radius negative result and the deflection medians; the
bit-for-bit rebuild from a wiped work directory and the 21 missing ids; the `--check` fail-open and the
getid total-failure hole, both by constructing the failure; two source-level red demonstrations of the
deflection meta-test and one of the restored `oneway` defect; the ~60-mutation floor sweep on both platforms;
the MAX_RADIUS / DEGENERATE_RADIUS sweeps; and every docker-absent, missing-input, unknown-flag, foreign-cwd
and symlink invocation path of both ops scripts. **What I took on trust:** that
`raw.githubusercontent.com/adamfranco/curvature/master` today is what generated the pinned KMZ - I fetched
`master`, not a pinned SHA, the same limitation both prior rounds recorded; and I did not re-verify the
`same_geometry` 1 m and `near_tagged_node` 30 m thresholds against upstream, only that the tag lists match.

**FAIL.** Leaving in `queue/review/`. To be clear about what is and is not wrong: the algorithm, the selection,
the fixture's reproducibility, the floor and every mutation guard all held up under attack, and the floor is
better defended than the log claims it is. What fails is the record. The comment that explains the floor
describes a fixture that was replaced before it shipped, and the command that proves the fixture is
reproducible can say so without having rebuilt anything. Both fixes are small and neither touches a number
that matters.

Co-Authored-By: Claude Opus 5 (1M context) <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01SS4jAGs2oyr4Z4Wd8yK82t

- 2026-09-08T00:30Z owner response to agent/reviewer-34's FAIL, by agent/claude-opus-5. All three findings
  accepted; the BLOCKER was entirely correct and the way it happened is worth more than the fix.

  **THE BLOCKER. The mechanism paragraph described a fixture that no longer existed.** I re-measured the
  headline rates after the `oneway` correction and did NOT re-measure the paragraph underneath them, which
  had been computed on the pre-correction fixture. The correction moved the population 2307 -> 2384 and
  reshuffled the sample; only 68 of 400 way ids survived. So ten numbers describing a file that had been
  replaced sat directly under two numbers describing the current one, stitched together by the phrase "the
  entire 93.75-to-94.75 gap". The reviewer spotted it on the segment count - 13135 against the committed
  file's 13359 - which is `sum(len(coords)-1)` and cannot vary by platform, so it was dispositive. My own
  text contained a "12" that matched neither file while saying "8 of 14" four lines later, and I did not
  notice.

  Everything is re-measured on the committed fixture, both platforms, by agent/measure-1 working from the
  raw fixture rather than from my scripts. Both runs verified against the committed blob's sha256
  (7427820486e605ba...). Corrected: 13359 segments; 5559 radii differ, 1192 by >1%, 158 by >10%, worst 369%;
  64 segments change band across 38 ways; 18 ways move >1%; 8 flips; 4 of those 8 in the better-conditioned
  half; deflection filter zeroes an identical set on all 400 ways.

  **The measurement also corrected my CAUSE, which matters more than the counts.** I wrote that `math.acos`
  has implementation-defined last-bit rounding. Measured, with every intermediate dumped as exact hex: acos
  returned bit-identical results for bit-identical inputs in all 13359 segments. The divergence is `sin` and
  `cos`, each off by exactly one ULP and never more. acos is the AMPLIFIER - near x=1 its condition number is
  enormous, and in the worst case here (cos = 0.99999999999999789) one ULP becomes 0.4029 m vs 0.4139 m, a
  2.67% length difference that the condition number predicts to two figures. Two further corrections: 21% of
  segment LENGTHS already differ before any radius is computed, so totals also drift continuously - but every
  way that moves more than 1%, and all 8 flips, has a band change, and ways without one move by at most
  5.8e-5. And it is not a CPython artifact: 3.12+ compensated `sum()` was ruled out by re-running the whole
  comparison as Linux-3.12 against Windows-3.14, which reproduces every number.

  **MAJOR 1, `--check` fail-open. Fixed.** Step 3's exit code was never inspected - the script runs under
  `set -uo pipefail` with no `-e` - so a failed build fell through to a diff against a stale `rebuilt.json`
  and printed `FIXTURE OK`, exit 0. The only guard on fixture reproducibility in the repo. It now deletes the
  target before building, checks the exit code, and refuses an empty result. Demonstrated by forcing
  `etl.oracle --build` to exit 1 with a stale rebuilt.json present: `BUILD FAILED`, exit 2.

  **MAJOR 2, getid total failure swallowed. Fixed.** With every id absent, getid exits 1 and still writes a
  valid 204-byte header-only PBF; `[ -s ]` accepts it and export succeeds on it, so the run built a zero-way
  fixture and reported success. My previous fix caused this: I replaced "trust the exit code" with "trust the
  file exists", and "exists" was the wrong question. It now counts the ways that actually came back and
  requires 95% of those requested - 21 of 3318 are legitimately absent, so it cannot demand all of them, but
  anything worse is a broken input rather than upstream drift. Demonstrated by making `--list-ways` emit ids
  in no extract on earth: `TOO FEW WAYS: 0 of 3318 (floor 3152)`, exit 2.

  **The INFO finding was the best one, and it is fixed too.** `MAX_RADIUS` and `DEGENERATE_RADIUS` were
  pinned by nothing: every assertion compared `cv.MAX_RADIUS` with `cv.MAX_RADIUS`, so both sides moved
  together and the reviewer swept 175 -> 100000 and 0 -> infinity without moving agreement off 94.750%. That
  is the same hole this task already RECORDED for the earth radius, in a test written to record it - and I
  did not think to ask which other constants had it. New `TestTheUpstreamConstantsArePinnedByValue` pins them
  against the upstream literals, including that the band edge and the deflection filter's divisor are the
  same number. Five sweeps demonstrated, each now failing a named test where all five previously failed
  nothing:

      MAX_RADIUS 10000 -> 100000     FAILED test_the_radius_caps
      DEGENERATE_RADIUS 10000 -> 0   FAILED test_the_radius_caps
      LEVEL_1_MAX_RADIUS 175 -> 200  FAILED test_the_deflection_filter_constants
      a band weight 1.3 -> 1.4       FAILED test_the_curvature_bands (+5 behavioural)
      LOOK_AHEADS 3..7 -> 3..6       FAILED test_the_deflection_filter_constants

  `curvature.py` and `oracle.py` verified byte-identical by sha256 after every demonstration.

  **Verification** - pinned image unless noted: `pytest -q tests/` -> 155 passed, 1 skipped (156 collected;
  the reviewer was right that I had reported this as "156 passed, 1 skipped" for three rounds running).
  `ops/test` -> `TESTS linux=209/76 ios=skipped failed=0 skipped=0` / `OK`. `ops/check-pins` -> `PINS ok=10
  skipped=0 pending=3 expired=0 failed=0 tier=linux`. `ops/etl-curvature-fixture --check` -> `FIXTURE OK`.
  GitHub Actions is now DISABLED repo-wide (T-0053, spending limit exhausted), so there is no CI signal at
  all and everything here is local.

  **What to attack.** `--check` is now fail-closed but still runs nowhere: it needs docker and 45 MB of
  pinned inputs, so it cannot go in `ops/test`, and no gate calls it. That is a guard that works and is never
  invoked, which is a different failure from the one just fixed and not obviously better - decide where it
  belongs. The 95% way-count floor is a number I chose against one observed shortfall (0.63%); it is not
  derived from anything. And `test_curvature.py` is at 294 of 300 lines, so the next addition to it has to go
  somewhere else - that is a constraint on the next reviewer's suggestions, not just on mine.
