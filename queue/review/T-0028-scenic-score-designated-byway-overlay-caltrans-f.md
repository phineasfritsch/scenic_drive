---
id: T-0028
title: Scenic score: designated byway overlay (Caltrans + FHWA), snapped to OSM ways
state: review
owner: agent/claude-opus-5
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T20:11:54Z
lease_expires_at: 2026-09-08T00:11:54Z
worktree: ../wt/T-0028
branch: task/T-0028
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: agent/reviewer-33
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Caltrans Scenic Highway System GIS layer + FHWA America's Byways. Public domain / state open data.
Snap to OSM ways and set a byway flag worth +0.15 to E, capped.

ORACLE: byway-flagged ways must rank materially above class- and region-matched non-byway ways. That is the
second external oracle in the plan (the first being Curvature).

## Log

## Log
- 2026-09-07T14:20:00Z VERIFIED ENDPOINTS (live, 2026-09-07). The brief's assumed NTAD/BTS ArcGIS org is DEAD for this dataset: services.arcgis.com/xOi1kZaI0eWDREZv returns {"error":{"code":400,"message":"Invalid URL"}} for every scenic-byway name variant, though it does host other real NTAD layers. The working sources are:
- 2026-09-07T14:20:00Z FHWA, national: https://geo.dot.gov/server/rest/services/US_Scenic_Byways/MapServer/107/query?where=1=1&outFields=*&f=geojson -> HTTP 200, count 648. Esri MapServer (not FeatureServer) but /query supports f=geojson. Fields: Admin_Org, Type, Trail_Name - `Type` carries the designation category (National Scenic Byway vs All-American Road); enumerate its coded values before filtering. An unfiltered pull is ~29 MB, so filter or use the CA layer.
- 2026-09-07T14:20:00Z Caltrans, California: https://services1.arcgis.com/0MSEUqKaxRlEPj5g/arcgis/rest/services/CA_Scenic_Hwys/FeatureServer/0/query?where=1=1&outFields=*&f=geojson -> HTTP 200, count 273, ~4.2 MB total. Fields: Status (short coded designation - pull its coded-value domain before hard-coding, do NOT assume "OD"/"E"), RTE, DIST, CO, LOCATION, DESIG_DATE, MILES, PM1/PM2/SPM1/SPM2. Caltrans's own ArcGIS org.
- 2026-09-07T14:20:00Z NOTE: geo.dot.gov layer 11 ("CA_Scenic_Byways") has essentially the SAME schema as the Caltrans layer, so FHWA appears to have ingested Caltrans's data rather than maintaining an independent federal layer for California. Use the Caltrans source for CA and treat layer 107 as the national fallback - do not double-count a segment that appears in both.
- 2026-09-07T14:20:00Z LICENCE: Caltrans states an as-is disclaimer, access level public, accessInformation "California Department of Transportation" - that is CA-OpenData, already in KNOWN_LICENSES. The FHWA service carries NO explicit terms page; public domain is INFERRED from it being a federal work, not verified. Record it as inferred in the manifest notes rather than asserting US-PD-17USC105 outright.
- 2026-09-07T20:11:54Z claimed by agent/claude-opus-5; lease until 2026-09-08T00:11:54Z

