---
id: T-0169
title: refetch california-osm.pbf and record what was verified - never edit bytes: to match a file nothing can verify
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-18T21:54:29Z
lease_expires_at: 2026-09-19T05:54:29Z
worktree: .worktrees/T-0169
branch: task/T-0169
exclusive: []
touches: [services/etl/inputs/manifest.yaml, services/etl/etl/fetch.py, services/etl/tests/test_fetch.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "THE VERIFIED FETCH PRINTED IT, and the command is the one this program has (R3 - there is no positional argument and the entry's name: is `california-osm.pbf`). `cd services/etl && python -m etl.fetch --only california-osm.pbf`, run natively per R2, ONE run, started 2026-09-18T22:03:30Z and exited 2026-09-18T22:11:13Z, printed `verified california-osm.pbf bytes=1328688632 retrieved=2026-09-18 md5 ok` between `california-osm.pbf: verified (upstream-md5)` and `FETCH OK: 1 input(s) verified`, `EXIT=0`. The publisher's sidecar and the file on disk are quoted side by side in the Log: both `1f90ab1d0c885e884eea96fdf896a6b7`, `match True`, `stat size 1328688632`. No retry was needed - the daily-rebuild race did not happen"
  - "RED BY NAME BEFORE ANY OF IT EXISTED, twice, both verbatim in the Log. `python -m pytest tests/test_fetch.py -k TestTheVerifiedLine --tb=no -ra` against today's fetch.py -> `4 failed, 17 deselected in 0.66s`, naming `test_a_verified_fetch_prints_the_bytes_and_the_date`, `test_verify_only_reprints_the_line_without_downloading`, `test_verify_only_on_a_missing_file_fails_and_fetches_nothing`, `test_today_utc_is_a_utc_iso_date`, with `AttributeError: module 'etl.fetch' has no attribute 'today_utc'` and `etl.fetch: error: unrecognized arguments: --verify-only`. Then `today_utc()` was added ALONE and the first test still failed on the LINE - `assert 'verified file.bin bytes=2600 retrieved=2020-01-02 md5 ok' in 'file.bin: fetching ...\\nfile.bin: verified (upstream-md5)\\nFETCH OK: 1 input(s) verified\\n'` - which is the acceptance line's own red. Green: `python -m pytest tests/test_fetch.py -rs` -> `21 passed in 1.00s`"
  - "THE EXPECTED VALUES ARE TYPED, NOT COMPUTED FROM THE CODE UNDER TEST. `TestTheVerifiedLine.EXPECTED` is the literal string `verified file.bin bytes=2600 retrieved=2020-01-02 md5 ok`: 2600 is written out because the payload is `b\"scenic drive test payload\\n\"` (26 bytes) times 100 copies, not `len(PAYLOAD)`; the date is a literal because `fetch.today_utc` is monkeypatched to `lambda: \"2020-01-02\"`; and the sidecar the fetcher verifies against, served at `/typed.bin.md5`, carries the typed literal `555d88e602cd0616798d705d3a51c1b4` rather than a digest recomputed from the payload in the test. `report_verified` reads `path.stat().st_size` AFTER verification and never `entry.bytes`"
  - "THE MANIFEST IS A COPY OF THAT LINE, IN THIS COMMIT, AND THE FORBIDDEN NUMBER IS NOT IN IT. `git diff origin/main -- services/etl/inputs/manifest.yaml` is exactly `-  bytes: 1288490188` / `-  retrieved: 2026-09-07` / `+  bytes: 1328688632` / `+  retrieved: 2026-09-18` in the `california-osm.pbf` entry - four lines, one entry, nothing else. 1328688632 is what the verified fetch printed; 1327206195, the size of the unverifiable copy in the old worktrees, appears nowhere in the manifest"
  - "THE 1.3 GB IS NOT IN GIT. `git check-ignore -v services/etl/inputs/california-osm.pbf` -> `.gitignore:38:services/etl/inputs/*\tservices/etl/inputs/california-osm.pbf`, exit 0, and `git status --short` at the commit lists no .pbf. The download log lives in the gitignored `.artifacts/T-0169/`"
  - "THE WHOLE ETL SUITE, run bare at the final commit: `cd services/etl && python -m pytest tests -rs` -> `716 passed in 73.96s (0:01:13)`, exit 0, no `short test summary info` section - zero skips, zero xfails. Two earlier runs of the same command at the same file state printed `716 passed in 91.52s (0:01:31)` and `716 passed in 78.39s (0:01:18)`: the wall clock moves on a shared box, the 716 does not. `tests/test_fetch.py` alone is `21 passed`, and the red run's `17 deselected` is what that file held before, so this task adds 21 - 17 = 4"
  - "`bash ops/lib/check-line-cap`, run bare -> `P-SRC-02: 68 Swift files tracked (Sources=25, Tests=35, apps/ios=8), none over 300 lines`, exit 0. `bash ops/queue-check`, run bare -> `QUEUE OK (166 tasks)`, exit 0"
  - "UNDER THE 300-LINE CAP, `wc -l` at the final commit: `services/etl/etl/fetch.py` 255, `services/etl/tests/test_fetch.py` 299. The test file is one line under and the next test belongs in a new file"
  - "NOT IN THIS TASK. No .pbf is committed and no extract, corpus or tile step ran - T-0168 owns what consumes this file, and the fetched copy exists only in this worktree. The other fourteen manifest entries are untouched and were NOT re-verified (13 are `verify: sha256`; `vermont-osm.pbf` is the same upstream-md5 shape as california and is still carrying a 2026-09-07 date - STILL OPEN #1). No positional `california` argument was added to the CLI (R3). `--verify-only` deliberately does not delete a file that fails (R7). `ops/test` and `ops/check-pins` were NOT run locally: the default swift scratch path does not build inside a worktree on this box. CI on the PR is the only run of them, read once after pushing"
---
## Brief

From the 2026-09-18 14:13 panel (DIRECTION lens; one clause corrected by the grounding pass). The manifest's
california entry is `verify: upstream-md5` (Geofabrik rebuilds daily, so a sha256 pin would break daily) and
records `bytes: 1288490188` at `retrieved: 2026-09-07`. Two old worktrees hold a california-osm.pbf of
1,327,206,195 bytes - a DIFFERENT daily build, whose md5 sidecar no longer exists, so nothing can verify it.

**Forbidden, by name:** editing `bytes:` to 1327206195 so the manifest "matches" the file on disk. That asserts
a number against the file it was read from - this repository's signature defect.

**Do:** run `ops/etl-fetch-inputs` in WSL (it wraps `python -m etl.fetch`, which verifies the download against
TODAY's Geofabrik md5 sidecar). The grounding pass checked: the fetcher does NOT write the manifest - so record
`bytes:` and `retrieved:` from the verified file in the same commit and quote the md5 match in the Log.
Optional, small: make `etl.fetch` print `bytes` and the date after a verified fetch so the next refetch is a
copy, not a computation, with a test. 1.3 GB stays out of git (`services/etl/inputs/*.pbf` is ignored - confirm).

## Log
- 2026-09-18T20:57:28Z filed by agent/claude-fable-5-1 from the 14:13 panel's grounded synthesis. Not started.
- 2026-09-18T21:54:27Z PROMOTED to ready/ by agent/claude-fable-5-1 (15:13 panel, STRATEGY, grounded): this is the only unblocked link
  of the M2 critical path (T-0169 -> T-0168 -> T-0031) and it sat in backlog/ with `acceptance: []`, where
  `queue.py next`/`claim` (ready/ only) could never offer it. The Brief's "Optional, small" clause is now the
  MANDATORY RED in the acceptance block: `etl.fetch` prints bytes and the date after a verified fetch, red on
  today's fetch.py, then green. The manifest edit alone would be a check nothing can see red.
- 2026-09-18T21:54:29Z claimed by agent/claude-opus-5; lease until 2026-09-19T05:54:29Z
- 2026-09-18T22:00:20Z rulings by agent/claude-opus-5, BEFORE any code. Every disagreement between the plan, the Brief,
  the acceptance block and the code as it stands today.
  - **R1 - where the 1.3 GB lands, and that git cannot see it.** `fetch.py:24-26` sets
    `ROOT = Path(__file__).resolve().parents[1]` and `DEST = ROOT / "inputs"`, so inside this worktree the file
    lands at `.worktrees/T-0169/services/etl/inputs/california-osm.pbf`. Confirmed ignored, not assumed:
    `git check-ignore -v services/etl/inputs/california-osm.pbf` printed
    `.gitignore:38:services/etl/inputs/*	services/etl/inputs/california-osm.pbf`, exit 0. `ls -la
    services/etl/inputs/` at the start of this task listed only `manifest.yaml` (11617 bytes) - this worktree
    has NO pbf yet, so nothing here can be mistaken for a verified file. `df -h /c` printed `191G` available
    against a 1229 MB download.
  - **R2 - the fetcher does not need WSL, and I am not pretending it does.** The Brief says "run
    `ops/etl-fetch-inputs` in WSL". `services/etl/etl/fetch.py` imports `argparse, dataclasses, hashlib, os,
    sys, urllib.request, pathlib` and `etl.manifest` - stdlib only. No osmium, no GDAL, no docker, no
    osm2pgsql. The plan's WSL2 line (plan:185) is about the pipeline AFTER the fetch (`osmium extract` ->
    `osm2pgsql --flex` -> GraphHopper import), not about the manifest fetch. RULING: it runs natively on the
    Windows python, and that is measured, not assumed - `python -m etl.fetch --dry-run --only
    california-osm.pbf` printed `california-osm.pbf           missing       1229 MB  verify=upstream-md5
    ODbL-1.0             https://download.geofabrik.de/north-america/us/california-latest.osm.pbf`, exit 0,
    under `Python 3.10.11`. Running the 1.3 GB transfer through `wsl -e bash -lc` would put it on the 9p
    filesystem bridge for no benefit. WSL is NOT used by this task.
  - **R3 - `python -m etl.fetch california` is not a command this program has.** The acceptance block's first
    line names it. `fetch.py:104-109` defines `--dry-run`, `--only`, `--record-digest`, `--manifest` and NO
    positional argument, and the manifest entry's `name:` is `california-osm.pbf`, not `california`. RULING:
    the command is `python -m etl.fetch --only california-osm.pbf` (equivalently `bash ops/etl-fetch-inputs
    --only california-osm.pbf`, which forwards `"$@"`). I am NOT adding a positional alias: `--only` is the
    selector the wrapper, the existing tests and the manifest header all use, and inventing a second spelling
    for it is scope this task did not buy. The acceptance block below quotes the command I actually ran.
  - **R4 - what `retrieved:` means.** RULING: the UTC calendar date on which the bytes on disk were verified
    against the publisher's checksum sidecar - NOT the date Geofabrik built the extract (the fetcher never
    learns it), and NOT the date the manifest line was typed. So the printed date must be taken at the moment
    `verify()` returns None, and `fetch.today_utc()` is `datetime.now(timezone.utc).date().isoformat()` -
    `timezone.utc` explicitly, because a local-time date would be a day ahead or behind for most of the world
    and would make two agents in different zones write different `retrieved:` for the same file.
  - **R5 - the forbidden edit stands.** `bytes:` is NOT set to 1327206195. That number is the size of a
    DIFFERENT daily build sitting in old worktrees whose md5 sidecar no longer exists; writing it into the
    manifest would assert a number against the very file it was read from, which is the defect this repository
    exists to catch. `bytes:` gets the size of the file this task downloaded and verified, and
    `git diff origin/main -- services/etl/inputs/manifest.yaml` is quoted verbatim in the acceptance block so
    the number is auditable.
  - **R6 - what the new line says, and which entries get one.** The acceptance block fixes the shape:
    `verified california-osm.pbf bytes=<N> retrieved=<YYYY-MM-DD> md5 ok`. RULING: the trailing token names
    the verification MODE that passed, so an `upstream-md5` entry ends `md5 ok` and a `sha256` entry ends
    `sha256 ok`. One line per entry that verified, on stdout, in addition to the existing prose line - the
    prose line is what a human reads, this one is what the next refetch copies from. It is printed on BOTH
    paths that end in a verified file: a fresh download, and an on-disk copy that re-verified (otherwise
    "re-run it to get the numbers again" would mean re-downloading 1.3 GB). `bytes` is
    `path.stat().st_size` - the size of the file that just passed verification, read after the check, never
    the manifest's own `bytes:` field, which is exactly the circularity this task is about.
  - **R7 - `--verify-only` never downloads and never deletes.** The Brief's optional half asks for a path that
    re-runs the sidecar check without re-downloading. RULING: it is a REPORTING path. It does not download
    (a missing file is a failure, exit 1, not a reason to fetch 1.3 GB), and unlike the fetch path it does not
    `unlink` a file that fails verification. The delete-on-failure rule exists so that THIS PROGRAM never
    leaves an unverified file it just wrote where a later stage could read it; `--verify-only` wrote nothing,
    and `verify()` returns `could not verify (...)` for a network hiccup on a 60-byte sidecar
    (`fetch.py:78-100`), which would make a transient DNS failure delete a 1.3 GB download. It reports and
    exits 1 instead, and says so in its own `--help` text and docstring.
  - **R8 - the RED is the first acceptance line, by name.** `tests/test_fetch.py::TestTheVerifiedLine` is
    written first and run against today's `fetch.py`, which prints only `california-osm.pbf: verified
    (upstream-md5)` and has no `today_utc` and no `--verify-only`. The failures are quoted verbatim below
    before the implementation exists. Expected values are typed-out literals: the fake payload is
    `b"scenic drive test payload\n" * 100`, and `26 * 100 = 2600` is written into the test as the literal
    `bytes=2600` rather than as `len(PAYLOAD)`; the date is pinned by monkeypatching `fetch.today_utc` to the
    literal `"2020-01-02"` so the expected line is a literal string, not a value computed from the clock the
    code under test reads.
- 2026-09-18T22:16:46Z RED FIRST, then green, then the one real fetch. agent/claude-opus-5.

  **RED 1 - all four new tests, by name, against today's `fetch.py` (not one line of it changed yet;
  `git status --short services/etl/` printed only ` M services/etl/tests/test_fetch.py`).**
  `cd services/etl && python -m pytest tests/test_fetch.py -k TestTheVerifiedLine --tb=no -ra`:

        FFFF                                                                     [100%]
        =========================== short test summary info ===========================
        FAILED tests/test_fetch.py::TestTheVerifiedLine::test_a_verified_fetch_prints_the_bytes_and_the_date
        FAILED tests/test_fetch.py::TestTheVerifiedLine::test_verify_only_reprints_the_line_without_downloading
        FAILED tests/test_fetch.py::TestTheVerifiedLine::test_verify_only_on_a_missing_file_fails_and_fetches_nothing
        FAILED tests/test_fetch.py::TestTheVerifiedLine::test_today_utc_is_a_utc_iso_date
        4 failed, 17 deselected in 0.66s

  The two failure shapes, from the first run of the same class
  (`python -m pytest tests/test_fetch.py -k TestTheVerifiedLine -rs`, same four failures, full tracebacks):
  `E   AttributeError: module 'etl.fetch' has no attribute 'today_utc'` and, from the captured stderr,
  `etl.fetch: error: unrecognized arguments: --verify-only` under
  `usage: etl.fetch [-h] [--dry-run] [--only ONLY] [--record-digest NAME] [--manifest MANIFEST]`.
  The `17 deselected` is the count of tests `tests/test_fetch.py` already had, so this task adds 4.

  **RED 2 - the red that names THE ACCEPTANCE LINE ITSELF.** RED 1's first test stops at the monkeypatch, so
  it proves `today_utc` is absent rather than that the LINE is absent. So `today_utc()` was added ALONE - no
  print, no `--verify-only` - and the first test re-run:
  `python -m pytest "tests/test_fetch.py::TestTheVerifiedLine::test_a_verified_fetch_prints_the_bytes_and_the_date" --tb=short`

        tests\test_fetch.py:272: in test_a_verified_fetch_prints_the_bytes_and_the_date
            assert self.EXPECTED in out, out
        E   AssertionError: file.bin: fetching http://127.0.0.1:54473/file.bin
        E     file.bin: verified (upstream-md5)
        E     FETCH OK: 1 input(s) verified
        E
        E   assert 'verified file.bin bytes=2600 retrieved=2020-01-02 md5 ok' in 'file.bin: fetching http://127.0.0.1:54473/file.bin\nfile.bin: verified (upstream-md5)\nFETCH OK: 1 input(s) verified\n'
        1 failed in 0.70s

  That is today's fetcher's whole output after a successful verification: a prose line and nothing a manifest
  can be copied from. GREEN after `report_verified()`, `--verify-only` and the `verify_only()` path:
  `python -m pytest tests/test_fetch.py -rs` -> `21 passed in 1.00s` (17 + 4).

  **THE REAL FETCH, ONCE.** Started 2026-09-18T22:03:30Z, process exited 2026-09-18T22:11:13Z, one run, no
  retry - the Geofabrik sidecar matched first time, so the "daily rebuild raced you" branch was never taken.
  Run natively per R2 (`cd services/etl && python -m etl.fetch --only california-osm.pbf`), backgrounded with
  stdout+stderr to the gitignored `.artifacts/T-0169/fetch.log`. Its control lines, `\r` progress stripped:

        california-osm.pbf: fetching https://download.geofabrik.de/north-america/us/california-latest.osm.pbf
        california-osm.pbf: verified (upstream-md5)
        verified california-osm.pbf bytes=1328688632 retrieved=2026-09-18 md5 ok
        FETCH OK: 1 input(s) verified
        EXIT=0

  **THE MD5 MATCH, both sides quoted** (the fetcher's own `upstream_md5()` and `md5_file()`, run from the
  gitignored `services/etl/work/`):

        sidecar https://download.geofabrik.de/north-america/us/california-latest.osm.pbf.md5
        sidecar md5 1f90ab1d0c885e884eea96fdf896a6b7
        on-disk md5 1f90ab1d0c885e884eea96fdf896a6b7
        match True
        stat size 1328688632

  **THE THREE NUMBERS ARE ALL DIFFERENT, WHICH IS THE POINT.** Today's verified build is 1328688632 bytes.
  The manifest said 1288490188. The file in the old worktrees, the one the Brief forbids copying, is
  1327206195. Had `bytes:` been edited to that third number the manifest would have "matched" a file whose
  sidecar no longer exists. `ls -l services/etl/inputs/` now shows `1328688632 california-osm.pbf` and the
  `.part` file is gone - `download()` renames only on success.

  **`--verify-only` ON THE REAL 1.3 GB FILE**, re-running the sidecar check with no second download:

        california-osm.pbf: verified (upstream-md5)
        verified california-osm.pbf bytes=1328688632 retrieved=2026-09-18 md5 ok
        VERIFY OK: 1 input(s) verified
        rc=0

  Byte-identical to the line the fetch printed, which is what makes the manifest a copy rather than a
  computation.

  **ALSO CHANGED, and it belongs to R3:** `fetch.py`'s own usage block said
  `python -m etl.fetch --only california-osm` - a name the manifest does not have, so the documented command
  exits 2 with `no such entry: california-osm`. It now reads `--only california-osm.pbf` with
  "(the manifest's `name:`, exactly)". One line of docstring, in a file this task already owns.

  **STILL OPEN.**
  1. The other fourteen manifest entries (15 `- name:` lines in all) were NOT refetched and NOT re-verified. Their `bytes:`/`retrieved:`
     still say what they said; thirteen of them are `verify: sha256` (`grep "^  verify:" | sort | uniq -c` -> 13 sha256, 2 upstream-md5) and would fail loudly if they had drifted,
     but `vermont-osm.pbf` is the same `upstream-md5` Geofabrik entry as california and is therefore in
     exactly the state this task just fixed for california - its `bytes: 45880330` / `retrieved: 2026-09-07`
     describe a daily build that is almost certainly gone. Not in scope here (it is `consumed_by: T-0025`),
     and `--verify-only` across all fifteen is now one command when someone wants it.
  2. `services/etl/inputs/california-osm.pbf` exists ONLY in this worktree. T-0168 and anything else that
     consumes it will need its own fetch, or the file copied; nothing in the repo points at this path.
  3. Nothing deletes the stale 1,327,206,195-byte copies in the old worktrees. They are gitignored and out of
     this task's `touches:`.
  4. `ops/test` and `ops/check-pins` were NOT run locally, per the standing rule for this box.
  5. No pin asserts that `retrieved:` is not in the future or that `bytes:` is plausible; `manifest.validate`
     does not look at either field. A check for that is a task, not a line in this one.
- 2026-09-18T22:17:24Z acceptance block written and the whole of it re-run at this, the final pre-review commit, by
  agent/claude-opus-5. Every line above quotes a command run against exactly the tree being committed: the
  suite `716 passed in 73.96s (0:01:13)`, `P-SRC-02: 68 Swift files tracked (Sources=25, Tests=35,
  apps/ios=8), none over 300 lines`, `QUEUE OK (166 tasks)`, `wc -l` 255 and 299, and the manifest diff. No
  measured file was touched after its measurement.
  One pointer note, since a reviewer will open the file: R1 cites `fetch.py:24-26` for `ROOT`/`MANIFEST`/
  `DEST`, which is where `git show origin/main:services/etl/etl/fetch.py` puts them - the numbering the
  ruling was written against. This commit adds the `--verify-only` usage line, the T-0169 paragraph and the
  `datetime` import above them, so in the committed file the same three constants are at `fetch.py:30-32`.
  The ruling is unchanged; only the line numbers moved.
