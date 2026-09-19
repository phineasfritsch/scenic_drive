---
id: T-0217
title: etl - the waydoc -> ExtractWay adapter: corpus.build has no committed path from a real extract (three shapes, no converter), so nothing in CI has ever fed it real ways
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T17:00:29Z
lease_expires_at: 2026-09-19T23:00:29Z
worktree: .worktrees/T-0217
branch: task/T-0217
exclusive: []
touches: [services/etl/etl/, services/etl/tests/, ops/mutate/, ops/lib/]
pins_affected: []
reviewer: null
depends_on: [T-0206]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURED in T-0206's Log: corpus.build -> extractway.load_extract reads {region, ways:[{id, cls, highway, access_ok, oneway, nodes, name?, surface?}]}; the real window doc is waydoc.py's {way_id, tags, coords}; window-scored.json is a third shape; grep access_ok hits only consumers. SHIP one module that derives cls from tagfilter.WAY_CLASSES, surface from surface.surface_state, oneway from the tags, and access_ok = 0 iff tags.get('access') in assemble.CLOSED_ACCESS or tags.get(assemble.MOTOR_VEHICLE_KEY) == assemble.MOTOR_VEHICLE_REFUSED - the two access rules of assemble.gate_reason (assemble.py:146-150) factored into ONE importable predicate that gate_reason itself calls, evaluated independently of the surface and track rules (no second copy). NOT access_ok == (gate_reason(tags) != GATE_NO_ACCESS): gate_reason returns the FIRST firing rule, so a private unpaved road answers GATE_UNPAVED_SURFACE and would read access_ok=1; the committed slice carries exactly such a way (access=private + surface=dirt) asserted access_ok=0 AND surface=unpaved, with a test bound to the shipping entry point over a committed slice of REAL ways (from the canyon window; licence line ODbL) covering access=private, motor_vehicle=no, oneway=-1, oneway=yes, a roundabout, a way with no name, a class outside the table (T-0206's throwaway skipped 2 of 23,474 - name them)"
  - "its ops/mutate population with a literal floor (it is a new numeric-adjacent module under services/etl/etl/ - or an allowlist entry with a reason if ruled non-numeric), python ops/lib/check-mutate-population.py bare; the ETL suite count line; the canyon window built end to end from the committed adapter with ways/segments/bytes equal to T-0206's 11,740 / 24,205 / 6,135,808 or the difference explained row by row"
---
## Brief

T-0206's R1: 'the waydoc->ExtractWay adapter is NOT this task's shipping work' - its measurement adapter lives in the
gitignored work/ dir of a worktree that will be removed. A class/access/oneway decision over real tags is a safety-
adjacent table (access_ok feeds the corpus the hazard strip reads), so it ships with a population, not as a script.
The throwaway is preserved at services/etl/work/t0206/ in the main checkout for reference only.

## Log
- 2026-09-19T13:12:06Z filed by agent/claude-fable-5-1 (orchestrator, from T-0206's measurement on PR #120). Not started.
- 2026-09-19T16:40:26Z acceptance line 1 corrected by agent/claude-fable-5-1 (06:13 panel, CODE lens, fable-grounded on assemble.py:141-150 / schema.py): the panel's first predicate (access_ok == gate_reason != GATE_NO_ACCESS) would grant access to a private unpaved road because gate_reason returns the first firing rule; the corrected line factors the two access rules into one importable predicate and pins the private+dirt row.
- 2026-09-19T17:00:29Z PROMOTED to ready/ by agent/claude-fable-5-1 (orchestrator): T-0206 is in done/ (#120); disjoint from T-0208 except the DRIVERS table in ops/lib/check-mutate-population.py - the final pre-review merge of main resolves it.
- 2026-09-19T17:00:29Z claimed by agent/claude-opus-5; lease until 2026-09-19T23:00:29Z
- 2026-09-19T17:07:57Z RULED by agent/claude-opus-5 (owner), before any code. Every measurement below was taken
  in the MAIN checkout, read-only, and is quoted with the command that produced it.

  R0 THE DISAGREEMENTS BETWEEN THE ACCEPTANCE, extractway.py AND THE DATA, ruled first.
  (a) "surface from surface.surface_state (three states)" vs `extractway.py`. The extract's `surface` key is
      the RAW OSM tag by that reader's own contract, and `RETIRED_WAY_KEYS = ("paved",)` REFUSES a
      pre-derived surface column by name; `ExtractWay.surface_state` IS `surface.surface_state`, and
      `corpuswriter.write_features` writes `w.surface_state` into the corpus. An adapter that emitted the
      three-state integer would be refused by the reader AND would be a second copy of the rule. RULED: the
      adapter copies the raw tag, and CALLS `surface.surface_state` only to COUNT the three states on its
      own count line - so the number is measured rather than claimed - and the committed slice asserts
      state 0 (UNPAVED) on the private dirt way THROUGH `ExtractWay.surface_state`.
  (b) "a class outside the table (from the canyon window)". There is no such way in the window. Measured:
      `python services/etl/work/t0217/scan.py` - the window's 11,740 ways carry 15 distinct `highway`
      values (service 6818, residential 2562, track 988, tertiary 406, secondary 277, trunk 251, primary
      181, unclassified 94, motorway_link 73, motorway 48, trunk_link 14, primary_link 10, tertiary_link 8,
      secondary_link 6, living_street 4) and every one of them is in `tagfilter.WAY_CLASSES`; T-0206's own
      line says the same thing - `ADAPT in=11740 out=11740 skipped_class=0`. RULED: the two out-of-table
      rows come from `services/etl/work/la-grid/grid-b-doc.json` (R5), the same region and the same
      `waydoc.build` producer, and the fixture names each way's source document in a header field.
  (c) a repeated `way_id`. T-0206's throwaway dropped a repeat in silence (`if way_id in seen: continue`).
      RULED: this adapter REFUSES the document by name - `load_extract` refuses duplicates anyway, and a
      silent drop moves every other way's rank. Measured: the window has 0 duplicate ids and 0 rows under
      2 coordinates, so the refusal costs the shipping path nothing.

  R1 THE MODULE AND THE ENTRY POINT. `services/etl/etl/extractadapter.py`, reached by
  `python -m etl.extractadapter --input <waydoc.json> --out <extract.json> [--region la]`. Its `main` is
  what production runs and what the defect-named tests bind to (CLAUDE.md: a test binds to the shipping
  symbol). NOT `--waydoc` on `python -m etl.corpus`: `corpus.build`'s contract is one extract in, a
  byte-identical corpus out (P-DATA-01, and its docstring promises exactly one input shape), a converter
  inside it would be a second shape nothing else could diff, and the intermediate extract is precisely the
  artifact T-0206 had to keep by hand. The committed path is two commands; the second one does not move.

  R2 THE MAPPING TABLE, field by field and value by value.
    cls       `HIGHWAY_TO_CLS`, inverted from `tagfilter.WAY_CLASSES` at import - never a second literal
              list, so a class added there is adapted without editing this module.
    highway   the raw tag.
    name      `tags["name"]` when it is a non-empty str, absent otherwise (7,623 of the window's 11,740
              ways carry no name; `extractway` makes the key optional).
    surface   the raw tag when it is a non-empty str, absent otherwise. R0(a).
    oneway    `yes|true|1` -> 1; `-1|reverse` -> -1; `no|false|0` -> 0, each of them FINAL. Any other value
              and an absent tag fall through to the implication: `junction=roundabout` -> 1, because OSM's
              roundabout is one-way and the device router reads this column (6 of the window's 15
              roundabouts carry no `oneway` tag at all, e.g. way 338438553); `junction=circular` -> 0,
              because a circular junction carries no such implication (the window's 2, e.g. 1025983659
              Seaver Drive); otherwise 0. So `oneway=roundabout` - a value the key does not define, and
              absent from all three LA documents (window/grid-a/grid-b `oneway` tallies: yes/no/-1/absent
              only) - is 1 on a roundabout and 0 elsewhere, and `reversible`/`alternating` are 0: a corpus
              with no time dimension must not claim a direction.
    access_ok 0 iff `accessrule.access_refused(tags)`, else 1. ONE definition (R3).
    nodes     the row's `coords`, `[lat, lon]` pairs, in order; `geom.canonical` is `extractway`'s job.

  R3 WHERE THE ACCESS PREDICATE LIVES, AND WHY assemble.py GETS SHORTER RATHER THAN LONGER. The acceptance
  wants the two access rules of `assemble.gate_reason` factored into ONE importable predicate that
  `gate_reason` itself calls. Measured line budget: main's `assemble.py` is 293 lines against the 300-line
  cap, and T-0208's branch already has it at 299 (`wc -l .worktrees/T-0208/services/etl/etl/assemble.py`
  at a4fac76, clean tree). Adding a predicate there (+4 at best) refuses the MERGED head at
  `ops/lib/check-line-cap` - exactly the failure the "merge origin/main first" clause exists to catch. So
  the rule moves OUT: `services/etl/etl/accessrule.py` owns `CLOSED_ACCESS`, `MOTOR_VEHICLE_KEY`,
  `MOTOR_VEHICLE_REFUSED` and `access_refused`; `assemble.py` imports and re-exports all four, so
  `assemble.CLOSED_ACCESS` still IS the set `test_assemble.py:247` pins against `Gates.swift`'s
  `closedAccess` by identity, and `gate_reason` spells neither rule any more. assemble.py gets SHORTER, so
  the merge with T-0208 lands under the cap instead of over it. `test_assemble_wiring.py` counts refusal
  branches in `Gates.swift`, not in `assemble.py`, so the shape of `gate_reason` is free to change; its
  three `gate_reason(...)` assertions and `PORTED_GATE_KEYS` are behaviour and must stay green untouched.
  NOT `access_ok == (gate_reason(tags) != GATE_NO_ACCESS)`: `gate_reason` returns the FIRST firing rule, so
  the slice's private dirt road (way 1206170836, `access=private` + `surface=dirt`) answers
  `unpaved_surface` and would read access_ok=1 - the defect the 06:13 panel corrected.

  R4 THE COMMITTED SLICE. `services/etl/tests/fixtures/canyon_adapter_slice.json`, real ways, `way_id`,
  `tags` and `coords` VERBATIM from the source documents; the producer outputs the adapter never reads
  (furniture_nodes, landcover_codes, elevation_profile, sinuosity, tunnel_meters,
  meters_to_nearest_motorway) are dropped and NAMED in the document's own `dropped_keys` field, so a slice
  is a slice and not 43 MB. Licence in the header field `licence` (ODbL 1.0, (c) OpenStreetMap
  contributors) - a field, not a comment. The rows and what each one pins:
    1206170836 access=private + surface=dirt, service  -> access_ok=0 AND surface state UNPAVED (R3's defect)
    10724329   access=private + highway=track          -> access_ok=0 although `track` fires first
    1331140342 motor_vehicle=no, asphalt, named        -> the second access rule, alone, ungated otherwise
    1288190701 oneway=-1 (Zuma Access Road)            -> the reverse direction survives
    13465412   oneway=yes, access=yes                  -> access=yes is not a refusal
    1514080016 junction=roundabout + oneway=yes        -> the explicit tag and the implication agree
    338438553  junction=roundabout, NO oneway, private -> the implication alone, and a way with no name
    1025983659 junction=circular (Seaver Drive)        -> circular implies nothing: oneway=0
    179078676  highway=track, no name, no surface      -> track is kept, not excluded; access_ok=1
    299078436  motorway_link, no name                  -> a motorway is kept and never refused
    640857250  access=destination                      -> refused (CLOSED_ACCESS), where the throwaway allowed
    42798087   access=customers                        -> ALLOWED, where the throwaway refused
    221164479  motor_vehicle=private                   -> allowed: the key refuses on `no` only
    799554704  access=permit                           -> refused
    426254440  access=no                               -> refused
    1211805282, 1211805283 (grid-b)                    -> highway=footway: skipped by count (R5)
  plus one `oneway=no` row, the smallest in the window, named in the fixture and in the test.

  R5 THE TWO WAYS T-0206 SKIPPED, NAMED. `ADAPT in=23474 out=23472 skipped_class=2 skipped_short=0` is
  T-0206's line for `la-grid/grid-b-doc.json`. The two are way 1211805282 and way 1211805283, both
  `highway=footway`, both `name=Universal CityWalk Hollywood` (tourism=attraction, wikidata Q120648521,
  access=permissive, motor_vehicle=no). They reach a waydoc because the osmium keep-pass keeps
  `nw/tourism=attraction` (`tagfilter.POI_CLASSES`) and `waydoc.build` counts anything carrying a `highway`
  tag as a road; `footway` is in no `WAY_CLASSES` entry, so the corpus reader would refuse them by name.
  The adapter SKIPS them by count and makes no access decision about either - and both carry
  `motor_vehicle=no`, so a skip that went silent would look exactly like two correctly refused roads.

  R6 THE POPULATION. `ops/mutate/extractadapter.py`, the `ops/mutate/surfacecoverage.py` contract
  identically (HEAD-guarded subjects, SKIP-on-stale-anchor, a catch needs a NAMED test, MIN_MUTATIONS as
  the literal floor, EQUIVALENT with a witness, `--prove-vacuity`, __pycache__ purge + 1.1 s settle).
  `SUBJECT_MODULES = ("services/etl/etl/extractadapter.py", "services/etl/etl/accessrule.py")`, registered
  in `DRIVERS` and `COVERED_FLOOR` in `ops/lib/check-mutate-population.py` (the one line T-0208 also
  touches; the final merge keeps both). Mutations by name: the access predicate widened (CLOSED_ACCESS to
  every refusing value, the throwaway's own list), narrowed (destination dropped), `motor_vehicle` widened
  to CLOSED_ACCESS and narrowed to nothing; the rule ORDER - access folded into the surface/track answer
  via gate_reason, which is the corrected panel's defect; oneway -1 dropped; the roundabout implication
  removed and its opposite (circular implying oneway); the class skip made silent (count zeroed, skip
  turned into a refusal-free pass-through); the name/surface pass-through dropped.

  R7 THE END-TO-END NUMBER AND THE DIFFERENCE FROM THE THROWAWAY, PREDICTED BEFORE THE RUN. The canyon
  window through the committed path must land on T-0206's `ways=11740 segments=24205` and `bytes=6135808`.
  No row is added or dropped (skipped_class=0, skipped_short=0, 0 duplicate ids - measured above), and the
  segmenter reads only coords, so ways and segments cannot move. Two COLUMNS do move, and both are
  deliberate corrections of the throwaway:
    access_ok  162 of 11,740 ways. The throwaway used one list {no, private, customers, delivery, permit,
               military} for BOTH keys; this adapter uses Gates' own `CLOSED_ACCESS` {private, no, permit,
               destination} for `access` and `motor_vehicle == "no"` only. Row by row:
               access=customers 85 ways 0 -> 1; motor_vehicle=private (not otherwise closed) 54 ways
               0 -> 1; access=destination 22 ways 1 -> 0; motor_vehicle=permit 1 way 0 -> 1.
    oneway     6 ways 0 -> 1: the roundabouts with no `oneway` tag (R2).
  Neither moves the FILE SIZE: SQLite stores integer 0 and integer 1 as zero-payload serial types 8 and 9,
  so `bytes` is expected to be 6,135,808 exactly; `content_sha256` is expected to DIFFER from T-0206's, and
  that difference is the point. Measured differently from this prediction, the difference gets its own Log
  line before the PR is opened.
