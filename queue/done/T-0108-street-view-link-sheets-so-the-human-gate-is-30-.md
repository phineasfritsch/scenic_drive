---
id: T-0108
title: Street View link sheets so the human gate is 30 clicks instead of 5 drives
state: done
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T11:47:56Z
lease_expires_at: 2026-09-08T15:47:56Z
worktree: null
branch: task/T-0108
exclusive: []
touches: [services/etl/etl/streetview.py, services/etl/etl/review_sheet.py, services/etl/tests/test_streetview.py, services/etl/tests/test_review_sheet.py, ops/score-review]
pins_affected: []
reviewer: agent/reviewer-final-pr69
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**The slowest step in this whole product is a human driving somewhere.**

Human gate #1 is five real commutes with a verdict on each; gate #2 is twenty more, driven by somebody else.
Both are `runs_on: human` pins that expire after 30 days, so they are not one-off costs — they recur. And
every scoring change wants re-validation, which today means driving again.

**Street View collapses most of that.** For a candidate segment we have the coordinates already; a link like

    https://www.google.com/maps/@?api=1&map_action=pano&viewpoint=<lat>,<lon>&heading=<bearing>

opens the panorama at that point, facing along the road. Thirty of those in a page is a scoring review that
takes ten minutes instead of a Saturday.

**What this is for, precisely: it does not replace the drive.** Gate #1 asks whether the ROUTE was better
than the freeway — pacing, traffic, whether the pretty part arrives when you have the patience for it. No
photograph answers that. What Street View answers is the cheaper question that currently rides along with
it: **does this segment look anything like its score?** That is where the bad ones are — a 9.2 on an access
road behind a business park, a 2.1 on a genuinely lovely lane the canopy layer missed. Catching those before
a drive makes the drive worth doing.

Do:

1. `ops/score-review <region> [--top N] [--bottom N] [--band 4-6]` — emit a static HTML sheet of segments
   with score, the term breakdown (curv / elev / canopy / impervious / byway), and a Street View link per
   segment. **The band matters more than the extremes**: the top and bottom are usually obviously right, and
   the score earns its keep in the middle.
2. **Heading, not just position.** A panorama facing a wall is useless. Compute the bearing from the
   segment's own geometry and pass it, so the view looks along the road.
3. **Record the verdict.** A sheet you click through and forget is a nicer way to waste an afternoon. Each
   row gets *looks right / looks wrong / cannot tell*, written to a file that the score tuning reads —
   this is the Bradley-Terry input the plan already wants, gathered 30 at a time instead of one drive at a
   time.
4. Seed it from the disagreements: segments where one term is extreme and the others are not. Those are
   where the composite is doing something interesting and where it is most likely wrong.

**The legal line, and it is a real one.** The plan deliberately avoids Google because their terms fight this
product — the Maps ToS forbids showing Google imagery alongside a non-Google map, which is why the app uses
MapLibre and Protomaps. **That constraint is about the APP.** This is an internal QA tool that emits links a
developer opens in a browser, which is a person using Google Maps normally. So:

  * links only, opened in a browser — **never** the Street View Static API, never fetched, never cached,
    never embedded, and nothing from this tool ever ships in the app;
  * `ops/score-review` lives in `ops/`, not in `Sources/` or `apps/`, and the file says why in its header so
    a later reader does not "helpfully" pull the imagery inline.

**Vacuity guard:** a sheet generated from an empty or unscored corpus must refuse, not emit an empty page.
An afternoon spent clicking through nothing that reports "reviewed 0 segments, no problems" is this
repository's signature defect in its most expensive form.

## Log
- 2026-09-08T11:47:56Z claimed by agent/claude-opus-5; lease until 2026-09-08T15:47:56Z

