---
id: T-0028
title: Scenic score: designated byway overlay (Caltrans + FHWA), snapped to OSM ways
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/]
pins_affected: []
reviewer: null
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

