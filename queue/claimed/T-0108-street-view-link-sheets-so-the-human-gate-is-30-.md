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
touches: [services/etl/etl/streetview.py, services/etl/tests/test_streetview.py, ops/score-review]
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
