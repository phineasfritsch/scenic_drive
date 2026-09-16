---
id: T-0107
title: second region around UCLA, because the developer who has to drive the routes lives in Westwood
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T11:41:59Z
lease_expires_at: 2026-09-08T15:41:59Z
worktree: null
branch: task/T-0107
exclusive: []
touches: [services/etl/regions/, services/etl/etl/region.py, ops/etl-extract]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**The plan's success criterion is "the developer drives a route this app made and it was better than the
freeway." The developer is in Westwood. The corpus is 350 miles away.**

Every region artifact today is `sfbay`: the bbox, the recorded counts, the curated seeds, the fixtures, the
human gates. Human gate #1 is five real commutes driven by the person building this, and gate #2 is twenty
more. Neither can happen from Los Angeles against a Bay Area graph, and the plan's own risk table calls
route quality on the developer's own commute *the thing that kills the product*.

So this is not "add a second market". It is **moving the feedback loop to where the developer is**, which
is the difference between tuning the score against roads you can drive tomorrow and tuning it against
screenshots.

**What LA has that makes it a good scenic test bed** — arguably better than the Bay Area:

  * **Santa Monica Mountains**, 15 minutes from UCLA: Mulholland Drive, Topanga, Malibu, Latigo and Las
    Flores canyons. Dense curvature with real elevation, immediately adjacent to dense city.
  * **PCH**, the coastal case, where the road is straight and the score must still be high — a direct test
    that `E` is not merely a proxy for `M`.
  * **Angeles Crest (CA-2)**, an hour out: sustained mountain highway, the long-drive case.
  * **Palos Verdes**, the coastal-suburban case.
  * And the hard negative it shares with nowhere in the Bay Area: **the 405 and Sepulveda Pass**, where a
    scenic detour has to beat a freeway everybody already hates.

Do:

1. `services/etl/regions/socal/region.json` — id, name, counties, bbox. Proposed bbox, argued rather than
   asserted:

        min_lon -119.00   west past Leo Carrillo, so PCH and the Malibu canyons are whole
        max_lon -117.85   east to the far end of Angeles Crest
        min_lat  33.70    south past Palos Verdes
        max_lat  34.45    north over the San Gabriel crest

   1.15 x 0.75 degrees, comfortably inside `region.py`'s MIN_SPAN_DEG/MAX_SPAN_DEG and SMALLER than
   `sfbay`'s 2.07 x 2.07, so the fifteen-minute build promise holds.

2. **Do NOT invent the counts.** `region.json`'s counts block is described in its own comment as *"Recorded
   from a real extract, not invented"*, and `checkbounds` correctly returns 2 (`cannot tell`) for a region
   with none. Ship the region with no counts, and record them with `ops/etl-extract --record-counts` on a
   real extract. A fabricated baseline is worse than none: it would make `ops/sane` assert against a number
   nobody measured.

3. Everything region-scoped has to stop assuming `sfbay`. Grep for the literal before writing code — the
   region id appears in fixture paths, curated seed directories and at least one pin. Whatever is hard-coded
   is the actual size of this task.

4. `curated.yaml` for socal: the plan wants 30 seeds per region. Twelve good ones beat thirty padded — and
   for the human gate, the seeds that matter are the ones within 30 minutes of Westwood.

**Ordering.** The ETL chain (T-0023 through T-0028) has to merge first; those branches carry `region.py`,
the extract and the scoring modules. Filed now because the region choice changes what the fixtures should
be, and fixtures written for sfbay will otherwise have to be written twice.

**Not proposed: dropping sfbay.** The Bay Area fixtures encode real work — the Altamont bbox correction, the
recorded class counts, the flagship 280/Cañada/Skyline shape. Two regions also proves the pipeline is not
accidentally single-region, which is worth having before a third.

## Log
- 2026-09-08T11:41:59Z claimed by agent/claude-opus-5; lease until 2026-09-08T15:41:59Z
