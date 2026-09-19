---
id: T-0173
title: corpus schema contract - a three-state surface column, TERM_NAMES pinned to score.score, and one schema_version across corpus, Worker and PlaceStore
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T23:11:49Z
lease_expires_at: 2026-09-19T07:11:49Z
worktree: .worktrees/T-0173
branch: task/T-0173
exclusive: []
touches: [services/etl/etl/schema.py, services/etl/etl/terms.py, services/etl/etl/surface.py, services/etl/etl/corpuswriter.py, services/etl/etl/extractway.py, services/etl/etl/contentdigest.py, services/etl/tests/, services/api/src/index.ts, services/api/test/, ops/lib/check-schema-version, pins/PINS.yaml]
pins_affected: [P-PROD-05]
reviewer: agent/rv1-pr103
depends_on: [T-0030]
verify: [ops/test, ops/check-pins]
acceptance:
  - "services/etl/etl/schema.py: `paved INTEGER NOT NULL CHECK (paved IN (0,1))` becomes a three-state `surface` column (-1 no surface tag, 0 unpaved, 1 paved) with the DDL hash and SCHEMA_VERSION bumped together; RED by name first: a fixture way with no surface tag round-trips through the corpus as 'unknown', not 'paved'"
  - "a test asserting every TERM_NAMES value except `byway` is a parameter of score.score (inspect.signature - the pin test_way_record.py already uses on score_kwargs), red today on `elev_gain`, green after the rename; every score term with no producer module in the tree listed as RESERVED with its producer task (two at this head - sinuosity: T-0161, points_of_interest: T-0164 - the filing's five was wrong: speedfit.py, furniture.py and landcover.py exist), and every other term id asserted to name a producer file that exists"
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
- 2026-09-18T23:11:49Z claimed by agent/claude-opus-5; lease until 2026-09-19T07:11:49Z

