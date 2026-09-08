---
id: T-0110
title: sfbay recorded counts describe the pre-correction bbox, so ops/sane gates against the wrong region
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/regions/sfbay/region.json]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**The first real extract this project has ever run failed its own bounds check, and the extract is right.**

`ops/etl-extract --region sfbay`, against a freshly fetched `california-latest.osm.pbf` (1.3 GB,
md5-verified against Geofabrik's sidecar):

    BOUNDS FAIL
      motorway:    15572 vs recorded 19515   (-20.2%,  +/-15% allowed)
      primary:     21055 vs recorded 26578   (-20.8%)
      secondary:   40672 vs recorded 51556   (-21.1%)
      tertiary:    29845 vs recorded 38111   (-21.7%)
      residential:135776 vs recorded 183831  (-26.1%)
      service:    361277 vs recorded 473124  (-23.6%)
      park:         4362 vs recorded  5670   (-23.1%)
      peak:         1198 vs recorded  1470   (-18.5%)

**Every class is low by a uniform 18-26%, and that uniformity is the finding.** A tag-filter defect hits one
class. A bbox difference hits all of them, roughly in proportion to how densely that class covers the area
that changed.

**Which is exactly what happened, and it is written in the region's own file.** `region.json`'s bbox comment
records that the eastern edge was `-121.20` until `agent/reviewer-23` measured what that pulled in — Tracy
and Stockton, neither in the nine ABAG counties — and quantifies it: *"23.8% of every way in the extract -
28.6% of residential, 26.3% of service, 22.4% of motorway."* The bbox was corrected to `-121.55`. **The
counts were not re-recorded.**

Predicting today's numbers from the recorded ones and reviewer-23's own percentages:

    class        recorded   predicted if stale   measured now   error
    residential    183831              131,255        135,776   +3.4%
    service        473124              348,692        361,277   +3.6%
    motorway        19515               15,144         15,572   +2.8%

Three independent classes agree to within 3.6%, and the residual is the right sign and size for OSM growth
between reviewer-23's measurement on 2026-09-07 and today's daily rebuild.

**So the baseline describes a region 20-26% larger than the one the code now cuts**, and it is the baseline
`ops/sane` check 4 gates against. The bbox correction fixed the extract and left the yardstick measuring the
old shape — which is the same defect one level up from the one it fixed: *"a bbox whose own comment said
Altamont while reaching 40 km past it made the recorded counts a quarter Central Valley, so the baseline
ops/sane gates against was measuring the wrong region."*

Do:

1. Re-record the counts from the corrected bbox. The real run is in `work/sfbay/meta.json`, built
   `2026-09-08T12:10:39Z` from `california-osm.pbf` at 1,327,206,195 bytes, bbox
   `-123.62,36.85,-121.55,38.92`.
2. **Record WHICH run**, in the file. sfbay's counts comment already says *"Recorded from a real extract, not
   invented"*; it should also say which extract, so the next person who sees a 20% swing can tell a stale
   baseline from a broken filter without reconstructing this argument.
3. `road: 3 vs recorded 5` is inside the small-class tolerance but worth a glance - a class with three
   members is one mapper's afternoon from moving.

**Do not widen the tolerance.** +/-15% is doing its job here: it caught a stale baseline on the first real
run. A tolerance loose enough to accept both bboxes would accept the Central Valley coming back.

**Ordering.** `region.json` lives on the ETL chain, not on `main`, and `task/T-0028` currently has an agent
on it. Do this on a branch that carries the file, not in that worktree.

## Log
