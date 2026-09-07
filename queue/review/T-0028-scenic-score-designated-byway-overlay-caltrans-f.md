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