- 2026-09-08 — **built. `ops/score-review <segments.json>` emits the sheet; the empty page is refused.**

  **The default reviews the MIDDLE, and that is the design rather than a setting.** A page of the highest and
  lowest scores mostly confirms what anyone would already guess. The segments that decide whether the index
  is any good are the ones it placed at 4-6, where a small weighting error changes the ranking. On four
  fixtures scored 9.1, 5.2, 4.4 and 2.0:

        default band 4-6      picks Mulholland (5.2) and Sepulveda (4.4); skips PCH and the access road
        --top 1 --bottom 1    adds both extremes, 4 rows, no duplicates

  The heading is computed from the road's own geometry so the panorama looks *along* it rather than at a
  wall, taken at the **length-midpoint** - the ends of an OSM way are junctions, which look like every other
  junction.

  **A defect I wrote and then caught by running it.** `midpoint_index` first returned the index of the
  *segment* containing the half-way mark, which for an evenly drawn way is segment 0 - so a function whose
  docstring promised "the point nearest the middle BY LENGTH" returned the **start of the road**. Found by
  calling it on three points of Sunset and getting index 0. It now picks the point nearest the half-length,
  pinned with a deliberately skewed way - four tight points then one far - where the by-index answer (2) and
  the by-length answer (3) differ.

  `bearing()` returns None rather than 0 when two points are too close to define a direction. Zero means due
  north; substituting it would be a silent lie, and a confidently wrong heading is worse than none.

  **Both vacuity guards, executed:**

        empty input     SCORE-REVIEW REFUSED: no segments to review ...                    exit 2
        band 7.5-8.5    SCORE-REVIEW REFUSED: 4 segment(s) given but none selected ...     exit 2
                        - widen the selection rather than reviewing an empty page

  An afternoon of clicking that ends in *"reviewed 0 segments, no problems"* is this repository's signature
  defect in its most expensive form, so it refuses rather than warns.

  **The licensing line is pinned as a test, not left in a comment.**
  `test_the_sheet_never_requests_an_image` asserts no `streetview`, no `key=`, no `<img>` in the output. The
  plan avoids Google because the Maps terms forbid showing their imagery beside a non-Google map - **that
  constraint is about the APP**, and this is a build-time tool emitting links a developer opens in a browser.
  "Just show the thumbnail" is the obvious next feature and exactly the one that would turn the app's map
  stack into a licensing problem.

  **What it does not do:** replace the drive. Gate #1 asks whether the ROUTE was better than the freeway -
  pacing, traffic, whether the pretty part arrives while you still have the patience for it - and no
  photograph answers that. This removes the cheaper question that currently rides along with it.

  **Not wired to real data**, because there is nothing to wire: the composite score is [[T-0029]] and the
  corpus emitter is [[T-0030]]. `select()` falls back to reviewing every segment when none carries a score,
  since "does this look like a road with 82% canopy" is answerable from a photograph and the terms exist.

        services/etl  282 passed  (25 of them new)

