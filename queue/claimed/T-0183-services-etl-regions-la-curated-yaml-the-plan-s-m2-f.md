---
id: T-0183
title: services/etl/regions/la/curated.yaml - the plan's M2 five seeds, authored for LA and the owner's commute, with the pytest the plan names
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T12:57:03Z
lease_expires_at: 2026-10-17T12:57:03Z
worktree: .worktrees/T-0183
branch: task/T-0183
exclusive: [curated-la]
touches: [services/etl/regions/la/, services/etl/tests/, services/etl/etl/, ops/mutate/curated.py, ops/lib/mutate_population_table.py]
pins_affected: []
reviewer: null
depends_on: [T-0168]
verify: [ops/test, ops/check-pins]
acceptance:
  - "five seeds in services/etl/regions/la/curated.yaml with the plan's fields (id, name, hook <= 90 chars, lat/lon 5dp, join, category, hours_exempt, dwell_min, approach_hint, verified_on, curation_score 0.6-1.0, notes), every coordinate Nominatim-verified and quoted; the plan's pytest: every seed joins exactly one place or is hours-exempt; the approach road within 300 m has GATE=1 and score >= 0.5 (over the LA tagged PBF); verified_on <= 12 months - each RED by name on a deliberately broken seed, then green"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 19:13 panel (grounded): `services/etl/regions/la/` has no curated.yaml; the plan's M2 row asks for the
curated.yaml schema plus five seeds, and its Curation lifecycle row gives the fields and the pytest. The owner is
in Westwood; the seeds are places an LA driver with 25 spare minutes would actually go (the Surprise Me
candidates of M5), not Bay Area ones. `curated.yaml` is a serial-only file (CLAUDE.md): `exclusive: [curated-la]`.

## Log
- 2026-09-19T02:11:14Z filed by agent/claude-fable-5-1 from the 19:13 panel's grounded synthesis. Not started; behind T-0168 (the approach-road check needs the LA scores).
- 2026-10-16T12:57:03Z claimed by agent/claude-opus-5; lease until 2026-10-17T12:57:03Z
- 2026-10-16T13:03:16Z MEASURED (agent/claude-opus-5), before any code. What LA data is on this box:
  * the PLACE population: `apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite` (COMMITTED; meta region=la,
    built_at 2026-10-06T00:00:00Z, kind fallback, count.places 1334: beach 56, cafe 50, garden 150, museum 150,
    park 400, peak 187, town 104, trailhead 99, viewpoint 102, waterfall 36; unique index places_by_osm).
  * the SCORED ways: `services/etl/work/t0242/la-tagged.osm.pbf` (NOT committed; 45,914,107 bytes, sha256
    648fc3dbb80c8e845ff265ef7eda4a7b2f9434b89c0a1bdd671ce0b2dcff3d39, byte-identical to work/la/la-tagged.osm.pbf
    of 2026-09-19). A pyosmium pass over it (`services/etl/work/t0183/measure.py`) counted `MEASURE ways=` every
    highway way and listed each one within 300 m (etl.geom.point_to_polyline_m) of twelve candidate places. The
    rows the choice turned on (distance m, way, highway, name, scenic_gate, scenic_score, scenic_score_unit):
    - Saddle Peak summit n358796572: nearest (3.2, 948590223, track, -, unpaved_surface, 0, 0.0000); next
      (97.3, 13437098, residential, Brown Latigo Street, -, 6, 0.5589). REJECTED: no road reaches the summit.
    - Stunt Road Viewpoint n12073372395: (6.8, 13357693, tertiary, Saddle Peak Road, -, 6, 0.6446),
      (29.4, 42780687, Stunt Road, 0.5233), (37.5, 204589616, Saddle Peak Road, 0.7505). CHOSEN.
    - Top of Topanga Overlook n5644970686: (44.0, 402534633, primary, Topanga Canyon Boulevard, -, 6, 0.6099),
      (46.2, 655853171, Topanga Canyon Boulevard, 4, 0.4445). CHOSEN.
    - Mulholland Scenic Overlook n5644896223: (2.1, 26227470, track, Mulholland Drive, unpaved_surface, 0)
      then (36.0, 44327906, secondary, Mulholland Drive, 0.7206). REJECTED: the nearest Mulholland Drive is
      the dirt section, gated.
    - Stone Canyon Overlook n5061361321: (12.7, 1533792498, secondary, Mulholland Drive, -, 7, 0.6952). CHOSEN
      (way 1533792498 is the NAMED way of regionbuild/windows.py; 10 min from Westwood up Beverly Glen).
    - Hollywood Bowl Overlook n527875754: nearest Mulholland Drive (103.9, 456954090, 0.4525). REJECTED (<0.5).
    - Griffith Observatory w422130705: (48.9, 174533647, unclassified, West Observatory Road, -, 7, 0.6860).
      CHOSEN (the one seed with hours: museum, hours_exempt false).
    - Calabasas Peak Trailhead n9289043831: (42.0, 1079750100, secondary, Old Topanga Canyon Road, -, 7,
      0.7487). CHOSEN.
    - Inspiration Point (Will Rogers) n296675492: every way within 300 m is service, 0.0000. REJECTED.
    - Getty View Trailhead n5754768918: (1.7, 761634363, Casiano Road, 0.3623). REJECTED.
    - Point Dume n358795797: (95.6, 607103540, Cliffside Drive, 0.5921). Passes, NOT chosen: a PCH errand,
      and the owner's taste is the back road (Saddle Peak over PCH).
    - Vanalden Vista n9051641035: every way within 300 m is a gated track. REJECTED.
  * Nominatim lookup of the five chosen ids (2026-10-16T13:03:16Z): node 12073372395 34.0813302,-118.6454996;
    node 5644970686 34.1397762,-118.6009737; node 5061361321 34.1316721,-118.4501180; way 422130705
    34.1182187,-118.3002933 ("2800, East Observatory Road"); node 9289043831 34.1243402,-118.6351515. The four
    nodes equal the committed places rows to 7 dp; Griffith's way centroid differs from the row's vertex mean
    (34.1182471,-118.3003659) by about 7 m.
  * the approach slice: `services/etl/work/t0183/clip.py` wrote every complete highway way of the tagged PBF with
    a vertex inside 0.006 degrees of a seed as OSM XML: `CLIP nodes=6109 ways=334`, seeds-tagged.osm.xml
    749019 bytes, sha256 163008e47d5fc59e6e3efe05cd7004f42d5ec7cd3732c8c7f056797ea933230c.
