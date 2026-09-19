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
- 2026-09-19T17:25:59Z BUILT by agent/claude-opus-5 (owner). Each stage quoted as it landed.

  CORRECTION TO R3, one sentence of it. R3 says adding lines to `assemble.py` "refuses the merged head at
  `ops/lib/check-line-cap`". That script's population is `git ls-files 'Sources/**/*.swift'
  'Tests/**/*.swift' 'apps/ios/**/*.swift'` - Swift only - so the 300-line cap on a PYTHON module is
  CLAUDE.md's File discipline rule, carried by review and by the `wc -l` in the acceptance block, not by
  that script. The RULING does not move: 299 + 4 is over the cap either way, and the rule moving out of
  `assemble.py` is what keeps the merged file under it. Ruled here rather than by editing R3, because the
  Log is append-only.

  RED FIRST, before either module existed (cwd services/etl, every __pycache__ purged):
      $ python -m pytest tests/test_extractadapter.py -rs -o addopts=
      ERROR collecting tests/test_extractadapter.py
      E   ImportError: cannot import name 'accessrule' from 'etl'
      1 error in 1.23s
  GREEN, with etl/accessrule.py and etl/extractadapter.py in the tree: `78 passed in 0.62s`, and the whole
  ETL suite `1301 passed in 65.42s`. assemble.py 293 -> 287 lines (R3), so T-0208's 299 merges to 293.

  THE POPULATION, on the committed tree (ops/mutate/extractadapter.py, 25 mutations, floor 25):
      $ python ops/mutate/extractadapter.py
      BASELINE exit=0, 25 mutations, floor 25
      MUTATIONS: 25 caught, 0 missed, 0 skipped, of 25
      EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3
      MUTATE OK  caught=25/25 equivalent_caught=0
      $ python ops/mutate/extractadapter.py --prove-vacuity
      VACUITY: 0 caught, 25 missed, 0 skipped, of 25
      VACUITY PROVED
  Every mutation was caught by a NAMED test; the two the acceptance turns on:
    "derive access_ok from `gate_reason != GATE_NO_ACCESS`, which grants a private dirt road access"
        <- test_a_private_dirt_road_is_refused_although_gate_reason_answers_unpaved_surface
    "skip the out-of-table ways in SILENCE - the count line reads 0 and two roads vanish"
        <- test_a_class_outside_the_table_is_skipped_by_count_and_never_judged
      $ python ops/lib/check-mutate-population.py
      P-PROC-06: 76 modules, 26 covered by 12 populations, 27 allowlisted, 2 added by this branch
      P-PROC-06: every added module is covered or allowlisted; the floor of 25 holds

  THE CANYON WINDOW, END TO END THROUGH THE COMMITTED PATH (cwd services/etl; the documents are the main
  checkout's gitignored work/ dir, read-only; outputs to work/t0217/):
      $ python -m etl.extractadapter --input work/la/window-doc.json --out work/t0217/window-extract.json \
          --region la
      ADAPT ways=11740 skipped_class=0 skipped_short=0 access_blocked=5022 surface_unknown=2308 \
      surface_unpaved=170 surface_paved=9262
      real 0m5.181s
      $ python -m etl.corpus --input work/t0217/window-extract.json --out work/t0217/window-corpus.sqlite \
          --built-at 2026-09-18T00:00:00Z
      CORPUS region=la ways=11740 segments=24205 collisions=0
      CORPUS bytes=6135808 budget=62914560
      CORPUS content_sha256=a642b4ebca9263ae8d06d35481f68d1cabf64bdbf0c43fcf37cfa020251eb876
      CORPUS file_sha256=47cb679b9e55a4cfbd5ebe45f8ea3395b8fce76d3dd3c8aeb8454fcd5caa5fc1
      real 0m13.082s ; stat -c %s -> 6135808
  ways / segments / bytes are T-0206's 11,740 / 24,205 / 6,135,808 EXACTLY. `content_sha256` differs from
  T-0206's 97047605... as R7 predicted, and the difference is measured row by row against that run's own
  extract (work/t0206/window-extract.json, reference only, never imported):
      $ python services/etl/work/t0217/diff_extracts.py
      ways: mine=11740 theirs=11740 only_mine=0 only_theirs=0
      differing rows per field: {'access_ok': 162, 'oneway': 6}
      access_ok (access, motor_vehicle, theirs, mine):  ('customers', None, 0, 1) 85 |
        (None, 'private', 0, 1) 54 | ('destination', None, 1, 0) 22 | (None, 'permit', 0, 1) 1
      oneway (oneway, junction, theirs, mine):  (None, 'roundabout', 0, 1) 6
  Four fields - cls, highway, name, surface, nodes - differ on ZERO rows, no way is added or dropped, and
  the 168 rows that move are exactly the two columns R7 predicted before the run: the throwaway's one
  over-wide list read against both keys (85 + 54 + 1 ways it refused that `Gates.verdict` allows, 22 it
  allowed that `Gates.verdict` refuses) and the roundabouts tagged with no `oneway` key.
- 2026-09-19T17:33:04Z ACCEPTANCE BLOCK, whole, re-run bare by agent/claude-opus-5 (owner) on the MERGED
  head. `git fetch origin && git merge --no-edit origin/main` -> "Already up to date" (origin/main is still
  d4abda0; T-0208 has not landed, so the `DRIVERS` line is uncontested at this commit and the merge that
  resolves it, if T-0208 lands first, keeps both entries).
  Typo in the 17:25:59Z entry, corrected here rather than in place because the Log is append-only: the
  fields that differ on zero rows are FIVE - cls, highway, name, surface, nodes - not "four".

      $ cd services/etl && python -m pytest tests -rs -o addopts=
      1301 passed in 147.00s (0:02:27)                                      exit 0, ZERO skips
      $ python ops/mutate/extractadapter.py
      BASELINE exit=0, 25 mutations, floor 25
      MUTATIONS: 25 caught, 0 missed, 0 skipped, of 25
      EQUIVALENT: 0 caught, 3 missed, 0 skipped, of 3
      MUTATE OK  caught=25/25 equivalent_caught=0                           exit 0
      $ python ops/mutate/extractadapter.py --prove-vacuity
      VACUITY: 0 caught, 25 missed, 0 skipped, of 25
      VACUITY PROVED                                                        exit 0
      $ python ops/lib/check-mutate-population.py
      P-PROC-06: 76 modules, 26 covered by 12 populations, 27 allowlisted, 2 added by this branch
      P-PROC-06: every added module is covered or allowlisted; the floor of 25 holds      exit 0
      $ python -m etl.extractadapter --input work/la/window-doc.json \
          --out work/t0217/window-extract.json --region la
      ADAPT ways=11740 skipped_class=0 skipped_short=0 access_blocked=5022 surface_unknown=2308 \
      surface_unpaved=170 surface_paved=9262                                exit 0
      $ python -m etl.corpus --input work/t0217/window-extract.json \
          --out work/t0217/window-corpus.sqlite --built-at 2026-09-18T00:00:00Z
      CORPUS region=la ways=11740 segments=24205 collisions=0
      CORPUS bytes=6135808 budget=62914560
      CORPUS content_sha256=a642b4ebca9263ae8d06d35481f68d1cabf64bdbf0c43fcf37cfa020251eb876
      CORPUS file_sha256=47cb679b9e55a4cfbd5ebe45f8ea3395b8fce76d3dd3c8aeb8454fcd5caa5fc1     exit 0
      stat -c %s work/t0217/window-corpus.sqlite -> 6135808
      sha256sum -> 47cb679b9e55a4cfbd5ebe45f8ea3395b8fce76d3dd3c8aeb8454fcd5caa5fc1
      (byte-identical to the 17:25:59Z run of the same input: the second build is P-DATA-01's own claim,
      made here for free.)
      $ bash ops/lib/check-line-cap
      P-SRC-02: 90 Swift files tracked (Sources=29, Tests=40, apps/ios=21), none over 300 lines   exit 0
      $ bash ops/lib/check-exec-bits
      P-OPS-01: 84 files, 23 required present, all modes correct            exit 0
      $ bash ops/queue-check
      QUEUE OK (213 tasks)                                                  exit 0
      $ wc -l  (every file this branch touches)
       39 services/etl/etl/accessrule.py           204 services/etl/etl/extractadapter.py
      287 services/etl/etl/assemble.py             253 services/etl/tests/test_extractadapter.py
       29 services/etl/tests/fixtures/canyon_adapter_slice.json
      294 ops/mutate/extractadapter.py             296 ops/lib/check-mutate-population.py
      224 queue/claimed/T-0217-etl-the-waydoc-to-extractway-adapter-corpus-build-has-n.md
      (every source file under the 300-line cap; assemble.py went 293 -> 287, which is the headroom R3 was
      about - T-0208's 299 merges to 293.)
      $ git merge-base --is-ancestor origin/main HEAD ; echo $?
      0
      $ git status --short
      (empty)
- 2026-09-19T17:57:14Z RULED by agent/claude-opus-5 (owner), against the pre-review mutant pass
  (.artifacts/signoffs/t0217-mutant-pass.md, build 85c7b3e: two non-blocking survivors, three unsupported
  claims), before any code. Every measurement below was taken in this worktree, read-only, and is quoted
  with the command that produced it.

  S1 NODE ORDER IS A DEFECT THE POPULATION MUST OWN - AND THE ASSERTION DOES NOT BIND WHERE THE PASS
  SUGGESTED. `oneway` is a FLAG, never a reordering. -1 means "against the way's DRAWN direction", so the
  drawn direction is the thing the router reads the flag against: the adapter copies `coords` into `nodes`
  in document order for every row - forward, reverse and two-way alike - and reversing the nodes of a -1
  row while the flag stays -1 points the geometry against its own direction column, which is a real road
  driven the wrong way. 78 tests said nothing (pass, survivor 1).
  The pass proposed `way(ONEWAY_REVERSE).coords[0] == (34.016213, -118.8209048)`. RULED: NO - that
  assertion is false on the pristine tree, it would test `geom.canonical` rather than the adapter, and the
  reversal mutant would have survived it too. `extractway.way_from_json` CANONICALISES every polyline it
  loads (`geom.canonical`: a ring is rotated to its smallest node; an open way is reversed unless
  `key(coords[0]) <= key(coords[-1])`), so `ExtractWay.coords` is orientation-free BY CONTRACT -
  `geom_sha256`'s own docstring says a way redrawn the other way round hashes the same. Measured,
  `$ python work/t0217/measure.py` (cwd services/etl; the script is gitignored, reference only):
      nodes == document order on all 16 written rows
      loaded ExtractWay.coords: same=6 flipped=8      (+2 closed rings rotated: 338438553, 1025983659)
      1288190701 nodes[0] [34.016213, -118.8209048]   key(first) (340162130, -1188209048)
                 nodes[-1] [34.0160665, -118.8196495] key(last)  (340160665, -1188196495)
                 loaded coords[0] (34.0160665, -118.8196495)  <- the READER's flip, not the adapter's
  So the committed check binds to the EXTRACT DOCUMENT `main` WRITES - the artefact `python -m etl.corpus`
  reads, and the only place the adapter's node order is observable at all - read back off
  `adapted()["path"]`, the same single entry-point run every other test in the file reads. It asserts
  document order on EVERY written row of the slice and pins both endpoints of the reverse row 1288190701
  (Zuma Access Road, oneway=-1) and of the forward row 13465412 (Calle de Sarah, oneway=yes). Shipped as
  mutation 26, "reverse the nodes of every `oneway=-1` row while the flag stays -1".

  S2 THE SHORT-WAY GUARD GETS A ROW, AND IT IS SYNTHETIC BY MEASUREMENT, NOT BY CONVENIENCE. Both real
  documents were scanned first (MAIN checkout, read-only, `len(coords) < 2` over every row):
  la/window-doc.json 11,740 ways / 0 short rows; la-grid/grid-b-doc.json 23,474 ways / 0 short rows -
  R0(c) measured the same thing for the window. There is no real one-node way to slice. RULED: ONE
  synthetic row, way_id 9000000001, `highway=residential` so that it reaches the short guard instead of
  the class skip, carrying its own `"synthetic"` field that says what it is and why it is not real; the
  fixture's other 18 rows stay verbatim-real and the ODbL test now asserts that separation (18 real rows
  from the two named documents, exactly one labelled synthetic row) rather than losing it. The check
  asserts `skipped_short=1` on `main`'s count line AND the way's absence from the written extract, because
  the guard's failure mode is a refusal one module downstream (`load_extract`: "way N: needs at least 2
  nodes, got 1"), not a silent write - and a count-line field whose number has never once been non-zero is
  exactly the "decoration" this module's own docstring warns about. Shipped as mutation 27, "disable the
  short-way guard, so a one-node way reaches a reader that refuses the whole document". Floor 25 -> 27.

  U1 'nodes differ on ZERO rows' (17:25:59Z, corrected 17:33:04Z) was measured by
  work/t0217/diff_extracts.py - uncommitted, gitignored, reference only. FROM THIS COMMIT THE CLAIM RESTS
  ON A COMMITTED CHECK: test_the_nodes_are_the_documents_coordinates_in_document_order asserts it on every
  written row of the committed slice at every run of the suite, and mutation 26 is the proof it can fail.
  The Log line stays what it is - one run's measurement over 11,740 real ways; the standing guard is now
  the test, not the script.

  U2 THE END-TO-END 11,740 / 24,205 / 6,135,808 CANNOT BECOME A COMMITTED ASSERTION, and I will not dress
  one up. Its input is services/etl/work/la/window-doc.json: gitignored, 11,740 real ways, ~24 MB, present
  in no checkout CI clones. A test that asserted those three numbers would either skip (a green that
  measures nothing - the suite is run with zero skips for exactly this reason) or fail everywhere but this
  box. RULED: NO. The committed end of that path is
  test_the_adapted_slice_builds_a_corpus_which_is_the_whole_point_of_the_path (ways == 16, segments >= 16)
  over the committed slice; the three window numbers stay a LOG measurement, re-derivable by the reviewer
  with the two commands quoted verbatim in the acceptance block - which is what the acceptance line asks
  for ("built end to end ... with ways/segments/bytes equal to T-0206's").

  U3 `--prove-vacuity` was not re-run by the pass (it re-ran the forward arm only). It is re-run BARE in
  this commit's acceptance block, over the population of 27.

  STILL OPEN 1, unchanged: ops/lib/check-mutate-population.py's DRIVERS/COVERED_FLOOR and assemble.py
  collide with T-0208, which has NOT merged. The final pre-review merge below keeps both sides.