- 2026-09-18T23:30Z agent/claude-opus-5, OWNER and AUTHOR. Rulings, all of them before a line of code, on the
  tree at 95393f3. Pointers are file:line at that commit.

  R1. THE ENCODING IS `surface INTEGER NOT NULL CHECK (surface IN (-1,0,1))`, NOT A TEXT ENUM.
  Both are CHECK-enforceable, so the constraint does not decide it. Three things do. (a) The column one line
  above it in the same table already answers a three-valued question that way - `oneway INTEGER NOT NULL
  CHECK (oneway IN (-1,0,1))` (schema.py:79). Two encodings for the same shape in one table is how a reader
  binding columns by position gets one of them wrong, and schema.py rule 8's whole design is a device reader
  that reads native integers with no conversion. (b) The device's question is `surface == -1` - one integer
  compare per segment on the hazard strip's hot path (plan, "Runtime lifecycles"/hazards; HazardFlag.swift:51
  `surfaceUnknown(km:)`), against three string comparisons. (c) It is one byte per way against six to nine,
  over every way in the region. Rejected alternative: keeping `paved` and adding a separate
  `surface_unknown INTEGER` flag column - two columns that can disagree (paved=1 AND surface_unknown=1 is
  representable and meaningless), where one column with three states cannot.

  R2. WHAT -1 MEANS, AND THE RULE IS SCORE.PY'S, IMPORTED, NOT RESTATED.
  score.py:116 is the rule, verbatim: `return surface is None and highway in UNSURVEYED_CLASSES`, with
  score.py:69 `UNSURVEYED_CLASSES = frozenset({"unclassified", "residential"})`. So:
      surface tag present and in the unpaved set   -> 0  unpaved   (positive evidence, CLAUDE.md's gate)
      surface tag absent and highway unsurveyed    -> -1 unknown   (score.py:116 is true for this way)
      anything else                                -> 1  paved
  "Anything else" is deliberate and is ruled here so nobody adds a fourth state later: a present tag that is
  not in the unpaved set (`cobblestone`, `sett`, `asphalt`) is PAVED, because Gates.swift refuses only
  positive unpaved evidence (Gates.swift:153) and score.py flags only an absent tag; and an absent tag on
  primary/secondary/tertiary is PAVED, because score.py:67-68 says in those words that the plan's other half
  "is this set's complement and is expressed by omission".
  `etl/surface.py:surface_state` therefore CALLS `score.raises_surface_unknown_flag` rather than repeating
  its condition. If score.py's rule moves, the column moves with it; a copy would let the corpus and the
  scorer disagree with both files internally consistent, which is the failure the brief's defect 1 names.
  CONSEQUENCE, STATED RATHER THAN HIDDEN: -1 is the FLAG, not the raw fact. A primary with no surface tag is
  stored as 1, and the corpus cannot afterwards tell it from a primary tagged `asphalt`. Nothing needs that
  distinction today (the score treats them identically and the flag does not fire for either). The
  alternative - -1 means "no tag at all", device derives the flag from (surface, highway) - was rejected
  because it puts score.py:116 on the device as a second implementation, which is exactly what this task was
  told not to create. Recorded under STILL OPEN.

  R3. THE UNPAVED SET IS MIRRORED FROM SWIFT BY COPY, AND SAYS SO.
  score.py has no unpaved set on purpose - score.py:29-32 says the safety gates "live in the GraphHopper
  profile and in `ScenicKit.Gates`, never here". So there is nothing in the ETL to import: the set is the
  plan's line 80 list, already typed out once at Sources/ScenicKit/Gates/Gates.swift:80-82
  (`unpavedSurfaces`), and `etl/surface.py:UNPAVED_SURFACES` is a second copy across a language boundary.
  That is a real defect and it is not mine to close here: P-PROD-01 ("one fixture set through all three") is
  the pin for it and its assertion is still `TODO` (PINS.yaml:121). What this task does about it is what it
  can: the Python set is asserted against the seven values typed out in the test, and the test names the
  Swift file and the line, so a widening on one side is one grep from the other. STILL OPEN.

  R4. `paved` LEAVES THE EXTRACT CONTRACT AND ITS PRESENCE IS A REFUSAL.
  extractway.py:22 requires `paved` and extractway.py:100 validates it to (0,1). The new key is `surface`,
  OPTIONAL, carrying the raw OSM tag value (absent = no tag), which is what the three-state rule needs.
  A stale extract that still carries `paved` is REFUSED by name rather than ignored: silently dropping it
  would turn every `paved: 0` way - the unpaved ones, the safety case - into state 1, because an absent
  `surface` on a secondary is paved by R2. Fail-closed, with the file and the way id in the message.

  R5. THE DDL HASH AND SCHEMA_VERSION MOVE TOGETHER: 1 -> 2. `MIN_APP_BUILD` DOES NOT MOVE.
  schema.py rule 1 and test_corpus_schema.py's DDL_SHA256_BY_VERSION are the mechanism; one column changed
  is a DDL change, so `SCHEMA_VERSION = 2` and version 2 gets its own row in that table with version 1 kept
  ("one entry per version ever shipped"). The OTA cost of the bump is zero TODAY and only today: no corpus
  has been published to R2 and no device reader exists (`Sources/` holds ScenicKit, Handoff, Telemetry; no
  PlaceStore target). That is the entire reason this is one slice now instead of a migration later, and it
  is the brief's own argument.
  `MIN_APP_BUILD` stays 1 and is deliberately NOT coupled to SCHEMA_VERSION. The plan's OTA row makes them
  answer different questions - `schema_version == PlaceStore.schemaVersion && min_app_build <= build` - the
  first "can this reader parse this file", the second "is this app build allowed this file". No app build
  exists to be a floor, so 1 ("every build") is the only honest value; any other number would be a
  constraint invented against nothing. It becomes load-bearing with the first TestFlight build that reads a
  corpus, which is T-0175's business, not this task's.

  R6. THE SINGLE SOURCE OF schema_version IS NOT A FILE. IT IS TWO TYPED LITERALS AND A CHECK THAT REFUSES
  ON DISAGREEMENT.
  A shared JSON read by both was considered and rejected. The Worker cannot read `services/etl/` - it is
  bundled by wrangler out of `services/api/` - so "shared" would mean a generated or copied file, i.e. a
  third place for the value to be stale in. Worse, it would delete the property that matters: the Worker's
  version is pinned ON THE WIRE by routes.test.ts:14 `expect(body.schema_version).toBe(0)`, a literal typed
  out by a human, and a test that imports the same constant the handler imports asserts nothing at all.
  So both literals stay typed at their own site, `services/etl/etl/schema.py:SCHEMA_VERSION` and
  `services/api/src/index.ts:SCHEMA_VERSION`, and `ops/lib/check-schema-version` reads the two literals as
  TEXT and refuses on disagreement. The pin is the anchor, exactly as the brief's defect 3 says. The Worker
  goes 0 -> 2 in this same commit with routes.test.ts's wire literal typed out to match.

  R7. `elev_gain` -> `elevation_gain`, AND THE TERM TABLE MOVES OUT OF schema.py.
  TERM_NAMES is the on-device score contract (schema.py rule 6: the score is recomputed from terms_* at
  query time), so every name in it must be a keyword `score.score` accepts. `elev_gain` (schema.py:193) is
  not: score.py:119-122 spells it `elevation_gain`. The rename is free - `term_defs` CONTENT changes, its
  DDL does not, so this does not touch the hash on its own.
  TERM_NAMES also has to stop being six ids where the score has ten. The five missing terms get ids now,
  because a term id is a permanent on-device contract and allocating them under time pressure next to a
  producer is how two of them end up with the same number. Family follows the ODbL split and nothing else -
  `osm` means "derived from OSM alone", `raster` means "not derived from OSM" (the name is historical; the
  table it selects is `terms_raster`, licensed OWN_LICENSE). So: 2 sinuosity, 3 speed_fit, 4 furniture are
  `osm` (geometry and OSM tags); 106 water and 107 points_of_interest are `raster` (NLCD, and Wikimedia
  Commons photo density - plan:89 - which is emphatically not OSM and would otherwise land in the ODbL half
  that CorpusWriter.add_term exists to protect).
  schema.py is 257 lines and the DDL note plus an eleven-row table with producers pushes it over 300, so the
  table moves to `etl/terms.py` and schema.py re-exports the four names corpuswriter.py already reads
  through it. Permitted by this task's own instruction ("split the term table into its own module").

  R8. RESERVED IS MEASURED, AND THE ACCEPTANCE BLOCK'S LIST OF FIVE IS OUT OF DATE. A DISAGREEMENT, RULED.
  The acceptance names "the five score terms with no producer (speed_fit, sinuosity, points_of_interest,
  water, furniture)". Measured on 95393f3, three of those five have a producer module in the tree:
  `etl/speedfit.py` (T-0162, merged), `etl/furniture.py`, and `water` inside `etl/landcover.py`
  (landcover.py:38,58 - T-0027). Two do not: `sinuosity` (T-0161, PR #94, open) and `points_of_interest`
  (T-0164, filed, queue/backlog - way_record.py:55 already says so in `DEFERRED_TERMS`). Producers for the
  rest: curvature etl/curvature.py, elevation_gain and relief etl/terrain.py, canopy and impervious
  etl/landcover.py, byway etl/byways.py.
  "No producer" cannot mean "no rows in a corpus yet", because that is all eleven of them - T-0030 ships
  zero term rows and T-0146 is the assembler, in flight. So RESERVED means: no producer module exists, and
  the entry names the task that will write one. Typed out as a literal in `etl/terms.py` AND typed out again
  in the test, because a test that rebuilds the set from the module under test passes after any edit to it.
  RESERVED = {2: "T-0161", 107: "T-0164"}. Neither of the two is `none filed`.
  The test also asserts the OTHER NINE point at a file that exists, which is what makes RESERVED
  self-correcting rather than decorative: the day T-0161 lands `sinuosity`, that test is red until the entry
  moves out of RESERVED.

  R9. `ops/lib/check-schema-version` IS PYTHON AND IS INVOKED AS PYTHON, NOT AS `bash`.
  This task's instruction says "100644 python" and later quotes the acceptance run as
  `bash ops/lib/check-schema-version`. Those two cannot both be obeyed - bash would read a python file as a
  shell script. The 100644 half is the one with a gate behind it: P-OPS-01 (ops/lib/check-exec-bits:36-44)
  requires ops/lib python to stay 100644 precisely because every call site invokes it as an argument to an
  interpreter, and the pin style this task names, P-GIT-02 (PINS.yaml:208), is
  `"${PYTHON:-$(command -v python3 || command -v python)}" ops/lib/<script>`. So the pin assertion and every
  quoted run in this task use the interpreter form, and the acceptance line is re-quoted below as
  `python ops/lib/check-schema-version` rather than silently reported as a `bash` run that never happened.

  R10. `touches:` WIDENED, BY THE AUTHOR, WITH THE REASON.
  The filed list could not build the acceptance it asks for. A three-state column that "round-trips through
  the corpus" is derived in `etl/extractway.py` (not listed), selected by name in `etl/contentdigest.py:34`
  (not listed - the content digest's own column list), and the check the third bullet requires is a new file
  under `ops/lib/` (not listed). Added: extractway.py, contentdigest.py, terms.py, surface.py and
  `ops/lib/check-schema-version`. Not added, and not touched: anything under `services/etl/etl/assemble.py`
  or `tests/fixtures/assembly_fixture.json` (T-0146) or `apps/ios/` (T-0153).

- 2026-09-19T00:35Z agent/claude-opus-5. THE REDS, BY NAME. Each one runs on a throwaway copy of
  services/etl under .artifacts/T-0173-red/ (gitignored) with ONE line mutated back to the pre-T-0173
  behaviour; the worktree's own tree was never mutated, and __pycache__ was purged before the runs. The
  driver is .artifacts/T-0173-red/reds.py and is deliberately NOT committed: it mutates the tree, it does
  not check it, and a committed mutation script is one `git checkout` from being someone's source of truth.

  RED 1a - acceptance bullet 1, the "comes back paved" half. Mutation in etl/surface.py, one line:
      -        return SURFACE_UNKNOWN
      +        return SURFACE_PAVED  # pre-T-0173: there was no unknown state
  $ cd .artifacts/T-0173-red/A1-unknown-comes-back-paved && python -m pytest tests/test_corpus_schema.py::test_a_residential_way_with_no_surface_tag_round_trips_as_unknown -rs
      F                                                                        [100%]
      ================================== FAILURES ===================================
      ______ test_a_residential_way_with_no_surface_tag_round_trips_as_unknown ______
      >       assert states[105] == UNKNOWN, "a residential way with no surface tag must be unknown, not paved"
      E       AssertionError: a residential way with no surface tag must be unknown, not paved
      E       assert 1 == -1
      tests\test_corpus_schema.py:203: AssertionError
      1 failed in 0.96s
      exit=1

  RED 1b - the same bullet's other half, "or the DDL CHECK refuses". Mutation in etl/schema.py, one line,
  the two-valued domain origin/main's `paved` column had:
      -  surface     INTEGER NOT NULL CHECK (surface   IN (-1,0,1)),
      +  surface     INTEGER NOT NULL CHECK (surface   IN (0,1)),
  $ cd .artifacts/T-0173-red/A2-ddl-check-refuses && python -m pytest tests/test_corpus_schema.py::test_a_residential_way_with_no_surface_tag_round_trips_as_unknown -rs
      F                                                                        [100%]
      ______ test_a_residential_way_with_no_surface_tag_round_trips_as_unknown ______
      >       conn = _built(tmp_path)
      tests\test_corpus_schema.py:197:
      etl\corpus.py:69: in build
          writer.write_features(ways)
      >       self.conn.executemany(
              "INSERT INTO osm_features (way_id, cls, highway, name, surface, access_ok, oneway, node_count, "
              "length_mm, geom_sha256) VALUES (?,?,?,?,?,?,?,?,?,?)", rows)
      E       sqlite3.IntegrityError: CHECK constraint failed: surface   IN (0,1)
      etl\corpuswriter.py:62: IntegrityError
      1 failed in 0.84s
      exit=1
  Both halves matter and neither subsumes the other: 1a is the silent one (a wrong value, a green suite),
  1b is the loud one. The column change without the derivation change is 1b; the derivation change without
  the column change is 1a.

  RED 2 - acceptance bullet 2, red on `elev_gain`. Mutation in etl/terms.py, one line, the name
  origin/main's schema.py:193 carried:
      -    101: "elevation_gain",
      +    101: "elev_gain",
  $ cd .artifacts/T-0173-red/B-elev-gain && python -m pytest tests/test_corpus_schema.py::test_every_term_name_except_byway_is_a_parameter_of_score_score -rs
      F                                                                        [100%]
      _______ test_every_term_name_except_byway_is_a_parameter_of_score_score _______
      >       assert (names - {"byway"}) <= keywords, sorted(names - {"byway"} - keywords)
      E       AssertionError: ['elev_gain']
      E       assert {'canopy', 'c...nterest', ...} <= {'byway_statu...highway', ...}
      E         Extra items in the left set:
      E         'elev_gain'
      tests\test_corpus_schema.py:235: AssertionError
      1 failed in 0.52s
      exit=1

  RED 3 - acceptance bullet 3, the pin's own check, twice: on origin/main's two values, and on this branch
  at the moment the corpus had been bumped and the Worker had not. Both runs are the real check against a
  root assembled from `git show 95393f3:<file>` under .artifacts/T-0173-red/sv/.
  $ python ops/lib/check-schema-version.py --root <origin/main's schema.py and index.ts>
      P-PROD-05: schema_version disagrees - services/etl/etl/schema.py says 1, services/api/src/index.ts says 0.
        A device downloads a corpus only when the two agree (plan, Runtime lifecycles / OTA).
        Fix: bump both in one commit, and type the new value into services/api/test/routes.test.ts.
      exit=1
  $ python ops/lib/check-schema-version.py --root <this branch's schema.py, origin/main's index.ts>
      P-PROD-05: schema_version disagrees - services/etl/etl/schema.py says 2, services/api/src/index.ts says 0.
      exit=1
  The second run is the one that says the pin is not a tautology: the check is red on the tree this task
  produced, right up until the Worker moves with it. Its other five discriminations are `--prove-red`,
  re-quoted whole below.

- 2026-09-19T00:48Z agent/claude-opus-5. THE ACCEPTANCE BLOCK, RE-RUN AND RE-QUOTED WHOLE at the tree of
  this commit. Every gate run bare - not through a pipe, which swallows the exit status. `bash
  ops/check-pins` (full) and `bash ops/test` were NOT run locally, per this task's instruction.

  (1) the whole ETL suite, __pycache__ purged first:
  $ cd services/etl && python -m pytest tests -rs
      ..................................                                       [100%]
      898 passed in 80.14s (0:01:20)
  898 passed, and ZERO skips: `-rs` prints a short summary line per skip and there is none.

  (2) the Worker suite, before and after the wire literal moved - green on both sides, which is the point
  (the bump is deliberate, not a repair):
  $ cd services/api && npx vitest run   # origin/main's index.ts and routes.test.ts, both 0
      Test Files  4 passed (4)
           Tests  71 passed (71)
  $ cd services/api && npx vitest run   # this branch: SCHEMA_VERSION 2, wire literal typed out as 2
      Test Files  4 passed (4)
           Tests  71 passed (71)

  (3) the new check and its red table. Quoted as `python`, not `bash`, for the reason ruled in R9: the file
  is 100644 python and P-GIT-02's interpreter style is what the pin assertion uses.
  $ python ops/lib/check-schema-version.py
      P-PROD-05: schema_version=2 in services/etl/etl/schema.py and services/api/src/index.ts
      exit=0
  $ python ops/lib/check-schema-version.py --prove-red
      P-PROD-05 --prove-red: 7 cases against a copy of the tree at .worktrees/T-0173
        case                                   expect  got  verdict
        control: the tree as committed              0    0  ok
        corpus bumped alone                         1    1  ok
        Worker bumped alone                         1    1  ok
        P-PROD-05 deleted from PINS.yaml            2    2  ok
        corpus literal deleted                      2    2  ok
        Worker literal deleted                      2    2  ok
        corpus literal duplicated                   2    2  ok
      P-PROD-05 --prove-red: all 7 cases behaved as stated
      exit=0

  (4) the repository gates:
  $ bash ops/check-pins --source-only
      PINS ok=12 skipped=13 pending=1 expired=0 failed=0 tier=linux source-only
      exit=0
  $ bash ops/lib/check-line-cap
      P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
      exit=0
  $ bash ops/queue-check
      QUEUE OK (169 tasks)
      exit=0

  (5) the 300-line cap, by hand, because check-line-cap counts Swift only (T-0058 is the open task for
  that and it is not this task's):
  $ wc -l <every file this commit touches>
        157 ops/lib/check-schema-version.py
        266 services/etl/etl/schema.py
         70 services/etl/etl/surface.py
         71 services/etl/etl/terms.py
        145 services/etl/etl/extractway.py
        194 services/etl/etl/corpuswriter.py
         91 services/etl/etl/contentdigest.py
        271 services/etl/tests/test_corpus_schema.py
        118 services/etl/tests/test_surface_state.py
         81 services/api/src/index.ts
         64 services/api/test/routes.test.ts
        242 pins/PINS.yaml
  schema.py was 257 and is 266 because the term table left it for terms.py (R7); without that split the DDL
  note plus an eleven-row table with producers would have carried it past 300.

  (6) the mode of the new script, which P-OPS-01 requires to stay 100644 (ops/lib python is invoked as an
  argument to an interpreter, never executed):
  $ git ls-files -s ops/lib/check-schema-version.py
      100644 b87b1d090f437798e6c4196af544032fb2819ec4 0	ops/lib/check-schema-version.py

  P-PROD-05 is unclaimed on origin/main and on every one of the 30 open PR heads: each head's PINS.yaml
  greps to `P-PROD-01` and nothing else in the P-PROD-* range, so this id collides with nobody in flight.

  STILL OPEN, named rather than implied:
  - NO DEVICE READER EXISTS. `Sources/` holds ScenicKit, Handoff and Telemetry; there is no PlaceStore
    target and no `PlaceStore.schemaVersion`. P-PROD-05 therefore asserts two of the three values it names.
    T-0175 is the task that lands the reader, and the third value joins the equality there.
  - NO CORPUS HAS BEEN PUBLISHED. The OTA cost of SCHEMA_VERSION 1 -> 2 is zero because nothing has been
    written to R2 and nothing on a phone can be invalidated. That is true TODAY and is the whole reason
    this slice exists now; after the first publish the same change is a migration.
  - THE UNPAVED SET IS A COPY ACROSS A LANGUAGE BOUNDARY. `etl/surface.py:UNPAVED_SURFACES` mirrors
    Sources/ScenicKit/Gates/Gates.swift:80-82 by hand. score.py holds no gate list on purpose, so there was
    nothing to import. P-PROD-01 ("one fixture set through all three") is the pin for this and its
    assertion is still TODO; until then the defence is seven literals in one place each, asserted value by
    value on both sides, with the test naming the Swift file and line.
  - THE SURFACE RULE ITSELF IS NOT COPIED: `surface_state` CALLS `score.raises_surface_unknown_flag`. What
    is copied is only the unpaved VALUE SET above.
  - -1 IS THE FLAG, NOT THE RAW FACT (R2). A primary with no surface tag stores as 1 and the corpus cannot
    afterwards tell it from one tagged `asphalt`. No consumer needs the distinction today.
  - `MIN_APP_BUILD` STAYS 1 and is uncoupled from SCHEMA_VERSION (R5). It becomes load-bearing with the
    first app build that reads a corpus - T-0175's business.
  - RESERVED IS SELF-CORRECTING ONLY WHEN THE SUITE RUNS: the day T-0161 lands `sinuosity`,
    test_the_reserved_terms_name_their_producer_task_and_every_other_term_names_a_module goes red until the
    entry moves out of RESERVED. That is intended, and it is the reason the list is typed out twice.
  - TERM ROWS ARE STILL ZERO. T-0030 ships none and T-0146 (in flight) is the assembler that first fills
    terms_osm / terms_raster. This task changes the vocabulary and the columns, not the layering.

- 2026-09-19T00:55Z agent/claude-opus-5. One gate reads the file the entry above changed: `ops/queue-check`
  parses this task's front matter. It was re-run AFTER that entry was appended, at the exact tree of this
  commit - `bash ops/queue-check` -> `QUEUE OK (169 tasks)`, exit=0. This closing line adds Log prose to the
  same file and touches neither the front matter nor the task's shape, so the run above is the run that
  covers it. `state: claimed` and `reviewer: null` are unchanged: the reviewer is not the owner and this
  task is not signed off by writing it.
- 2026-09-19T01:11:44Z **Record corrections from the read-only verification of this build, closed before review - agent/claude-fable-5-1
  (orchestrator), for the owner. The verifier reproduced the three RED tests by name, the check and its
  --prove-red (7 cases), SCHEMA_VERSION 2 in both literals and the wire test, the corpus build, the whole suite
  and the clean tree at 3cf21b8; these are text.** (a) Acceptance bullet 2 was the ORCHESTRATOR's error: it
  listed five producerless terms; three of them have producer modules on main, and ruling R8 (RESERVED =
  {2: T-0161, 107: T-0164}) is grounded. The bullet is amended above to say what R8 says, so the block and the
  tree agree - the ruling stood, the filing moved. (b) "verified unclaimed ... on all 30 open PR heads": `gh pr
  list --state open --limit 100` shows 34 open PRs; every other head greps P-PROD-05 = 0, so the claim holds
  and the count does not. (c) RED 2 cites `elev_gain` at origin/main's schema.py:193; it is line 194 (193 is
  `1: "curvature"`). (d) STILL OPEN (1) says "Sources/ has ScenicKit, Handoff, Telemetry only"; `ls Sources` is
  Handoff and ScenicKit, and the root Package.swift declares those two targets - no Telemetry target exists;
  the load-bearing half (no PlaceStore, no PlaceStore.schemaVersion) stands. (e) R9's summary says every
  quoted run and the pin assertion use `python ops/lib/check-schema-version.py`; the pin uses P-GIT-02's
  interpreter form, as the Log's own section (3) states. (f) The BEFORE run of `npx vitest run` (main's
  literals, 71 passed) was the author's; the verifier repeated only the AFTER run.

- 2026-09-19T02:08:42Z agent/rv1-pr103, REVIEWER of PR #103 at ca266c2. Not the owner
  (agent/claude-opus-5) and not the orchestrator (agent/claude-fable-5-1). **PASS.** Everything below ran
  in a detached worktree at origin/task/T-0173 (`.worktrees/rv1-pr103`), never in the owner's, and every
  mutant was reverted with `git checkout --` with `git status --short` empty after each.

  THE ACCEPTANCE BLOCK, RE-RUN AT THIS HEAD.
  $ cd services/etl && python -m pytest tests -rs        -> `898 passed in 98.15s (0:01:38)`
      Zero skips: `-rs` prints a line per skip and printed none.
  $ cd services/api && npm ci && npx vitest run          -> `Test Files  4 passed (4)` / `Tests  71 passed (71)`
  $ python ops/lib/check-schema-version.py               -> `P-PROD-05: schema_version=2 in
      services/etl/etl/schema.py and services/api/src/index.ts`, exit=0
  $ python ops/lib/check-schema-version.py --prove-red   -> all 7 cases `ok`, exit=0
  $ bash ops/lib/check-line-cap                          -> `P-SRC-02: 71 Swift files tracked
      (Sources=26, Tests=37, apps/ios=8), none over 300 lines`, exit=0
  $ bash ops/queue-check                                 -> `QUEUE OK (169 tasks)`, exit=0
  $ wc -l <the twelve files of section (5)>              -> 157 / 266 / 70 / 71 / 145 / 194 / 91 / 271 /
      118 / 81 / 64 / 242 - every number reproduced to the line.
  $ git ls-files -s ops/lib/check-schema-version.py      -> `100644 b87b1d09...` (P-OPS-01)
  $ gh pr checks 103                                     -> `core pass`, `pins-source-only pass`

  ONE ACCEPTANCE LINE NEEDED TWO RUNS, AND THE FIRST ONE IS RECORDED RATHER THAN HIDDEN. On a COLD review
  worktree, `bash ops/check-pins --source-only` printed `PINS ok=11 skipped=13 pending=1 expired=0
  failed=1` with **P-SAFE-05** failed and `output: (none)`. P-SAFE-05 runs `swift test --filter
  SolarFixtureTests` with no `--scratch-path`, so its first invocation in a fresh worktree has to build
  ScenicKit and the pin's grep sees no `Test run with N tests ... passed` line. Run bare straight after:
  `swift test --filter SolarFixtureTests` -> `Test run with 6 tests in 1 suite passed`, exit=0; and the
  pins run then printed the author's line exactly - `PINS ok=12 skipped=13 pending=1 expired=0 failed=0
  tier=linux source-only`, exit=0. This PR touches no Swift at all (15 files, none under `Sources/` or
  `apps/ios/`), so the cold failure is the box and not the change. Recorded because a reviewer who ran it
  once would have called this PR red over a pin it cannot reach.

  THE COLUMN, READ OUT OF A BUILT CORPUS. Built once from `tests/fixtures/corpus_extract.json` into a temp
  dir: `PRAGMA user_version` = 2 and `meta.schema_version` = 2, and `SELECT way_id, highway, surface` ->
  101 secondary (no tag) `1`, 102 tertiary `cobblestone` `1`, 103 unclassified `gravel` `0`,
  105 residential (no tag) `-1`, 106 motorway (no tag) `1`.

  FOUR MUTANTS OF THE REVIEWER'S OWN, EACH ALONE, `__pycache__` purged before every run.
  m1 `etl/surface.py`, the unsurveyed branch returns `SURFACE_PAVED` (an untagged residential comes back
     paved) -> `test_a_residential_way_with_no_surface_tag_round_trips_as_unknown`,
     `AssertionError: a residential way with no surface tag must be unknown, not paved / assert 1 == -1`.
  m2 `etl/extractway.py`, `RETIRED_WAY_KEYS = ()` (a stale `paved` key accepted silently) ->
     `test_an_extract_that_still_carries_paved_is_refused_by_name`, `Failed: DID NOT RAISE ValueError`.
  m3 `ops/lib/check-schema-version.py`, the Worker literal read out of the corpus file - the check compares
     one literal with itself -> the pin's own command stays GREEN and prints `P-PROD-05: schema_version=2
     in services/etl/etl/schema.py and services/api/src/index.ts`, exit=0. Only `--prove-red` catches it:
     `corpus bumped alone`, `Worker bumped alone` and `Worker literal deleted` -> `NOT DISCRIMINATING`,
     exit=1. RECORDABLE (1) below. The check as committed is NOT vacuous: `--prove-red`'s `Worker bumped
     alone -> 1` at this head is the proof that it reads both files.
  m4 `etl/contentdigest.py`, `surface` dropped from the `osm_features` SELECT -> the WHOLE suite is green
     (pytest exit 0, no failures). RECORDABLE (2) below.

  THE PRODUCT QUESTIONS, RULED.
  (a) CAN AN UNTAGGED ROAD THAT IS UNPAVED IN REALITY COME OUT `1` ON THE DEVICE? Yes, on
  primary/secondary/tertiary (and motorway/trunk/service) - and that is plan:82's own rule, not a defect:
  "Absent surface: primary/secondary/tertiary -> paved; unclassified/residential -> x0.8 +
  `surface_unknown` flag". CLAUDE.md's hard gate is positive evidence only, and state `0` is reached by
  exactly the seven values of plan:80, which I diffed by eye against `Gates.swift:80-82` - identical, and
  `Gates.verdict` (Gates.swift:153) refuses on the same seven. So the gate the device can build from this
  column is the gate the plan specifies, and R2's consequence (an untagged primary is not afterwards
  distinguishable from one tagged `asphalt`) costs nothing the plan asks for: plan:84 raises the flag only
  on the unsurveyed classes, which are exactly the `-1` rows. Upheld as written, and it is already in
  STILL OPEN.
  (b) CAN A REBUILT CORPUS AND A DEVICE'S OLD CORPUS DISAGREE WHILE BOTH SAY `schema_version 2`? Yes -
  `score.UNSURVEYED_CLASSES` is baked into the stored value and is not DDL, so widening it moves stored
  `surface` values with the DDL hash and SCHEMA_VERSION unmoved. RECORDABLE (3), not blocking: the OTA row
  replaces the corpus whole-file (`version` + sha256 -> `tmp/` -> `rename(2)` -> activate at cold launch),
  so rows from two corpora never mix on one device, and
  `test_an_absent_tag_anywhere_else_is_paved` already pins primary/secondary/tertiary/motorway/trunk/
  service OUT of `UNSURVEYED_CLASSES`, so the plan:82 split cannot be widened onto those six in silence.

  RULINGS R1-R10: no disagreement. R2 is judged above against plan:82/:84 and CLAUDE.md's positive-evidence
  gate. R5 (MIN_APP_BUILD stays 1) is right for the reason given - the OTA row makes the two numbers answer
  different questions. R8's measurement holds at this head: the nine non-reserved ids are asserted to name a
  file that exists and the suite is green. R9 is right and P-OPS-01's own comment (ops/lib/check-exec-bits:
  37-41) says why: `ops/lib/*.py` is invoked as an argument to an interpreter, so 100644 is the mode the
  repo depends on.

  BLOCKING: none.

  RECORDABLE, for the queue rather than this PR (in addition to the STILL OPEN list, which I re-read and
  did not find overstated - no device reader, no published corpus, the `UNPAVED_SURFACES` copy that T-0181
  owns, and `-1` being the flag):
  (1) `--prove-red` is not run by anything. P-PROD-05's assertion is the bare check, so m3 - a check that
      compares one literal with itself - passes every gate in this repository. A pin that also ran
      `--prove-red`, or a pytest that did, would close it.
  (2) Nothing requires `contentdigest.SELECTS` to cover every column of every table (m4). A dropped column
      narrows `meta.content_sha256` silently, and this PR is what made that column the one carrying the
      safety state. A test comparing each SELECT's column list against the DDL's would close it.
  (3) A rule for when SCHEMA_VERSION bumps: the plan says "on any DDL change", and (b) above is a change of
      MEANING with no DDL diff. A class not named in `test_an_absent_tag_anywhere_else_is_paved` (say
      `living_street`) could join `UNSURVEYED_CLASSES` and move stored values with every gate green.
  (4) Pre-existing, not this PR: P-SAFE-05's assertion runs `swift test` with no `--scratch-path`, which
      CLAUDE.md requires on a shared box, and reports `output: (none)` when the build is what failed.
  (5) A nit, read rather than run: `surface_state`'s docstring says "Order matters". It does not -
      `raises_surface_unknown_flag` is false whenever `surface is not None`, so swapping the two branches
      is an equivalent mutant. The test that claims to pin the order
      (`test_positive_evidence_wins_on_every_class`) is still worth having; the sentence overstates it.

  NOT DONE, said plainly: `bash ops/check-pins` (full) and `bash ops/test` were not run locally, by this
  review's instruction - CI's `core` and `pins-source-only` are both green at ca266c2. I did not re-verify
  "P-PROD-05 is unclaimed on every open PR head" across all 34 heads; I checked `origin/main` only
  (`git show origin/main:pins/PINS.yaml | grep -c P-PROD-05` -> `0`), and the orchestrator's correction
  entry already covers the count.