- 2026-09-07T21:10Z Handing to agent/reviewer-33; state -> review.

  **Endpoints re-verified live**: Caltrans FeatureServer returns count 273, geo.dot.gov MapServer layer 107
  returns count 648. Both still exactly what the earlier research recorded.

  **The Status field, which decides two thirds of the data.** The earlier note warned against assuming what
  `Status` means. It has values {E: 207, OD: 66} and NO published coded-value domain - the layer describes
  itself only as "eScenicHwys2014", so the meaning is not in the service at all. Sourced from Caltrans's own
  scenic-highway programme:

      E   Eligible - the legislative designation, assessed on the LANDSCAPE: the breadth of what a traveller
          can see, its scenic quality, and how far development intrudes on the view.
      OD  Officially Designated - an eligible highway whose LOCAL GOVERNMENT applied to Caltrans and adopted
          a Corridor Protection Program limiting development and outdoor advertising.

  The difference is administrative, not scenic. Scoring only OD would discard 207 of 273 segments for reasons
  that have nothing to do with how the road looks, and would discard RURAL corridors hardest - they are the
  ones with no local government to do the filing, and they are what this product exists to find.

  Both count. OD 0.15, E 0.10, capped at the plan's 0.15. The reviewer should argue with those two numbers:
  the RATIO is the judgement, and I have no evidence for it beyond the reasoning above.

  **Snapping**, with the failure each choice prevents:
    60 m tolerance - byway centrelines are digitised coarser than OSM and a divided highway's carriageways
    are ~30 m apart, so it cannot be tight; at 100 m a frontage road collects the freeway's designation.
    30% minimum overlap - a cross street meeting a byway at a junction shares one node and would otherwise
    inherit the designation from a single point of contact.
    overlap by LENGTH not node count - OSM node density varies enormously, so by count a short curly section
    outvotes a long straight one and the answer depends on how the road was mapped.
    cos(latitude) in the distance - without it an east-west offset reads ~26% further than it is here and the
    tolerance silently becomes an ellipse.

  27 tests, seven mutations. Six failed immediately; removing cos(lat) did NOT, because my directional test
  used a round offset and rel=0.15 and passed either way. Offsets are now computed so the two distances are
  equal when the correction is applied, at rel=0.02.

  **What to attack:**
  - The E-versus-OD decision. It is the single judgement that moves the most data, and it is mine.
  - 60 m and 30%. Try a real frontage road and a real divided highway from the Bay Area extract rather than
    the synthetic lines in my tests; that is the only way to find out whether those numbers hold.
  - `match()` prefers higher overlap, then stronger status. Check that ordering cannot pick an eligible
    segment over a designated one that overlaps almost as much.
  - Nothing fetches the byways yet. The manifest has no entry, and `problems()` is written for a parsed set
    that does not exist. That is deliberate - the ORACLE the brief asks for (byway-flagged ways ranking above
    class- and region-matched non-byway ways) needs the corpus from T-0030 - but it means this task ships
    arithmetic and no data, and you should decide whether that is acceptable or whether the fetch belongs
    here.

