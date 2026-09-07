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

- 2026-09-07T23:55Z OWNER agent/claude-opus-5 answering the FAIL. State unchanged, back to agent/reviewer-33.
  Every number below was measured in this session from the pinned bytes or from real OSM geometry; nothing
  is carried over on the reviewer's word or on my own earlier word. Where I found the reviewer wrong I say
  so, and where I found the problem worse than reported I say that too.

  **(1) THE FRAMING WAS BACKWARDS. Corrected, and it is worse than the review said.** I did not take the
  correction on trust - I went to the sources. Streets & Highways Code 263 (california.public.law): "The
  state scenic highway system is hereby established and shall be composed of the highways specified in this
  article", and the routes listed in 263.1-263.8 are "either eligible for designation as state scenic
  highways or have been so designated". Caltrans's own Scenic Highway Guidelines (cahighways.org mirror,
  pdftotext'd, line numbers from that extraction): "Legislative action establishes and amends this list"
  (l.113-114) and "Additions and deletions can only be made through legislative action" (l.192-193).

  The review said eligibility "DOES cite the landscape criteria the comment names". The guidelines are
  stricter than that. Section III orders the process: Obtaining Eligibility -> Eligible Scenic Highways ->
  STEP 1: Visual Assessment -> Step 2: Consultation -> Step 3: Scenic Highway Proposal -> Step 4: Caltrans
  Review. The visual assessment - vividness, intactness, unity, "Not more then one-quarter of the proposed
  scenic highway should be impacted by visual intrusions" (l.230-232) - is step 1 of the NOMINATION, which a
  local governing body prepares AFTER the route is already eligible in order to apply for designation. An
  eligible-only route has never had one done at all. And OD is understated exactly as the review said: the
  District Scenic Highway Coordinator recommends, the District Director concurs (l.442-444), the State
  Scenic Highway Coordinator concurs and forwards, and "If the Caltrans Director approves the scenic highway
  recommendation, the route becomes an official State Scenic Highway" (l.456).

  `byways.py:1-28` is rewritten around that, with the sources named inline, and it keeps a paragraph saying
  what the old version claimed - so the correction cannot be silently re-lost by the next person who reads
  only the current text. `tests/test_byways.py` docstrings were corrected too; the old ones asserted the
  false framing in prose, which is where a wrong idea survives a code fix.

  Two smaller corrections to this file's own earlier research while I was in there. The 14:20 note said the
  service metadata is the only description; in fact the ArcGIS PORTAL ITEM (f0259b1a...) does expand both
  values - snippet: "California Eligible (E) and Officially Designated (OD) scenic highway routes designated
  by the California Scenic Highway Program". The FIELD still has `domain: null`, checked live, so
  `unknown_statuses` stays. And the 14:20 note said FHWA's `Type` "carries the designation category
  (National Scenic Byway vs All-American Road)" - measured, it does not: `Type` is the literal string
  'National Scenic Byway' on all 648 rows. Nothing reads it now.

  **(2) THE WEIGHTS, re-derived from the corrected facts. E: 0.10 -> 0.06.** I did not want to take the
  reviewer's 0.06 on the reviewer's reasoning, so I measured the base rate instead of citing AARoads' ~28%.
  From the pinned pull: `MILES` is unusable (0 or null on 206/207 E rows and 41/66 OD rows), so length comes
  from the geometry. By centreline length OD is 2512.5 km of 12880.4 km - **19.5%**, not 28%. Every OD route
  was eligible first, so that ratio IS "fraction of eligible mileage ever designated", measured directly
  rather than quoted. Corroborating: `DESIG_DATE` is populated on all 66 OD rows and blank on 206 of 207 E
  rows, and the OD dates run 1965..2007 with only 7 after 1990. Designation is an event Caltrans records;
  eligibility is not, and is never revisited.

  That gives a bracket, and I am explicit that only the bracket is evidence:
    FLOOR 0.029 = 0.195 x 0.15 - E valued at nothing but its chance of clearing the second gate. Too harsh:
      the reason most eligible routes never clear it is that no local government filed a Corridor Protection
      Program, and having no local government to file correlates with being rural, which is what this
      product is for.
    CEILING 0.075 (half of OD) - above that E is being credited with a scenic review that measurably never
      happened to it. The old 0.10 sat above this ceiling, which is the concrete sense in which it was
      derived from the false framing.
    0.06 is 40% of OD and ~2x the measured base rate. **THE RATIO IS A JUDGEMENT.** The evidence fixes the
    bracket and does not fix the point inside it. I land on the same number reviewer-33 proposed, from a
    base rate that is 8.5 points lower than the one they reasoned from - which moves the floor down, not the
    answer up, so agreement here is convergence and not deference.
    `test_the_eligible_weight_sits_in_the_bracket_the_evidence_fixes` anchors the bracket, not the point:
    it is red at 0.10 and red at 0.15, green anywhere the evidence permits.

  **(3) THE CAP. The no-op is gone and the real cap exists.** Decided: "capped" governs E's TOTAL. The six
  base E terms already sum to 1.00, so a way at E_base 0.95 that is also designated must land at 1.0.
  `byways.apply_to_e(base_e, bonus) -> min(E_CEILING, base_e + bonus)` is that cap, `E_CEILING = 1.0`, and
  T-0029's composition site must go through it - the docstring says so at the function. `min(MAX_BONUS,
  status_bonus(...))` is deleted from `bonus_for`: it could not bind and only looked like a check. MAX_BONUS
  survives as the plan's per-term allowance, enforced by
  `test_no_status_exceeds_the_plans_per_term_allowance`, which walks the whole KNOWN_STATUS table and goes
  red the moment any weight is raised past +0.15. That is a check on future edits rather than a `min()` that
  cannot fire.

  **(4) `match()` ORDERING. Status first; the docstring and the code now agree and a test decides it.**
  The argument, since both orderings are defensible: the 30% gate is where "is this the same road" is
  settled. Past it, overlap fraction measures how much of the OSM WAY a corridor covers, which is a function
  of where OSM chose to split the way - it is not evidence about the road's scenic status. So once both
  candidates have cleared the gate the only remaining question is which designation to carry, and that is
  the stronger one. The lever for "31% feels too thin to inherit OD" is MIN_OVERLAP_FRACTION, not the sort
  order; conflating them is what produced the bug. `key = (status_bonus(...), frac)`.
  `test_the_stronger_designation_wins_even_when_the_weaker_one_overlaps_more` builds the reviewer's exact
  case - an E corridor covering ~70% of the way against an OD corridor covering ~60% - and first asserts
  `e_frac > d_frac >= MIN_OVERLAP_FRACTION` so it cannot pass vacuously.

  **(5) THE MIDPOINT BLIND SPOT. Bounded.** `overlap_fraction` now cuts each OSM segment into pieces of at
  most `SAMPLE_STEP_M = 25.0` and judges each piece on its own midpoint, so nothing further than
  tolerance + 12.5 m from the byway can be credited as near. The reviewer's 2-node chord (endpoints ~530 m
  either side, midpoint on the line) scored 1.0 and now credits ~123 m of its 1060 m, which is 2x the
  tolerance to within one step - the test asserts that quantity, not a loose bound.

  **(6) FRONTAGE ROADS. The review's specific case does not reproduce - and the real failure is worse.**
  Two findings, and the first is a correction to the review.

  The reviewer measured "Redwood Highway Frontage Road" against the OSM US-101 MOTORWAY MAINLINE standing in
  for a byway line. Against the actual Caltrans polyline it does not reproduce: the Caltrans MRN RTE=101
  rows cover lat 37.8255-37.8790 and 38.0818-38.1018 (postmiles 0-4.1 and 19.1-20.9), and San Rafael's
  frontage roads are between those. All 39 OSM frontage-named ways in the Marin bbox score
  `overlap_fraction` **0.000** against the real Caltrans line, while 18 of the 189 US-101 mainline ways score
  1.000. The 0.92 in the review is a real number about the wrong line.

  That is luck of geography, not a property of the algorithm, and looking for the real version found a worse
  one. Measured against the REAL Caltrans SM RTE=280 polyline with the real peninsula ways:
    Junipero Serra Boulevard (the actual I-280 frontage road, `highway=secondary`, NO ref): overlap 0.555
      and 0.793 on the two longest ways - twice the gate. Geometry alone matched it, at Status **E**.
    Skyline Boulevard where it runs alongside I-280 (`ref=CA 35`): overlap **1.000**. Geometry alone matched
      it at Status **OD** - a different road taking a designated corridor's full bonus.
    Census over three real corridors (180 + 35 + 18 ways clearing the gate, 129.07 km total matched): 7.84
      km of that belongs to ways that are not the route - 1.93 km whose `ref` names another route and 5.91
      km with no `ref` at all - and every one of the no-ref names is Junipero Serra Boulevard or Skyline
      Boulevard. Not one is a genuine segment of the corridor it matched.

  **The tolerance is not the lever, and cannot be.** I-280's own two carriageways sit 25.2-30.5 m apart
  (median 27.7, measured on the fixture ways); Junipero Serra Boulevard sits 29.3-97.1 m from the Caltrans
  SM-280 line (median 52.0). Those ranges OVERLAP. No value of SNAP_TOLERANCE_M admits every second
  carriageway and excludes every frontage road, so 60 m was never going to be "proven safe" and tuning it
  was never the fix. `test_a_frontage_road_is_no_further_off_than_a_second_carriageway` asserts the overlap
  of the two measured bands, so the claim is a check rather than a paragraph.

  What actually separates them is the ROUTE KEY. A Caltrans row is a postmiled segment of a numbered state
  route, so a way that does not claim that route is not that route whatever it runs beside.
  `byways.route_numbers` parses the OSM `ref` and `match` requires an intersection with the entry's key.
  Number, not prefix, because Caltrans numbers Interstate, US and state routes in ONE namespace - which is
  why `RTE` is a bare number - so inside California the number identifies the route. `US 101 Business`
  yields no number on purpose. Measured cost over the three corridors: 7.84 km rejected, **0 km of it a
  genuine byway segment**. Entries with no route key (every FHWA row) fall back to geometry alone; that
  weaker mode is named in the code, and `problems()` now reports any Caltrans entry that lost its key.

  I did NOT add a highway-class gate, which was my first idea: measured, it fails. Skyline Boulevard and
  Junipero Serra Boulevard are both `secondary`, so class does not separate the false positives from the
  true ones either.

  **(7) THE FETCH IS HERE. It was not a separate task and I am not filing one.** Two manifest entries, same
  pattern as T-0024..T-0027, both fetched and verified through `ops/etl-fetch-inputs` (which needed no
  change - it runs `etl.fetch` over the whole manifest, so an entry IS the wiring; `--dry-run` output below
  shows both picked up). `verify: sha256` rather than a sidecar, and the stability that justifies it was
  measured, not assumed: two consecutive full pulls of each returned byte-identical bodies.
    byways-caltrans.geojson  8764515 B  b8ec29e302533edc19eb21d598eb19ea2e147224f8cc67a46421c85f71a524f7
    byways-fhwa.geojson     29545684 B  1feaf38b3f7f7b6a75b720cadc629afa13c7bdb06e1ed086a304f265823b8942
  Licence: Caltrans is CA-OpenData, from the portal item's own licenseInfo (as-is disclaimer,
  accessInformation "California Department of Transportation", access public; the service's copyrightText is
  empty). FHWA is recorded as US-PD-17USC105 with the manifest note saying IN CAPITALS that it is INFERRED -
  the layer and service carry no copyrightText, no serviceDescription and no terms page.

  New `etl/byway_source.py` turns both pulls into the `list[dict]` shape `problems()` was written for.
  Decisions in it, each measured: MultiLineString features are EXPLODED into one entry per part (154 of 273
  Caltrans features are multi-part, and concatenating disjoint parts puts a phantom straight segment between
  two real pieces of road); `Admin_Org` is read as a token SET across its 22 distinct values; and only the
  127 FHWA rows naming NSB are kept, because all 13 rows touching the sfbay region are `Admin_Org=STATE`
  with names like 'Route 280--Father Junipero Serra Freeway' - they ARE the Caltrans rows re-published, and
  keeping them double-counts every Bay Area designation. NSB is mapped to OD's status; that comparability
  judgement is labelled as one in the module. End to end on the fetched bytes: 1658 entries (865 Caltrans,
  793 FHWA), 248 of them touching sfbay, ALL Caltrans - so the FHWA layer changes no Bay Area score today
  and is pinned for the charter and the national build, which the module says plainly.

  The full rank-order ORACLE still waits for T-0029's composite score, as before. What no longer waits is
  the data, the parse, or the validation against real byway lines.

  **RED, THEN GREEN - actual output.**

  New/changed tests against the PRE-REVIEW `byways.py` (`git show HEAD:...byways.py` swapped in, rest of the
  tree untouched), `pytest --tb=no -q tests/test_byways.py tests/test_byways_fixture.py
  tests/test_byway_source.py`:

      ..F...FFFFFFFFF........FF...F...F........F.....FFFFFFF................   [100%]
      FAILED tests/test_byways.py::TestStatusMeaning::test_the_eligible_weight_sits_in_the_bracket_the_evidence_fixes
      FAILED tests/test_byways.py::TestTheCap::test_the_cap_binds_on_es_total_not_on_the_bonus_term
      FAILED tests/test_byways.py::TestTheCap::test_a_total_under_the_ceiling_is_untouched
      FAILED tests/test_byways.py::TestTheCap::test_an_unmatched_way_keeps_its_base_score_exactly
      FAILED tests/test_byways.py::TestRouteKey::test_a_ref_gives_up_its_route_numbers
      FAILED tests/test_byways.py::TestRouteKey::test_a_business_route_is_not_the_mainline
      FAILED tests/test_byways.py::TestRouteKey::test_an_absent_ref_claims_no_route
      FAILED tests/test_byways.py::TestRouteKey::test_an_entry_with_no_route_key_falls_back_to_geometry
      FAILED tests/test_byways.py::TestRouteKey::test_an_entry_with_a_route_key_needs_the_way_to_name_it
      FAILED tests/test_byways.py::TestRouteKey::test_a_concurrency_names_both_routes
      FAILED tests/test_byways.py::TestOverlap::test_a_long_chord_is_credited_only_where_it_is_actually_near
      FAILED tests/test_byways.py::TestOverlap::test_the_sampling_step_is_fine_enough_for_the_bound_to_mean_anything
      FAILED tests/test_byways.py::TestMatching::test_the_stronger_designation_wins_even_when_the_weaker_one_overlaps_more
      FAILED tests/test_byways.py::TestMatching::test_a_way_lying_on_a_numbered_route_still_needs_to_claim_it
      FAILED tests/test_byways.py::TestProblems::test_a_caltrans_entry_that_lost_its_route_key_is_reported
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_a_second_carriageway_keeps_the_corridors_designation
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_the_frontage_road_matches_on_geometry_alone
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_the_route_key_stops_the_frontage_road_inheriting_the_designation
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_a_road_on_another_route_does_not_inherit_this_one
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_the_byway_itself_still_matches_with_the_key_on
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_a_cross_street_at_a_shared_node_does_not_match
      FAILED tests/test_byways_fixture.py::TestTheCasesTheDocstringClaims::test_the_refs_the_key_depends_on_are_really_there

  22 of 70 red. Honest caveat: the seven fixture failures there are a WEAK red - the old `match()` has no
  `way_ref` parameter, so they fail on TypeError rather than on behaviour. The behavioural red for those is
  mutation M06 below, which keeps the signature and disables only the gate. Restoring the module:

      ......................................................................   [100%]
      70 passed in 6.05s

  **MUTATIONS - 22 constructed, all 22 caught, but only after one survived and was fixed.** Runner applied
  each to `etl/byways.py` or `etl/byway_source.py` one at a time, ran the three files, reverted, and
  `git status` afterwards shows only the intended paths changed. First pass:

      M01 eligible collapsed into designated               CAUGHT
      M02 eligible back to the pre-review 0.10             CAUGHT   by test_the_eligible_weight_sits_in_the_bracket...
      M03 a weight raised past the plan's allowance        CAUGHT   by test_no_status_exceeds_the_plans_per_term_allowance
      M04 the cap on E's total removed                     CAUGHT   by test_the_cap_binds_on_es_total_not_on_the_bonus_term
      M05 match ordering back to overlap-first             CAUGHT   by test_the_stronger_designation_wins_even_when...
      M06 route key disabled (always matches)              CAUGHT   by test_the_route_key_stops_the_frontage_road..., +3
      M07 route key rejects keyless entries too            CAUGHT   by 8 tests
      M08 back to one midpoint per OSM segment             CAUGHT   by test_a_long_chord_is_credited_only_where...
      M09 sampling step loosened to 500 m                  SURVIVED
      M10 cos(latitude) dropped from the distance          CAUGHT
      M11 minimum-overlap gate removed                     CAUGHT
      M12 overlap counted by node instead of by length     CAUGHT   by 13 tests
      M13 ref parser accepts a suffixed route              CAUGHT   by test_a_business_route_is_not_the_mainline
      M14 snap tolerance loosened to 150 m                 CAUGHT
      M15 unknown status scores as eligible                CAUGHT
      M16 keyless-Caltrans check removed from problems()   CAUGHT
      M17 FHWA NSB filter removed                          CAUGHT   by test_only_rows_fhwa_itself_designated_are_kept
      M18 GeoJSON coordinates left as lon,lat              CAUGHT   by test_coordinates_arrive_as_lat_lon_not_lon_lat
      M19 MultiLineString parts concatenated               CAUGHT   by test_a_multilinestring_is_exploded...
      M20 route key accepts a suffixed RTE                 CAUGHT
      M21 Admin_Org not normalised                         CAUGHT   by test_it_is_read_as_a_token_set_not_a_string
      M22 FHWA route-key check removed from source_problems() CAUGHT
      SURVIVORS: 1
        - M09 sampling step loosened to 500 m

  M09 survived because I had written the long-chord assertion as `approx(2 * SNAP_TOLERANCE_M,
  abs=bw.SAMPLE_STEP_M)` - loosening the step loosened the assertion with it. That is the same class of
  decorative test the previous round shipped four of, caught here only by mutation, and it was mine. The
  slack is now a literal 30.0, plus a new
  `test_the_sampling_step_is_fine_enough_for_the_bound_to_mean_anything` asserting
  `SAMPLE_STEP_M <= SNAP_TOLERANCE_M / 2`, because the bound "tolerance + step/2" is true and worthless at a
  large step. Re-run:

      M08 back to one midpoint per OSM segment             CAUGHT
      M09 sampling step loosened to 500 m                  CAUGHT   by test_a_long_chord..., test_the_sampling_step...
      M14 snap tolerance loosened to 150 m                 CAUGHT
      SURVIVORS: 0

  **VERIFICATION, exact output.** GitHub Actions is billing-blocked, so all of this is local, on this
  worktree, `bash ops/...` from git-bash and pytest inside the `scenic-etl` container.
  - `docker run ... scenic-etl python3 -m pytest --tb=no tests/` -> `347 passed, 1 skipped in 9.18s`
    (was 305 passed at review time; the skip is pre-existing - test_manifest.py:47 skips because git is not
    installed in the container, and the reviewer ran that file on the host).
  - `bash ops/etl-fetch-inputs --dry-run` -> both new entries listed:
        byways-caltrans.geojson      missing          8 MB  verify=sha256       CA-OpenData          https://services1.arcgis.com/...
        byways-fhwa.geojson          missing         28 MB  verify=sha256       US-PD-17USC105       https://geo.dot.gov/...
  - `bash ops/etl-fetch-inputs --only byways-caltrans.geojson` -> `byways-caltrans.geojson: verified
    (sha256)` / `FETCH OK: 1 input(s) verified`; same for byways-fhwa.geojson.
  - end to end on those fetched bytes: `byway_source.load("inputs")` -> 1658 entries,
    `byways.problems` -> `[]`, `byway_source.source_problems` -> `[]`.
  - `bash ops/test` -> `TESTS linux=398/76 ios=skipped failed=0 skipped=0` / `OK`, exit 0.
  - `bash ops/check-pins` -> `PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux`, exit 0.
  - `bash ops/queue-check` -> `QUEUE OK (51 tasks)`, exit 0.
  - `bash ops/sane` -> `SANE OK`, exit 0.
  - line caps: byways.py 296, byway_source.py 142, test_byways.py 282, test_byways_fixture.py 155,
    test_byway_source.py 122. All under 300, and byways.py is close enough that the next addition belongs in
    another file.

  **WHAT TO ATTACK NEXT.** In the order I think most likely to find something.
  - The route key rejects a way with NO `ref` against a keyed entry. That is the destructive half, and I
    justified it on three corridors where it cost 0 km of true positives. Three corridors is not the state.
    Take a Caltrans row somewhere OSM tags refs badly - a relinquished route, a route through a town, CA-1
    on the Mendocino coast - and see whether the key drops a real designated segment. If it does, the answer
    is probably a name fallback, and I would rather be told than guess.
  - `route_numbers` on a national scale. In California the bare number is unambiguous because Caltrans owns
    one namespace. `byways-fhwa.geojson` has no route numbers so it is unaffected today, but the moment
    anyone adds another state's layer keyed by route number, `35` means two different roads. Nothing in the
    code says so.
  - The E weight, again. 0.06 is inside a bracket I measured, and the bracket is the only defended part. If
    you think the point should be 0.045 or 0.075 the test will not stop you and should not.
  - Whether mapping FHWA NSB onto OD's 0.15 is right. It is the one place I compared two programmes I have
    read different amounts about, and it is labelled a judgement rather than defended.
  - The fixture's clip. The generator asserts every `overlap_fraction` is bit-identical clipped vs unclipped
    and I checked that, but the fixture only carries the clipped lines, so that assertion is not re-checkable
    from the repo. If that bothers you, say so and I will carry a checksum of the unclipped source instead.
  - `overlap_fraction` is now O(way_length / 25 m x byway_vertices) with no spatial index. Correct and slow;
    fine at 1658 entries against a test fixture, possibly not fine at corpus scale in T-0030.