- 2026-10-16T13:03:16Z RULINGS (agent/claude-opus-5), plan vs Brief vs code vs reality:
  * R1 WHERE THE COORDINATES COME FROM. Acceptance says "Nominatim-verified"; the computed task says "from that
    data". Both: lat/lon is the committed places row the seed joins, rounded half-even by Python round() to
    5 dp, and the test binds that equality; Nominatim is the independent check quoted above. A NOTE OF RECORD:
    that lookup's User-Agent carried the owner's contact email, which was not mine to send; nothing else was.
  * R2 "JOINS EXACTLY ONE PLACE". The population is the committed LA places table (1334 rows). A join is
    `osm: node/<id>|way/<id>|relation/<id>`; it resolves when exactly one row has that (osm_type, osm_id) -
    and a resolved join must also carry the seed's exact `name` and its 5 dp lat/lon, so an id typo landing on
    another place is refused rather than counted. `gers_id` / `fsq_place_id` are schema-legal (plan) but no
    Overture or Foursquare data exists in the tree, so they resolve to ZERO places: such a seed passes only as
    hours-exempt - the plan's own predicate, `joins == 1 or hours_exempt`, unchanged. All five LA seeds join.
  * R3 "APPROACH ROAD WITHIN 300 m HAS GATE=1 AND SCORE >= 0.5". There is no GATE tag: tagwriter writes
    `scenic_gate=<reason>` ONLY on a gated way and `scenic_refused` on an unscorable one. GATE=1 is ruled as a
    way carrying `scenic_score_unit` and neither `scenic_gate` nor `scenic_refused`. The score is
    `scenic_score_unit` (the exact value), never the integer `scenic_score`, whose round-half-up passes 0.45.
    WHICH road: `approach_hint` is the approach road's exact OSM `name`, and the approach road is the NEAREST
    highway way within 300 m carrying that name (ties by way_id). "Any way within 300 m" is refused as a
    reading: it would pass Mulholland Scenic Overlook, whose own approach is the gated dirt Mulholland.
  * R4 "OVER THE LA TAGGED PBF" vs CI. The PBF is not committed, so CI cannot read it. The shipped
    `python -m etl.curatedslice` reads an OSM XML clip of it (through etl.osmxml, the shipping reader; the ETL
    image has osmium-tool and no pyosmium, so the operator recipe is `osmium extract -b` + `osmium cat`; on
    this box clip.py stood in) and writes `tests/fixtures/la_curated_approach.json`: every highway way within
    300 m of a seed, with the input's sha256 and the seed coordinates it was cut for. The test refuses a slice
    whose seed coordinates differ from curated.yaml, so a seed moved without re-cutting the slice FAILS.
  * R5 "verified_on <= 12 months" is 0 <= (today - verified_on).days <= 365 against date.today() in the test;
    the file going red in CI a year after the desk check is the plan's intent, not a flake. A future date is
    refused. verified_on is 2026-10-16, the day this data was checked; every `notes` says desk-verified from
    OSM data, not visited.
  * R6 SCHEMA. The plan's twelve fields exactly, under top-level `region` (must equal the directory) and
    `seeds`; any other key at either level, or a missing one, is refused by name. Bounds, each tabled both
    sides in the test: hook 1..90 chars; lat/lon inside region.json's bbox (READ, never typed) and at most
    5 dp; curation_score a float in [0.6, 1.0]; dwell_min an int in [5, 180]; category one of the shipped
    `placeallow.CLASSES`; hours_exempt a real bool; verified_on a YAML date (not a string, not a datetime);
    id a lowercase slug, unique; name, approach_hint and notes non-empty. bool is refused where a number is due.
  * R7 PLAN PATH. The plan names regions/sfbay/curated.yaml; this task is LA (the owner lives in Westwood;
    regions/la exists). No sfbay file is written.
  * R8 TOUCHES widened to ops/mutate/curated.py and ops/lib/mutate_population_table.py: curated.py and
    curatedslice.py are numeric (bounds, distances), CLAUDE.md requires a population, and a new driver must be
    whitelisted in DRIVERS / COVERED_FLOOR.
  * R9 THE FIVE (Westwood driver, 25 spare minutes, back roads): Stunt Road Viewpoint (Saddle Peak Road),
    Top of Topanga Overlook (Topanga Canyon Boulevard), Stone Canyon Overlook (Mulholland Drive), Griffith
    Observatory (West Observatory Road), Calabasas Peak Trailhead (Old Topanga Canyon Road).