- 2026-09-07T22:40Z REVIEW by agent/reviewer-33. VERDICT: FAIL, left in queue/review. Every check below was
  re-derived against real sources or real geometry, not taken on the owner's word - noted per item.

  **1. The Status field meaning - RE-DERIVED, and it is overstated.** Went to Caltrans's own scenic-highways
  FAQ (dot.ca.gov/programs/design/.../lap-liv-i-scenic-highways-faq2), the program page, and Streets &
  Highways Code S:263 (Justia), plus AARoads' State Scenic Highway System summary, rather than trusting the
  owner's paraphrase.

  `byways.py:15-16` claims Eligible is "assessed on the landscape itself." That overstates it. Eligibility is
  fundamentally a LEGISLATIVE act: a route becomes eligible when the Legislature adds it to S&H Code SS263.1-
  263.8 (state routes) via a bill, prompted by a city/county nomination that DOES cite the landscape criteria
  the comment names - but the gate is a bill passing, not a uniform Caltrans-administered scenic score applied
  consistently across all 273 segments. Per AARoads, only ~28% of eligible mileage ever becomes officially
  designated, and plenty of eligible mileage sits indefinitely not because it lacks merit but because no local
  government ever pursued a Corridor Protection Program - so E is closer to "on a nominated list, unrevisited
  for years or decades" than "recently assessed by the state." Conversely `byways.py:18-19` undersells OD:
  designation is NOT purely administrative paperwork layered on scenery already proven. Per the FAQ, the
  District/State Scenic Highway Coordinators review the CPP and "the Caltrans Director makes the final
  determination" and can decline - a real substantive gate, just one aimed at the CPP's adequacy, not a
  scenery re-score.

  Net: both E and OD counting is still defensible (nomination criteria are real, and E is not proof of LOW
  scenic quality), but the code's framing - "assessed on the landscape" for E, "administrative, not scenic"
  for the E/OD gap - overstates the rigor behind E and understates the rigor behind OD. `byways.py:1-28`
  should be corrected to say eligibility is a legislative listing prompted by a scenic nomination, not a
  scenic assessment in itself, before this ships as the record of what the data means.

  **2. The weight ratio.** The plan (`i-want-to-make-synthetic-twilight.md` line 87) gives ONE number: `(+0.15
  byway, capped)`. It does not split by Status - the two-tier E=0.10/OD=0.15 scheme (`byways.py:36-37`) is the
  owner's invention to reconcile the plan with a field the plan's author evidently didn't know existed. That's
  a legitimate thing to invent, but it means the split itself, not just the ratio, is undefended.

  Given (1): OD received two real gates (nomination + Director-level CPP review); E received only the first.
  I'd weight that asymmetry harder than 0.10:0.15 (a 2:3 ratio) - something like OD 0.15 / E 0.06 (a ~2.5:1
  ratio) reflects that E is a weaker, unrefreshed signal, while still keeping E above zero so rural corridors
  aren't dropped for lacking a filing government, which is the owner's correct instinct. I have no more hard
  evidence for 0.06 than the owner had for 0.10 - flagging that my number is also a guess, just a differently-
  reasoned one.

  Cap interaction (`byways.py:38`, `MAX_BONUS = 0.15`): since `DESIGNATED_BONUS == MAX_BONUS`, `min(MAX_BONUS,
  status_bonus(...))` at `byways.py:148` can never actually bind at current values - it's a no-op. If the
  plan's "capped" means "E's total (base + bonus) capped at 1.0" (the natural reading, since the six base E
  terms already sum to 1.00 per the plan), the cap is being applied to the wrong quantity: it caps the bonus
  term alone, not `E_base + bonus`. A way already scoring E_base=0.95 and also OD-designated would need
  `min(1.0, 0.95 + 0.15)` at the composition site in T-0029, and nothing here enforces that. Worth flagging
  now so T-0029 doesn't inherit a false sense that "capped" is already handled.

  **3. 60 m tolerance / 30% overlap against REAL geometry - re-derived, not trusted.** Built `services/etl/
  work/sfbay/sfbay.osm.pbf` via `python -m etl.extract --region sfbay` in WSL (scenic-etl docker image), then
  pulled real named ways with `osmium export -f geojsonseq` and ran the actual `byways.overlap_fraction` /
  `distance_to_line_m` against them (copied module into a scratch dir, not modified in the worktree).

  - Real divided highway, I-280 (Junipero Serra Freeway) near 37.5-37.6N: paired opposite-direction
    carriageways separated ~28-46 m. `overlap_fraction` at 60 m tolerance = 1.0. PASS - matches the design
    intent, the two carriageways correctly count as the same road.
  - Real cross street, Kings Mountain Road meeting Skyline Blvd (CA-35) at 37.42498,-122.31390 (an exact
    shared OSM node, confirmed by distance=0 between endpoints): `overlap_fraction` of the ~3 km Kings
    Mountain Road way against a 247-point Skyline polyline near the junction = 0.036, far under the 0.30
    threshold. PASS - correctly rejected.
  - Real frontage road, "Redwood Highway Frontage Road" (San Rafael/Marin, alongside US-101, tagged "Redwood
    Highway" ref `US 101` and, for one stretch, `US 101;CA 1`): measured actual point-to-line distances from
    337 real frontage-road points to the real highway polyline. Median distance 37.7 m, with the bulk of
    points between 20-45 m - NOT the ~100 m the owner's synthetic test assumed as the near-miss case.
    `overlap_fraction` at 60 m tolerance = 0.92, decisively over the 0.30 gate. This is exactly the failure
    the docstring at `byways.py:44-48` names ("at 100 m a frontage road collects the freeway's designation")
    - except the real-world setback is well under 60 m, not just under 100 m, so 60 m does not safely avoid
    it. One stretch of this exact highway carries the `CA 1` ref jointly with `US 101`, and CA-1 is itself an
    iconic officially-designated scenic corridor in Marin - meaning if Caltrans's line for that stretch is
    centreline-digitised the way state DOT scenic layers normally are (I did not have the real Caltrans
    polyline to test against, since it isn't fetched - see item 7), a real, separately-named local frontage
    road is a plausible candidate to silently inherit a real scenic designation. SEVERITY: HIGH. The owner's
    own two "prevents" bullets for 60 m/30% (`log 59-63` above) are half right (divided highway, cross
    street) and half not proven safe (frontage road) once tested against real setback distances instead of a
    synthetic 100 m offset.

  **4. `match()` ordering - constructed, and it is wrong relative to its own docstring.** `byways.py:127-128`
  states the design intent in prose: "a segment that runs along both an eligible and an officially designated
  corridor takes the designated one, because the stronger evidence is the one worth carrying." The code at
  `byways.py:138-139` does not implement that: `key = (frac, status_bonus(...))` sorts by overlap FIRST, status
  only as a tiebreaker on EXACT equal overlap.

  Constructed case: a way overlapping an OD-status byway line by 60% and a separate E-status byway line by
  70% (both well past the 30% gate). `match()` picks the E entry (higher frac wins) and the way scores 0.10,
  not 0.15 - even though it robustly (2x the minimum threshold) overlaps the designated corridor too. This
  contradicts the docstring's stated intent, which was written for the "runs along both" case generally, not
  only the exact-tie case.

  Worse: I mutated `match()` to sort by `(status_bonus, frac)` instead - status first, overlap only as a
  tiebreak, the OPPOSITE priority - and ran `python -m pytest -q tests/test_byways.py`: all 27 tests still
  passed. `test_the_stronger_designation_wins_a_tie` (`test_byways.py:111-114`) only exercises the case where
  both entries share the literal same geometry (`BYWAY`), so frac is identically equal for both - it cannot
  distinguish overlap-priority from status-priority ordering. There is currently zero test coverage of which
  of these two orderings the code implements, despite it being the exact tension the docstring calls out.
  SEVERITY: MEDIUM-HIGH (documented behavior does not match implemented behavior, and no test would catch a
  regression in either direction). What SHOULD win: status should be primary once BOTH entries clear the
  overlap gate (the docstring's own reasoning - "stronger evidence is worth carrying" - is right), with
  overlap only breaking a genuine near-tie in status-equal cases; the current ordering has it backwards.

  **5. `overlap_fraction` midpoint blind spot - constructed, and confirmed real geometry can trigger it.** A
  way with ONE segment (2 nodes) whose two endpoints sit 530 m on either side of a byway, but whose exact
  MIDPOINT lands on the byway, scores `overlap_fraction == 1.0` and earns the full 0.15 bonus
  (`byways.py:116-118`: the near/far test is applied only to each segment's midpoint, then the WHOLE segment's
  length is credited or not). This is not purely synthetic paranoia: I measured real inter-node segment
  lengths from the frontage-road/highway pull in item 3 (820 real segments) - median 14.5 m, but 12 segments
  (1.5%) exceed 200 m and 6 exceed 400 m, max 519 m. Long, sparsely-noded straight stretches (rural highways,
  bridges, tunnel approaches) genuinely occur in this extract, and any such segment that curves toward a
  byway at its midpoint while diverging at both ends would be silently counted as fully "near" for its entire
  length. SEVERITY: MEDIUM - requires a specific geometry (a long, sparse, non-parallel segment brushing past
  the byway), narrower than item 3's frontage-road case, but real and unguarded by any test (all 27 existing
  tests use ways with >=2 short segments; none exercise a single long chord).

  **6. Seven mutations - re-ran independently, six of my seven constructed mutations caught (matching the
  owner's "six of seven"), but my ONE surviving mutation is different from theirs.** The owner's residual
  (cos(lat) with a loose test) is now fixed - I mutated `point_to_segment_m` to drop `math.cos(lat0)` and
  `test_distance_is_not_directional` DID fail (552.7 vs 696.6, well outside rel=0.02): the tightened test
  genuinely discriminates now, confirmed. I then independently constructed 6 more mutations (drop length-
  weighting in favor of node-count in `overlap_fraction`; drop the `min_overlap` gate in `match()`; loosen
  `SNAP_TOLERANCE_M` 60->150; collapse `ELIGIBLE_BONUS` into `DESIGNATED_BONUS`; make unknown status default
  to `ELIGIBLE_BONUS` instead of 0; and the ordering-priority swap from item 4). Five of those six were caught
  immediately by the existing suite. The ordering-priority swap (item 4) was NOT caught by any of the 27
  tests - this is the same gap flagged in item 4, independently reconfirmed via mutation. All mutations were
  applied to `services/etl/etl/byways.py` and reverted with `git checkout`; `git diff --stat` confirms the
  file is unmodified.

  **7. The gap the owner declares - my judgement, since it was asked for plainly.** Confirmed independently:
  `grep -rl byways services/etl --include=*.py` returns only `byways.py` and its own test file - nothing in
  the codebase imports it. `inputs/manifest.yaml` has zero Caltrans/FHWA entries (both endpoints from the
  2026-09-07T14:20:00Z research are live and already characterized - schema, counts, licence posture - but
  neither was ever pinned or fetched). `problems()` (`byways.py:151-166`) operates on a `list[dict]` shape
  nothing in the tree ever constructs outside the tests.

  This is NOT acceptable as delivered, for reasons beyond the owner's own framing. `grep -rli
  "caltrans|fhwa|byway" queue/` (backlog + review) turns up ONLY this task file - I checked T-0029 (composite
  score + rank-order fixtures), T-0030 (corpus emission) and T-0031 (GraphHopper graph) explicitly and none of
  their briefs mention fetching Caltrans/FHWA data. The owner's claim that the oracle "needs the corpus from
  T-0030" is true for the FULL rank-order oracle (which needs T-0029's composite score, not even T-0030), but
  it does not follow that NOTHING should be fetched here: the fetch itself has no home anywhere else in the
  visible queue. Every sibling task in this exact stack (T-0024 california-osm.pbf, T-0025 vermont-osm.pbf +
  vermont-curvature.kmz, T-0026 the eight 3DEP tiles, T-0027 the two WorldCover tiles) fetched and pinned its
  own external data AND validated its arithmetic against real geometry or a real oracle within the same task -
  this is the established pattern for this exact pipeline, not an extra ask. T-0028's own title is "...
  (Caltrans + FHWA), snapped to OSM ways" - the overlay, not just the arithmetic behind it, is this task's
  charter. Shipping only the arithmetic, with the fetch responsibility unclaimed anywhere downstream, means if
  this is marked done the byway overlay may never get built at all, while the queue reads as if it has been.
  At minimum this task should: add the two manifest entries (endpoints and licence posture are already
  characterized in this file's own log), fetch and parse into the `list[dict]` shape `problems()` already
  expects, and validate `match()`/`overlap_fraction` against the REAL Caltrans/FHWA polylines snapped to real
  OSM ways (not necessarily the full T-0029 rank-order oracle, which genuinely can wait) - i.e. repeat item 3
  of this review against the actual byway lines rather than a motorway standing in for one.

  **Verification, exact output:**
  - `cd services/etl && python -m pytest tests/` -> `305 passed in 4.85s` (27 in test_byways.py, all green).
  - `cd services/api && npm ci --no-audit --no-fund` -> `added 85 packages in 12s` (fresh worktree, needed
    before ops/test).
  - `bash ops/test` -> `TESTS linux=355/76 ios=skipped failed=0 skipped=0` / `OK`, exit 0.
  - `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`, exit 0.
  - `bash ops/queue-check` -> `QUEUE OK (51 tasks)`, exit 0.

  All four mechanical checks pass. The FAIL is on substance: an inaccurate account of what the source data
  means (item 1), an unweighted design split with no evidence either way (item 2, not disqualifying alone),
  a real ordering bug with zero test coverage relative to its own documented intent (item 4), a real
  algorithmic soundness gap confirmed reachable by real OSM geometry (item 5), a tolerance whose safety
  against the frontage-road failure mode is NOT established by real geometry the way the divided-highway and
  cross-street cases are (item 3), and a data-fetch responsibility that currently belongs to no task in the
  queue (item 7).
