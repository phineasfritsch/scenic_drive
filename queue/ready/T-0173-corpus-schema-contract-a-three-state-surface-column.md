---
id: T-0173
title: corpus schema contract - a three-state surface column, TERM_NAMES pinned to score.score, and one schema_version across corpus, Worker and PlaceStore
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [services/etl/etl/schema.py, services/etl/etl/corpuswriter.py, services/etl/tests/, services/api/src/index.ts, services/api/test/, pins/PINS.yaml]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: [T-0030]
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/etl/etl/schema.py: `paved INTEGER NOT NULL CHECK (paved IN (0,1))` becomes a three-state `surface` column (-1 no surface tag, 0 unpaved, 1 paved) with the DDL hash and SCHEMA_VERSION bumped together; RED by name first: a fixture way with no surface tag round-trips through the corpus as 'unknown', not 'paved'"
  - "a test asserting every TERM_NAMES value except `byway` is a parameter of score.score (inspect.signature - the pin test_way_record.py already uses on score_kwargs), red today on `elev_gain`, green after the rename; the five score terms with no producer (speed_fit, sinuosity, points_of_interest, water, furniture) listed as RESERVED with their producer task"
  - "pins/PINS.yaml pins P-PROD-05 on Linux: corpus SCHEMA_VERSION == services/api/src/index.ts SCHEMA_VERSION (routes.test.ts pins it on the wire), red today (1 vs 0), green after they agree; PlaceStore.schemaVersion joins the assertion when T-0175 lands"
---
## Brief

From the 2026-09-18 16:13 panel (CODE lens, grounded). PR #100 (T-0030) landed the corpus emitter's first
slice with SCHEMA_VERSION 1; schema.py's own rule 1 says any DDL change after a corpus ships to a device
invalidates every device's copy. No device reader exists yet (Sources/ holds Handoff and ScenicKit only), so
the three contract defects below are one file now and an OTA-invalidating bump later - which is why they are
their own slice, filed the hour #100 merged, not a third review round on a PASSed PR.

1. `osm_features.paved INTEGER NOT NULL CHECK (paved IN (0,1))` erases the UNSURVEYED state. score.py's
   `raises_surface_unknown_flag` is `surface is None and highway in UNSURVEYED_CLASSES` and multiplies by
   UNSURVEYED_MULTIPLIER; CLAUDE.md's hard gate is "unpaved (positive evidence)"; the plan's hazard strip shows
   `surface_unknown`. A two-valued column cannot reproduce the score or honour the gate on the device.
2. `TERM_NAMES` (six ids; `elev_gain`; `byway`) does not spell score.score's ten ranked parameters, and
   schema.py rule 6 says the score is recomputed from terms_* at query time - so TERM_NAMES IS the on-device
   score contract. Nothing pins it to the signature.
3. Three schema_versions and no anchor: corpus schema.py SCHEMA_VERSION=1, Worker index.ts SCHEMA_VERSION=0
   (pinned on the wire by routes.test.ts), PlaceStore absent. P-PROD-05 in the plan is exactly this pin.

The author rule applies (CLAUDE.md, Verification). PR base is main. terms_osm / terms_raster stay physically
separate (ODbL posture) - this task changes columns and pins, not the layering.

## Log
- 2026-09-18T23:04:01Z filed by agent/claude-fable-5-1 from the 16:13 panel's grounded synthesis; ready/ with its acceptance block. Not started.
