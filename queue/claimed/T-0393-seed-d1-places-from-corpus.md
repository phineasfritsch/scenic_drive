---
id: T-0393
title: Nothing fills D1 places - every corpus place id the app sends is 404 unknown_place; ship an ops/seed-places that loads the corpus places table into D1 from the same commit
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-17T07:59:14Z
lease_expires_at: 2026-10-18T07:59:14Z
worktree: .worktrees/T-0393
branch: task/T-0393
exclusive: []
touches: [ops/, services/api/test/, services/api/migrations/, services/etl/etl/, services/etl/tests/]
pins_affected: [P-PROD-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The pilot audit found that the Worker resolves place ids against D1 places (migration 0001), and nothing writes that table: there is no ops/publish-corpus and no seeding. Every Surprise, plan-to-place or trip request with a corpus place id answers 404 unknown_place in production.

MEASURE first:
- which Worker routes read places;
- the D1 places schema against the corpus places table (the app's bundled corpus-fallback.sqlite and the LA corpus built by the region build);
- the row count.

Then RULE the source of truth (the corpus from the same commit as the app; schema_version must match) and write ops/seed-places. It should export the corpus places into idempotent, chunked SQL for `wrangler d1 execute --remote`, with a --dry-run mode that prints the row count and a sha256 of the canonical rows.

Test the exporter through its shipped entry point: a fixture corpus is exported, the SQL is applied to a local D1 (vitest/miniflare), and the rows are read back and compared whole. Re-running must leave the same rows. Never run it against the remote database in this task. The orchestrator runs it once the PR merges, under the owner's authorisation.

## Log
- 2026-10-17 filed by agent/claude-opus-5 from the pilot runbook audit (owner authorised the pilot backend 2026-10-17).
- 2026-10-17T07:59:14Z claimed by agent/claude-opus-5; lease until 2026-10-18T07:59:14Z
- 2026-10-17T08:13:36Z MEASURED (before any code):
  - Worker readers of D1 `places`: exactly one query, `PLACE_QUERY = "SELECT lat, lon FROM places WHERE id = ?1"`
    (services/api/src/placeResolver.ts, `d1PlaceResolver`), wired as `resolvePlace` for /plan (plan.ts:68, :114, 404
    unknown_place at :119) and /trip (trip.ts:90, :94). /trip's place list reads `trip_places` (migration 0009), a
    different table; nothing under ops/ or services/etl writes trip_places either (only ops/lib/named-tests.json
    names it) - out of this task's scope, recorded under stillOpen.
  - D1 schema (migrations/0001_places.sql): `places (id TEXT PRIMARY KEY NOT NULL, lat REAL NOT NULL, lon REAL NOT
    NULL)`. Corpus schema (etl/schema.py, SCHEMA_VERSION = 4): `places (place_id INTEGER PRIMARY KEY, osm_type,
    osm_id, cls, name, lon_e7 INTEGER, lat_e7 INTEGER)` with CHECKs lat_e7 in [-900000000, 900000000], lon_e7 in
    [-1800000000, 1800000000].
  - The id on the wire: PlanRequestBody encodes `String(place)` of the Int64 place_id (PlanRequestBody.swift:106);
    planRequest.ts requires a string matching PLACE_ID. So D1 `id` = the decimal place_id, `lat` = lat_e7 / 1e7.
  - Bundled fallback apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite: meta schema_version 4, region la,
    corpus_version 20261006T000000Z, build_complete 1, content_sha256 9b4e4565...4c17; 1334 places; place_id
    5618378043290861 .. 9221466198646572373 - 1331 of 1334 ids exceed 2^53, so an id must never pass through a JS
    number or a float; lat_e7 336942892..344491615, lon_e7 -1189962124..-1178446900.
  - The LA corpus a region build made (services/etl/work/t0266/la-corpus.sqlite, gitignored): schema_version 3,
    4773 places; all 1334 fallback ids are in it, 1318 with the same (lat_e7, lon_e7) and 16 with a different one.
    There is no ops/publish-corpus: no OTA corpus is published, so today every device opens the bundled fallback
    (LaunchCorpus.choose falls back to it when no downloaded slot exists).
- 2026-10-17T08:13:36Z RULINGS:
  - R1 source of truth. The seed reads ONE corpus file, by default the bundled fallback of the same commit
    (`apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite`), `--corpus PATH` for another. It refuses (exit 2, no file
    written) a corpus whose meta schema_version != etl.schema.SCHEMA_VERSION (the ETL literal P-PROD-05 already ties
    to the Worker's and PlaceStore's), whose build_complete != "1", or that has zero places. The local LA corpus is
    schema 3 and is refused - correct: it is not what any app build carries. When an OTA corpus is published, the
    same command runs over that file before the manifest goes live (recorded, not built here: no publisher exists).
  - R2 upsert, never delete. Each statement is `INSERT INTO places (id, lat, lon) VALUES ... ON CONFLICT (id) DO
    UPDATE SET lat = excluded.lat, lon = excluded.lon`. A re-run leaves the same rows; a coordinate a newer corpus
    moved (16 such ids measured above) is updated; a row the corpus does not carry is KEPT, because an older app
    build's corpus may still send it and 404 is worse than a stale-but-real coordinate. The exporter writes no DDL:
    the migrations own the table, and a database without it fails loudly at execute time.
  - R3 exact coordinates. lat/lon are written as `<lat_e7> / 10000000.0` - integer over a double, IEEE-divided by
    SQLite to the same double as JS `lat_e7 / 1e7` and Python `lat_e7 / 10**7` - so no decimal rendering can round.
    Ids are written as the quoted decimal of the Python int (digits only, so nothing to escape).
  - R4 chunks. One statement per file `places-NNNN.sql`, `--chunk N` rows each (default 500, 1..1000); the exporter
    refuses a statement over 100000 bytes (D1's statement limit). The out dir must be empty or absent.
  - R5 --dry-run writes nothing and prints the one summary line every run prints:
    `seed-places: schema_version=<v> region=<r> corpus_version=<c> rows=<n> chunks=<k> sha256=<hex>` where hex is
    sha256 over "<place_id>\t<lat_e7>\t<lon_e7>\n" per place, ascending place_id. A real run also prints the
    `npx wrangler d1 execute scenic --remote --file <path>` line per chunk for the orchestrator - it never runs it.
  - R6 every row re-validated (corrupt file): place_id int in [1, 2^63-1], lat_e7 int in [-900000000, 900000000],
    lon_e7 int in [-1800000000, 1800000000]; anything else exits 2 naming the place_id.
  - R7 the test seam. Vitest cannot run Python, so the shipped entry point `ops/seed-places` exports a fixture corpus
    (built in services/etl/tests from etl.schema's own DDL) into services/api/test/fixtures/seed-places/, committed;
    a pytest re-runs the entry point and requires those files byte-equal (stale = red). The vitest applies every
    shipped migration, then the committed files, reads `places` back whole, re-applies, reads back whole again, and
    resolves every fixture id through the shipping `d1PlaceResolver`.
  - R8 P-PROC-06: services/etl/etl/seedplaces.py is new and decides coordinates the server plans to, so it ships
    ops/mutate/seedplaces.py with a literal floor, registered in ops/lib/mutate_population_table.py. No PINS.yaml
    change: P-PROD-05's literal is what the exporter compares against, and its check is unchanged.

## Acceptance (T-0393, written 2026-10-17T08:13:36Z before code; re-run and re-quoted at the final commit)
1. `bash ops/seed-places --dry-run` exits 0 and prints exactly one line, `seed-places: schema_version=4 region=la
   corpus_version=20261006T000000Z rows=1334 chunks=3 sha256=<hex>`, and <hex> equals a recomputation in the test
   from the corpus read directly.
2. `cd services/etl && python -m pytest -q tests/test_seedplaces.py` passes, including: the committed fixture files
   byte-equal a fresh run of `ops/seed-places`; refusals exit 2 and write nothing for schema_version 3, 5 and missing,
   build_complete 0, zero places, a non-empty --out, --chunk 0 and 1001; the bound table for place_id (0 refused, 1
   and 2^63-1 accepted), lat_e7 (+-900000000 accepted, +-900000001 refused), lon_e7 (+-1800000000 accepted,
   +-1800000001 refused), a REAL lat_e7 refused; and (rv1 B1) the --out state table through main() - absent,
   absent under an absent parent and an existing empty dir exit 0 writing exactly the fixture files; a non-empty
   dir, a regular file and an empty regular file exit 2 with the exact REFUSED stderr and the path unchanged - each
   row asserting exit code, stdout, stderr and the after-state whole.
3. `cd services/api && npx vitest run test/seedPlaces.test.ts` passes: rows read back from local D1 equal the typed
   expected rows whole (ids above 2^53 as exact strings), a second apply leaves them equal, a stale coordinate is
   updated and a non-corpus row kept, and d1PlaceResolver returns each fixture coordinate and null for an unknown id.
4. RED by name before green: the vitest file run against the fixture with the upsert spelled `DO NOTHING` fails
   the stale-coordinate test; test_seedplaces.py fails on a pre-code tree (module absent).
5. `python ops/mutate/seedplaces.py` prints `MUTATE OK` with caught == population >= floor; `--prove-vacuity` prints
   `VACUITY PROVED`.
6. Gates bare: check-mutate-population, check-mutate-only, check-pins-yaml, check-exec-bits, queue-check,
   check-safety-disclaimer exit 0.
- 2026-10-17T08:48:33Z RED, then GREEN, by name:
  - pytest RED: with services/etl/etl/seedplaces.py moved aside, `python -m pytest -q tests/test_seedplaces.py`
    printed `34 failed in 201.85s` (every test, the last named
    `test_every_bound_of_every_row_field[(5, 0, None)->2]`). GREEN with the module: `34 passed in 37.87s`.
  - vitest RED: the committed fixture SQL rewritten in place to `ON CONFLICT (id) DO NOTHING;` (restored after),
    `npx vitest run test/seedPlaces.test.ts`: `× a stale coordinate is updated and a row the corpus does not carry
    is kept (R2: upsert, never delete)`, `Tests 1 failed | 3 passed (4)`. GREEN on the shipped fixture: `Tests 4
    passed (4)`.
  - R4 CORRECTED: the per-statement 100000-byte refusal was unreachable - the widest row is 76 bytes with its separator, so
    --chunk 1000 of max-width rows is under 80000 bytes - and an unreachable branch is a mutant nothing can kill. It is gone;
    `test_the_widest_statement_the_largest_chunk_can_make_fits_d1s_100000_bytes` exports 1000 rows of 19-digit ids at
    the negative bounds through main() and requires 70000 < bytes < 100000. The wrapper no longer scans its
    arguments for --corpus: it puts the default FIRST and argparse keeps the last, so a caller's --corpus wins.
  - The refusal and bound tables call `etl.seedplaces.main` - what ops/seed-places execs - in process: through bash
    each case cost ~6 s on this box (201 s for the RED run). The three tests that bind the entry point itself (the
    fixture export equal to the committed files, the re-run, the fallback dry-run with no --corpus) run ops/seed-places.
- 2026-10-17T09:57:08Z mutation population, first full run (08:48-09:34): `MUTATIONS: 40 caught, 3 missed`,
  MISSED `CHUNK_MAX raised`, `chunk 0 accepted`, `place_id type check dropped`; EQUIVALENT 0 caught of 1;
  `--prove-vacuity`: `VACUITY: 0 caught, 43 missed` `VACUITY PROVED`. The survivors were test defects:
  test_bad_arguments_are_refused passed --chunk with neither --dry-run nor --out, so the one-of guard refused before
  the chunk bound was reached (now `--dry-run --chunk 0|1001`); the loose corpus declared place_id INTEGER PRIMARY
  KEY, a rowid alias that can only hold an integer, so the type check was unreachable (now untyped; the bound
  table adds 5.0, "5" and NULL place_ids, all refused). Re-run of the three (owner-approved touched-rows-only):
  `MUTATE OK  caught=3/3`, each caught by its named test (`test_bad_arguments_are_refused[chunk-1001]`,
  `[chunk-0]`, `test_every_bound_of_every_row_field[(5.0, 0, 0)->2]`).
- 2026-10-17T09:57:08Z ACCEPTANCE re-run on 56cbd106 (origin/main merged: already up to date):
  1. `bash ops/seed-places --dry-run` exit 0: `seed-places: schema_version=4 region=la
     corpus_version=20261006T000000Z rows=1334 chunks=3
     sha256=0e6435da0287a5211a26bf48710bd89ddd99f4f8ea22cf323ec99a056a908e86`; test_dry_run_of_the_bundled_fallback
     recomputes the line from the corpus read directly. The LA work corpus: `REFUSED: corpus schema_version '3' is
     not this ETL's 4`, exit 2.
  2. `python -m pytest -q tests/test_seedplaces.py`: `38 passed in 19.59s`.
  3. `npx vitest run test/seedPlaces.test.ts test/migrationColumns.test.ts`: `Test Files 2 passed (2)`, `Tests 8
     passed (8)`.
  4. RED by name: quoted at 08:48:33Z above (pytest 34 failed with the module absent; vitest DO NOTHING fails the
     stale-coordinate test).
  5. `python ops/mutate/seedplaces.py`: population 43 = MIN_MUTATIONS 43; full run 40/43 then the three closed
     (above); VACUITY PROVED.
  6. Gates bare, exit 0 each: check-mutate-population (`every added module is covered or allowlisted; the floor of
     172 holds`), check-mutate-only (`MUTATE-ONLY OK: 245 of 245`), check-mutate-anchors (`0 stale`),
     check-pins-yaml (`PINS-YAML ok pins=52`), check-exec-bits (`246 files ... all modes correct`; ops/seed-places
     100755), queue-check (`QUEUE OK (385 tasks)`), check-safety-disclaimer (exit 0).
  Line counts: seedplaces.py 140, test_seedplaces.py 234, ops/mutate/seedplaces.py 160, ops/seed-places 11,
  seedPlaces.test.ts 63.
  NOT DONE HERE (by the Brief): nothing ran against the remote D1. The orchestrator runs, after merge,
  `ops/seed-places --out <dir>` and the printed `npx wrangler d1 execute scenic --remote --file ...` lines.
- 2026-10-17T11:12:37Z rv1 FAIL (agent/rv1-t-0393, head 297e07d6) B1 closed by CLASS - every clause of the --out
  guard and both mkdir arguments. The single non-empty-dir test is replaced by
  `test_every_out_state_exits_0_or_2_with_exact_output_and_files`, a six-row table through `etl.seedplaces.main`
  (absent, absent-under-an-absent-parent, existing-empty-dir, existing-non-empty-dir, existing-regular-file,
  existing-empty-regular-file); every row asserts (exit code, stdout, stderr, after-state) whole, the expectation
  computed from the row's accepted flag and its absolute path. ops/mutate/seedplaces.py gains six mutants - the
  reviewer's (a) `exist_ok dropped`, (b) `the is_dir clause dropped`, (c) `every existing out path refused`, plus
  `parents dropped`, `an out file accepted`, `the exists clause dropped` - MIN_MUTATIONS 43 -> 49 (population 49).
  - RED on the old tests (da40982c, mutants committed, tests untouched; touched rows only, owner-approved):
    `MISSED an existing empty out dir crashes - exist_ok dropped (exit 0)`, `MISSED a nested out dir crashes -
    parents dropped (exit 0)`, `MISSED an out file reaches iterdir - the is_dir clause dropped (exit 0)`, `MISSED an
    out file accepted (exit 0)`, `MISSED every existing out path refused (exit 0)`; `caught an absent out path
    refused - the exists clause dropped <- test_fixture_export_equals_typed_sql_and_the_committed_files`;
    `MUTATE FAILED  caught=1/6`.
  - GREEN (91ff6e6e, the table): `MUTATE OK  caught=8/8` over the six plus the two neighbouring guard mutants, by
    name: exist_ok dropped <- `[existing-empty-dir]`; parents dropped <- `[absent-under-an-absent-parent]`; the
    is_dir clause dropped <- `[existing-regular-file]`; an out file accepted <- `[existing-regular-file]`; every
    existing out path refused <- `[existing-empty-dir]`; a non-empty out dir accepted <- `[existing-non-empty-dir]`;
    the exists clause dropped <- `test_fixture_export_equals_typed_sql_and_the_committed_files`; --dry-run with
    --out accepted <- `test_bad_arguments_are_refused[neither-dry-run-nor-out]`.
  - On the merged head 2bf95207 (origin/main c3fd1f80 + queue commits to 2daea62c merged): `python -m pytest -q
    tests/test_seedplaces.py`: `43 passed in 20.62s`; `--prove-vacuity` over the six: `VACUITY: 0 caught, 6
    missed, 0 skipped, of 6` `VACUITY PROVED`. Gates bare, exit 0 each: check-safety-disclaimer (exit 0, P-SAFE-03
    report), check-mutate-population (`P-PROC-06: every added module is covered or allowlisted; the floor of 172
    holds`), check-mutate-only (`MUTATE-ONLY OK: 245 of 245 driver runs refused with exit 64`), check-pins-yaml
    (`PINS-YAML ok pins=53 fields=426`), check-exec-bits (`P-OPS-01: 247 files, 23 required present, all modes
    correct`), queue-check (`QUEUE OK (385 tasks)`). Line counts: test_seedplaces.py 268, ops/mutate/seedplaces.py
    170, seedplaces.py 140 (unchanged). Acceptance item 2 gains the --out state table clause.
- 2026-10-17T14:50:40Z rv2 FAIL (agent/rv2-t-0393, head b9ef6f90) closed by CLASS. The survivor
  `any(q.is_file() for q in out.iterdir())` lived because OUT_STATES had one non-empty row (a regular file) and
  state()/written() could not represent a subdirectory. Ruling: the --out corpus is every entry type a directory can
  hold, and the oracle is the whole recursive tree. state() is replaced by `tree()` - None, ("link", target),
  ("file", bytes) or ("dir", {name: tree}), recursing, never following a link, failing on any other entry type -
  and `build()` creates the same shape, so each row asserts `tree(out) == before` before the run and a refused row
  expects `before` verbatim after it. OUT_STATES is eleven rows through `etl.seedplaces.main`: absent,
  absent-under-an-absent-parent, empty-dir (the three accepted, exit 0), dir-with-a-regular-file,
  dir-with-an-empty-file, dir-with-an-empty-subdir, dir-with-a-non-empty-subdir, dir-with-a-hidden-dotfile,
  dir-with-a-symlink, regular-file, empty-regular-file (exit 2); each asserts (exit, stdout, stderr, tree) whole.
  The symlink row SKIPS on this box (`[WinError 1314] A required privilege is not held by the client`); it runs
  where a symlink can be made (CI Linux). ops/mutate/seedplaces.py gains `an out dir holding only subdirectories
  accepted` (the rv2 mutant) and `an out dir holding only dotfiles accepted`; MIN_MUTATIONS 49 -> 51.
  - RED (7de135a5: mutants committed, b9ef6f90 tests untouched; touched rows only, owner-approved):
    `MISSED an out dir holding only subdirectories accepted (exit 0)`, `MISSED an out dir holding only dotfiles
    accepted (exit 0)`, `MUTATIONS: 0 caught, 2 missed`, `MUTATE FAILED  caught=0/2`.
  - GREEN (9f1f8cff, the corpus): `MUTATE OK  caught=10/10 equivalent_caught=0` over the two plus every --out and
    mkdir mutant, by name: only subdirectories <- `[dir-with-an-empty-subdir]`; only dotfiles <-
    `[dir-with-a-hidden-dotfile]`; a non-empty out dir accepted <- `[dir-with-a-regular-file]`; exist_ok dropped
    <- `[empty-dir]`; parents dropped <- `[absent-under-an-absent-parent]`; the is_dir clause dropped <-
    `[regular-file]`; an out file accepted <- `[regular-file]`; every existing out path refused <- `[empty-dir]`;
    the exists clause dropped <- `test_fixture_export_equals_typed_sql_and_the_committed_files`; --dry-run with
    --out accepted <- `test_bad_arguments_are_refused[neither-dry-run-nor-out]` (all rows of
    `test_every_out_state_exits_0_or_2_with_exact_output_and_whole_tree`). `--prove-vacuity` over the two:
    `VACUITY: 0 caught, 2 missed, 0 skipped, of 2` `VACUITY PROVED`.
  - On the merged head 80740924 (origin/main 5e4150a0 merged): `python -m pytest -q tests/test_seedplaces.py`:
    `47 passed, 1 skipped in 27.91s` (the skip is the symlink row). Gates bare, exit 0 each:
    check-safety-disclaimer (exit 0, P-SAFE-03 report), check-mutate-population (`P-PROC-06: every added module is
    covered or allowlisted; the floor of 172 holds`), check-mutate-only (`MUTATE-ONLY OK: 245 of 245 driver runs
    refused with exit 64`, `NAME-PAIRS OK: 242093 pair tokens over 49 id populations`), check-mutate-anchors
    (`17 drivers, 1295 anchors, 0 stale`), check-pins-yaml (`PINS-YAML ok pins=53 fields=426`), check-exec-bits
    (`P-OPS-01: 247 files, 23 required present, all modes correct`), queue-check (`QUEUE OK (386 tasks)`). Line
    counts: test_seedplaces.py 293, ops/mutate/seedplaces.py 175, seedplaces.py 140 (unchanged).