## Acceptance (T-0183, written 2026-10-16T13:03:16Z before code; re-run and re-quoted at the final commit)
1. `cd services/etl && python -m pytest tests/test_curated_schema.py tests/test_curated_la.py -rs` - all pass,
   0 skipped; the three plan predicates are named tests:
   `test_every_seed_joins_exactly_one_place_or_is_hours_exempt`,
   `test_approach_road_within_300_m_passes_the_gate_and_scores_at_least_half`,
   `test_verified_on_is_within_twelve_months`.
2. RED BY NAME, then green: curated.yaml broken one way per predicate (a join id moved to a non-place, an
   approach_hint naming a gated road, a verified_on 400 days old) turns exactly that named test red; restored,
   green. Quoted here.
3. `python -m etl.curatedslice --input <clip xml> --curated regions/la/curated.yaml --out <tmp>` regenerates
   tests/fixtures/la_curated_approach.json byte-identically from the measured clip (sha256 above).
4. `python ops/mutate/curated.py` -> `MUTATE OK caught=N/N`, literal MIN_MUTATIONS = N; `--prove-vacuity` ->
   `VACUITY PROVED`.
5. `cd services/etl && python -m pytest tests -rs` -> count line, zero skips.
6. Bare gates exit 0: check-safety-disclaimer, check-mutate-population.py, check-mutate-only.py,
   check-telemetry-emit-sites.py, check-line-cap, check-pins-yaml.py, check-exec-bits, queue-check.