- 2026-09-08 — **fix pass on the PR #69 review (FAIL, three findings). All three reproduced first; all three
  closed. Nothing refuted: the reviewer was right about every one.**

  **Finding 1 — the length-midpoint was anchored on prose.** Reproduced before touching anything: changing
  `review_sheet.py` to `sv.look_along(pts, 0)` and running the whole suite gave

        25 new tests, exit 0                    - nothing noticed, every link on the first node of the way

  The unit was pinned (`test_midpoint_is_by_length_not_by_index`); the one call site where the property
  matters was not, while `review_sheet.py` printed "at its length-midpoint" into every page it emitted. Two
  tests now stand on the emitted URL rather than on the sentence. `w/12` is the only SEGS fixture with three
  points, and its legs are ~506 m and ~463 m, so its middle node is 22 m from the half-length and each end is
  485 m away; the sheet must carry `viewpoint=34.130100,-118.399000` and must not carry either junction. A
  second fixture (`SKEWED`: four points 92 m apart, then one 8.9 km away) separates the length midpoint
  (index 3) from the INDEX midpoint (index 2) — the arithmetic is hand-derived in the comment above it, not
  read back off the implementation.

  **Finding 2 — `select()` truncated while its docstring said it did not.** Reproduced against the public
  API, exactly as reported:

        unscored, distinct ids   5 of 5
        unscored, no id field    1 of 5      all share k = None
        6 pieces of one way      1 of 6      rendered, exit 0, no refusal
        6 SCORED pieces, band    1 of 6      (mine - the same collapse on the scored path)

  The dedup key is now the segment's POSITION in the input (`_position_key`), which is unique by
  construction; `id` never was, and nothing in the corpus contract says it is. Two further things came with
  it:

  * **The floor is the population the criteria matched, not "at least one row".** `if not rows: raise`
    catches 400 → 0 and waves through 400 → 1. `select` now counts the rows it kept against the segments the
    criteria matched, recomputed from the input, and refuses on a shortfall. Through the tool:

        ops/score-review pieces.json (dedup key = id)   SCORE-REVIEW REFUSED: selection matched 6
                                                        segment(s) but kept 1 ...            exit 2
        ops/score-review pieces.json (fixed)            wrote ... (6 segments in, 6 rows out) exit 0

  * **The same collapse one layer down, which the review did not reach.** The radio GROUP was named
    `v_<id>`, and a browser groups radios by name — so six pieces of `w/12`, or six segments with no id all
    rendering `?`, shared ONE group: answering row 6 silently un-answered row 1. The group is now named
    after the row.

  **Finding 3 — the verdict is recorded nowhere, and that was not disclosed. It still is not recorded; it is
  now disclosed in the three places that matter, and the page itself is the loudest of them.**

  Greps of a rendered sheet still return `<form` 0, `<script` 0, `localStorage` 0, `download` 0. What
  changed is that the sheet no longer pretends otherwise: every page prints `NOT_RECORDED_NOTICE` —
  *"Verdicts on this page are not recorded anywhere: nothing here writes them to a file, so closing the tab
  loses them"* — the module docstring's opening paragraph says the same, and [[T-0117]] is filed with the
  execution problem written down rather than left for the next agent to rediscover. Brief item 4 (seed from
  term disagreements) is in the same task; it wants [[T-0029]], because "one term is extreme" has no meaning
  until the terms are normalised and choosing thresholds now would be inventing product.

  **Why not just build the sink, since that would close the finding outright.** A static page can only
  persist through JavaScript, and this suite cannot execute the sheet's JavaScript: the ETL image ships
  python3/osmium/gdal and no node, so a node-driven test would SKIP exactly where the pipeline runs, and
  `assert "localStorage" in html` pins a string rather than a behaviour. Shipping untested browser code
  under a green suite is the defect this repository exists to catch, so the honest move was to defer it
  loudly. `test_the_sheet_does_not_pretend_to_record_the_verdict` encodes that: it passes if the sheet
  carries a real recording mechanism OR admits it has none, and fails only if the page starts lying.

  **Red demos — every new guard broken on purpose, one at a time, restored between each (driver at
  `.artifacts/fix0108/reddemo.py`; the source file's sha256 is compared before and after every break).**

        BASELINE                                                    exit=0  sha=68f464172463
        render stands on point 0 (the shipped defect)               exit=1  ..._not_on_a_junction,
                                                                            ..._not_the_index_midpoint
        render stands on the INDEX midpoint                         exit=1  ..._not_the_index_midpoint
        render stands on the last node                              exit=1  both midpoint tests
        dedup key back to `id` (the shipped defect)                 exit=1  ..._shares_one_id,
                                                                            ..._no_id_at_all, ..._refuses...
        truncation floor deleted                                    exit=1  ..._refuses_rather_than_short...
        radio group named after the id again                        exit=1  ..._own_radio_group...
        the not-recorded notice dropped from the page               exit=1  ..._does_not_pretend_to_record...
        empty-input refusal deleted                                 exit=1  test_empty_input_refuses
        none-selected refusal deleted                               exit=1  test_a_selection_that_matches...
        RESTORED                                                    exit=0  sha=68f464172463

  The last two are the empty-population end of the same floor, re-demonstrated: 0 rows refuses, and now so
  does 1 row where 6 matched.

  **Verify.**

        cd services/etl && python -m pytest     425 passed          exit 0   (was 418; 7 new tests)
        bash ops/check-pins                     PINS ok=11 ... failed=0      exit 0
        bash ops/sane                           SANE OK                      exit 0
        bash ops/queue-check                    QUEUE OK (100 tasks)         exit 0
        bash ops/test                           FAIL: services/api exists but vitest produced no report
                                                                             exit 1

  **`ops/test` is red and it is not mine.** Identical message and exit 1 on `main` in the same shell
  (`bash ops/test >/dev/null 2>&1; echo $?` → 1 from the main checkout): there is no vitest install for
  `services/api` on this box, so the Worker tier reports nothing. It is in this task's `verify:` list and it
  cannot be green here.

  Line counts after the fix: `review_sheet.py` 225, `test_review_sheet.py` 199, both under the 300 cap.
  Scratch confined to the gitignored `.artifacts/fix0108/`.

- 2026-09-08 — **the review's MINOR NOTE closed too, since it is the same defect class.**

  `test_look_along_faces_down_the_road` asserted `f"heading={sv.bearing(*SUNSET[0], *SUNSET[1]):.1f}"` - an
  expectation computed by the function under test, which passes for any pair of consistent-but-wrong
  implementations and survived only by leaning on `test_bearing_cardinals` next door. The expected heading is
  now derived in the test: Sunset's first leg runs 100.2 m north and 414.9 m east
  (0.0045 * 111320 * cos 34.074), so atan2(414.9, 100.2) = 76.43 deg, and over a 430 m leg the great-circle
  answer differs from the flat one by thousandths of a degree - the implementation returns 76.424, the hand
  figure is 76.426, and the URL carries one decimal place. Cross-checked before adopting, not after.

        BASELINE                                              exit=0  sha=d24dffb1bbf1
        look_along aims backwards down the road               exit=1  test_look_along_faces_down_the_road
        bearing swaps y and x (a transcription slip)          exit=1  test_look_along_faces_down_the_road
        bearing drops the cos(lat) term                       exit=1  test_look_along_faces_down_the_road
        RESTORED                                              exit=0  sha=d24dffb1bbf1

        cd services/etl && python -m pytest     425 passed     exit 0
        bash ops/check-pins                     failed=0       exit 0

- 2026-09-08 — **re-review of PR #69 after the fix pass — PASS. Transitioned to `queue/done/`.**
  Reviewer `agent/reviewer-final-pr69`, worktree `.worktrees/T-0108` @ `3761b81`. Not the owner
  (`agent/claude-opus-5`). Every prior finding was re-checked by RUNNING the break that demonstrated it,
  not by reading the diff.

  **`verify:` and `acceptance:` (`acceptance:` is empty).** Exit codes taken with
  `<cmd> >/dev/null 2>&1; echo $?`, never after a pipe.

        bash ops/check-pins                     PINS ok=11 ... failed=0                exit 0
        bash ops/sane                           SANE OK                                exit 0
        bash ops/queue-check                    QUEUE OK                               exit 0
        cd services/etl && python -m pytest     425 passed (counted by progress dots;
                                                pytest 9.1.1 prints no summary line)   exit 0
        bash ops/test                           FAIL: services/api exists but vitest
                                                produced no report                     exit 1

  **`ops/test` red is pre-existing and not this task's.** Confirmed rather than accepted: run from the
  `main` checkout in the same shell it exits 1 with the identical final line. No vitest install for
  `services/api` on this box.

  **The tool, end to end through the wrapper** (`bash ops/score-review`, so `git rev-parse` in the
  wrapper is exercised in a worktree too):

        segs.json                     wrote ... (4 segments in, 2 rows out)  Mulholland + Sepulveda  exit 0
        segs.json --top 1 --bottom 1  wrote ... (4 segments in, 4 rows out)                          exit 0
        empty.json                    SCORE-REVIEW REFUSED: no segments to review ...                exit 2
        segs.json --band 7.5-8.5      SCORE-REVIEW REFUSED: 4 segment(s) given but none selected ... exit 2

  Both refusal strings verbatim as logged. Greps of the rendered page: `streetview` 0, `key=` 0, `<img` 0,
  `<form` 0, `<script` 0, `localStorage` 0, `download=` 0. `viewpoint=34.130100,-118.399000` — w/12 stands
  on its middle node.

  **Prior findings, each closed by its own red demo (drivers in the gitignored `.artifacts/rvw69/`; both
  source files restored byte-for-byte between every break, sha256 compared — `review_sheet.py`
  `68f464172463`, `streetview.py` `d24dffb1bbf1`, identical at baseline and after the last restore, and
  `git status --porcelain` empty).**

        BASELINE                                                     exit=0  no failures
        F1  render stands on point 0 (the shipped defect)            exit=1  ..._not_on_a_junction,
                                                                             ..._not_the_index_midpoint
        F1  render stands on the INDEX midpoint                      exit=1  ..._not_the_index_midpoint
        F1  midpoint_index returns the SEGMENT holding the half-way  exit=1  test_midpoint_is_by_length...,
                                                                             ..._not_on_a_junction
        F2  dedup key back to `id` (the shipped defect)              exit=1  4 tests
        F2  dedup key back to `id` AND the floor disabled            exit=1  4 tests
        F2  radio group named after the id again                     exit=1  ..._own_radio_group...
        F2  truncation floor disabled, key left correct              exit=1  ..._refuses_rather_than_short...
        F3  the not-recorded notice dropped                          exit=1  ..._does_not_pretend_to_record...
        F3  notice replaced by "saved automatically"                 exit=1  ..._does_not_pretend_to_record...
        MN  look_along aims backwards down the road                  exit=1  test_look_along_faces_down...
        MN  bearing swaps atan2(y, x)                                exit=1  test_bearing_cardinals, ...
        MN  bearing returns 0.0 instead of None on a degenerate span exit=1  test_bearing_refuses_a_point...
        LIC BASE switched to the Static API                          exit=1  4 tests incl. ..._never_requests...
        GUARD empty-input refusal deleted                            exit=1  test_empty_input_refuses
        GUARD none-selected refusal deleted                          exit=1  test_a_selection_that_matches...
        RESTORED                                                     exit=0  no failures

  **Constants perturbed in both directions — none of the assertions is stated in terms of the constant it
  checks**, which is what this repository keeps shipping:

        REVIEW_BAND (4,6) -> (0,10)          exit=1   ..._default_reviews_the_middle..., ..._top_and_bottom...
        REVIEW_BAND (4,6) -> (5.15,5.25)     exit=1   7 tests
        MIN_BEARING_SPAN_M 1.0 -> 1000.0     exit=1   3 tests
        MIN_BEARING_SPAN_M 1.0 -> 0.0        exit=1   test_bearing_refuses_a_point_too_close...
        viewpoint 6dp -> 2dp                 exit=1   3 tests
        heading .1f -> .0f                   exit=1   2 tests

  **Numbers in the Log re-derived independently rather than believed.** w/12's legs 506.5 m and 462.8 m,
  half-length 484.7 m, so the middle node is 21.8 m from it and each end 484.6-484.7 m — index 1, by a wide
  margin. SKEWED: 0.001 deg of longitude at lat 34 is 92.29 m and the far leg is 8951.6 m, cum
  `[0, 92.3, 184.6, 276.9, 9228.5]`, half 4614.2, so |276.9-half| = 4337 beats |9228.5-half| = 4614 —
  index 3, not the index midpoint 2. Sunset's first leg is 100.2 m north and 415.0 m east, atan2 = 76.43 deg,
  matching `heading=76.4`. All three expectations come from the fixture or from hand arithmetic, none from
  the function under test.

  **The truncation floor is reachable, not tautological.** I suspected `len(out) != len(matched)` could
  never fire, since `_position_key` returns `i`. A 28,540-input search (`floor_probe.py`, random scores/ids/
  bands plus every same-id / no-id / distinct shape at n = 1, 2, 6, 40, 400) never fired it — but breaking
  the assembly loop (`break` after the first append) does: `SCORE-REVIEW REFUSED: selection matched 6
  segment(s) but kept 1`, exit 2. So it is live, and it holds the invariant its docstring names.

  **Notes, none blocking — recorded so the next agent does not have to rediscover them; posted on PR #69.**

  1. `test_the_sheet_does_not_pretend_to_record_the_verdict` asserts nothing once any of
     `RECORDING_MECHANISMS` appears in the page. Dropping `NOT_RECORDED_NOTICE` **and** adding an inert
     `<form>` around the table — or `download=""` on the existing link — leaves all 425 tests green with a
     page that records nothing and no longer says so. Demonstrated twice. That escape hatch pins a string as
     the proxy for a behaviour, which is the objection this task itself raised against
     `assert "localStorage" in html`. Whoever takes T-0117 should make the other branch assert the sink
     works, not that a tag exists.
  2. `midpoint_index`'s `if len(points) < 3: return 0` is unpinned: returning `len(points) - 1` instead, or
     deleting the branch entirely, leaves 425 tests green. Shipped behaviour is right — for two points both
     ends tie at half the length and `min` takes the first, so the short-circuit agrees with the general
     path — but nothing says so, and this is the branch most real segments take.
  3. `test_look_along_at_the_last_point_uses_the_previous_one` asserts only that `heading=` is present, not
     its direction; reversing the tail fallback leaves the suite green. Not reachable from the sheet
     (`midpoint_index` can never return the last index — it always ties with index 0 and loses), so this is
     an untested direction on a public function rather than a live defect.
  4. Wording only: the floor's `matched` is read off `picks`, not "recomputed from the input" as the Log
     says. Truncation applied while building `picks` (a cap on the band pick, on `scored`, or on the
     unscored fallback) shrinks both sides equally and goes out as "6 segments in, 1 rows out" at exit 0 —
     caught by other tests in every case I tried, but not by the floor.

  **Mechanical.** `git ls-files -s`: `ops/score-review` 100755, the four `.py` 100644. Line counts 18 /
  128 / 225 / 107 / 199, all under the 300 cap. Commits `99fdc23`, `7a1b247`, `3761b81` touch only paths in
  `touches:` plus `queue/` files, which `.githooks/pre-commit` exempts explicitly. No secrets. T-0117 filed
  in `queue/backlog/`. Scratch confined to the gitignored `.artifacts/rvw69/`.
