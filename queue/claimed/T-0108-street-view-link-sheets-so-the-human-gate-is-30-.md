---
id: T-0108
title: Street View link sheets so the human gate is 30 clicks instead of 5 drives
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T11:47:56Z
lease_expires_at: 2026-09-08T15:47:56Z
worktree: null
branch: task/T-0108
exclusive: []
touches: [services/etl/etl/streetview.py, services/etl/etl/review_sheet.py, services/etl/tests/test_streetview.py, services/etl/tests/test_review_sheet.py, ops/score-review]
pins_affected: []
reviewer: null
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
