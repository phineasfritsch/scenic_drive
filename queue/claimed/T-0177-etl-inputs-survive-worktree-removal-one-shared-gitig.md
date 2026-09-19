---
id: T-0177
title: ETL inputs survive worktree removal - one shared gitignored inputs directory outside .worktrees/, and the fetcher and the extract read it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T01:02:12Z
lease_expires_at: 2026-09-19T09:02:12Z
worktree: .worktrees/T-0177
branch: task/T-0177
exclusive: []
touches: [services/etl/etl/fetch.py, services/etl/etl/manifest.py, services/etl/tests/, ops/etl-fetch-inputs, ops/etl-extract, .gitignore, queue/README.md]
pins_affected: []
reviewer: null
depends_on: [T-0169]
verify: [ops/test, ops/check-pins]
acceptance:
  - "`python -m etl.fetch` and `ops/etl-fetch-inputs` resolve the inputs directory to ONE path shared by every worktree (the main checkout's services/etl/inputs/, or an env var SCENIC_ETL_INPUTS documented in queue/README.md), never <worktree>/services/etl/inputs/; RED by name: a test that runs the resolver from a fake worktree path and asserts the shared path, red today"
  - "`--verify-only` over the shared directory is the acceptance for every task that consumes an input; the verified line quoted"
  - "cd services/etl && python -m pytest tests -rs -> count line and zero skips at the final commit"
---
## Brief

From the 17:13 panel (STRATEGY, grounded). T-0169 fetched and verified the 1,328,688,632-byte California extract
into `.worktrees/T-0169/services/etl/inputs/` (gitignored); the worktree was removed with `--force` the hour
PR #99 merged and the deliverable went with it. Only an unverifiable 2026-09-08 build survives as hardlinks in
two old worktrees. T-0168 starts with a second 7m43s fetch. Rule: inputs live in ONE gitignored directory
outside `.worktrees/` (`fetch.py`'s `DEST = ROOT / "inputs"` is per-worktree today), the fetcher and
`ops/etl-extract` read it, and `queue/README.md` says so. Not a symlink farm (Windows).

## Log
- 2026-09-19T00:40:47Z filed by agent/claude-fable-5-1 from the 17:13 panel's grounded synthesis. Not started.
- 2026-09-19T01:02:12Z claimed by agent/claude-opus-5; lease until 2026-09-19T09:02:12Z

### 2026-09-19T01:13:59Z agent/claude-opus-5 — RULINGS (taken before the first edit to fetch.py, recorded here)

**R1 — where the resolver lives.** The Brief wants "the fetcher and `ops/etl-extract`" to read one directory.
`touches:` names `services/etl/etl/fetch.py`, `manifest.py`, `tests/`, the two ops wrappers, `.gitignore` and
`queue/README.md`. A new module `services/etl/etl/inputs_dir.py` matches no prefix in that list and
`.githooks/pre-commit` would refuse the commit, so `resolve_inputs_dir` is a function in `fetch.py`, where
`DEST` already lived. `fetch.py` stays under the 300-line cap (`wc -l` below).

**R2 — only the PAYLOADS are shared; `MANIFEST` is not.** `MANIFEST` stays `ROOT / "inputs" / "manifest.yaml"`.
`.gitignore` ignores `services/etl/inputs/*` but keeps `manifest.yaml` tracked, so the manifest is per-checkout
by design: a task that edits its own manifest must fetch against THAT edit, not the main checkout's copy.
Sharing the manifest too would silently ignore a worktree's edit. Guarded by
`test_the_manifest_stays_in_this_checkout`, which is green today, so it is demonstrated red by mutation below.

**R3 — `ops/etl-extract` is NOT rewritten.** It `cd`s to the current checkout and execs `python -m etl.extract`;
the per-worktree path it ends up using is `INPUTS = ROOT / "inputs"` inside `services/etl/etl/extract.py`, which
is NOT in `touches:`. Teaching the bash wrapper the worktree→root mapping would put a second implementation of
the rule in the one language this task has no tests in, and would have to guess when to override an explicit
`--input`. The wrapper is left byte-for-byte unchanged (`git status` below shows it unmodified). `extract.py`,
`dem.py`, `landcover.py` and `oracle.py` remain per-worktree — STILL OPEN below.

**R4 — `ops/etl-fetch-inputs` needs no logic.** It execs `etl.fetch`, so it inherits the resolver. Only its
header comment changed; its mode stays `100755` (`git ls-files -s` below).

**R5 — no mutation population under `ops/mutate/`.** CLAUDE.md requires one for a new *numeric* module;
`resolve_inputs_dir` computes a path and does no arithmetic, and `ops/mutate/` is outside `touches:`. The
mutation below is one hand-run mutant recorded verbatim to make a green-only guard red — not a population.

**R6 — `.gitignore` needs no new rule.** `services/etl/inputs/*` already ignores the payloads in the main
checkout, which is exactly where they now land, so a fetch from a worktree never shows up in `git status`
anywhere. Only a comment was added, naming that path as both sides of the mapping.

**R7 — the two unverifiable 2026-09-08 copies are left alone.** Measured, not moved, not deleted, not copied
into the shared directory (nothing ever verified them; no `verified ...` line exists for them):

```
$ ls -la .worktrees/T-0028/services/etl/inputs/ .worktrees/T-0107/services/etl/inputs/
=== T-0028 inputs ===
-rw-r--r-- 2 phineasf 197121    8764515 Sep  7 14:13 byways-caltrans.geojson
-rw-r--r-- 2 phineasf 197121   29545684 Sep  7 14:14 byways-fhwa.geojson
-rw-r--r-- 2 phineasf 197121 1327206195 Sep  8 05:06 california-osm.pbf
-rw-r--r-- 1 phineasf 197121      11259 Sep  7 16:23 manifest.yaml
=== T-0107 inputs ===
-rw-r--r-- 2 phineasf 197121    8764515 Sep  7 14:13 byways-caltrans.geojson
-rw-r--r-- 2 phineasf 197121   29545684 Sep  7 14:14 byways-fhwa.geojson
-rw-r--r-- 2 phineasf 197121 1327206195 Sep  8 05:06 california-osm.pbf
-rw-r--r-- 1 phineasf 197121      11259 Sep  8 04:42 manifest.yaml
```

Link count 2 on the three payloads: the two worktrees hold the same hardlinked bytes, so there is ONE copy, not
two. `california-osm.pbf` there is 1327206195 bytes, while the Brief above records T-0169's verified extract as
1,328,688,632 bytes — not the same file, on top of never having been verified here. This task does not adopt them.

### 2026-09-19T01:14:38Z agent/claude-opus-5 — RED BY NAME, then green

New file `services/etl/tests/test_inputs_dir.py`, written before the resolver existed. Red run, verbatim
(`__pycache__` purged first; `cd services/etl`):

```
$ python -m pytest tests/test_inputs_dir.py -rf --tb=no
FFFFFF.F                                                                 [100%]
=========================== short test summary info ===========================
FAILED tests/test_inputs_dir.py::TestResolveInputsDir::test_a_worktree_resolves_to_the_main_checkouts_inputs
FAILED tests/test_inputs_dir.py::TestResolveInputsDir::test_a_plain_checkout_resolves_to_its_own_inputs
FAILED tests/test_inputs_dir.py::TestResolveInputsDir::test_the_env_var_overrides_the_worktree_mapping
FAILED tests/test_inputs_dir.py::TestResolveInputsDir::test_a_blank_env_var_is_not_an_override
FAILED tests/test_inputs_dir.py::TestResolveInputsDir::test_it_creates_nothing_and_links_nothing
FAILED tests/test_inputs_dir.py::TestTheModuleUsesTheResolver::test_dest_is_never_inside_a_worktree
FAILED tests/test_inputs_dir.py::TestTheModuleUsesTheResolver::test_verify_only_names_the_directory_it_verified_against
7 failed, 1 passed in 0.39s
```

The first five are `AttributeError: module 'etl.fetch' has no attribute 'resolve_inputs_dir'`. The sixth is the
T-0169 loss itself, red because this session is running inside a worktree:

```
>       assert ".worktrees" not in fetch.DEST.parts, fetch.DEST
E       AssertionError: WindowsPath('C:/Users/phineasf/Documents/GitHub/scenic_drive/.worktrees/T-0177/services/etl/inputs')
```

The one test that passed, `test_the_manifest_stays_in_this_checkout`, is green today by construction (R2), so it
was made red with one mutant — `MANIFEST = DEST / "manifest.yaml"` appended after `DEST = resolve_inputs_dir(ROOT)`
— and the mutant reverted immediately after:

```
$ python -m pytest tests/test_inputs_dir.py -rf --tb=line
E   AssertionError: WindowsPath('C:/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/inputs/manifest.yaml')
=========================== short test summary info ===========================
FAILED tests/test_inputs_dir.py::TestTheModuleUsesTheResolver::test_the_manifest_stays_in_this_checkout
1 failed, 7 passed in 0.46s
```

Green after the resolver landed and the mutant was reverted:

```
$ python -m pytest tests/test_inputs_dir.py tests/test_fetch.py -rf
29 passed in 1.38s
```

### 2026-09-19T01:14:38Z agent/claude-opus-5 — what changed, and `--verify-only` against the shared directory

`fetch.resolve_inputs_dir(etl_root, env=None)`: `SCENIC_ETL_INPUTS` wins (blank does not count); else the
rightmost `.worktrees` segment with a name after it maps `<root>/.worktrees/<name>/services/etl` to
`<root>/services/etl/inputs`; else `<etl_root>/inputs`. It creates nothing and links nothing — no symlink farm,
because this tree is developed on Windows. `DEST = resolve_inputs_dir(ROOT)`; `MANIFEST` unchanged (R2).
`verify_only` now prints `inputs directory: <path>` on stdout before the per-input lines.
`queue/README.md` gains the three-row resolver table, the `--verify-only` acceptance and what is still
per-worktree. `.gitignore` and `ops/etl-fetch-inputs` gain comments only.

`--verify-only` run from this worktree, bare (stdout and stderr interleave in the terminal: the per-input
failures are stderr, `inputs directory:` is the first line of stdout). It downloaded nothing and deleted nothing:

```
$ bash ops/etl-fetch-inputs --verify-only; echo "EXIT=$?"
california-osm.pbf: not on disk at C:\Users\phineasf\Documents\GitHub\scenic_drive\services\etl\inputs\california-osm.pbf (--verify-only never downloads)
vermont-osm.pbf: not on disk at C:\Users\phineasf\Documents\GitHub\scenic_drive\services\etl\inputs\vermont-osm.pbf (--verify-only never downloads)
... 13 more, one per manifest entry, all under the same directory ...
VERIFY FAILED: 15 input(s)
inputs directory: C:\Users\phineasf\Documents\GitHub\scenic_drive\services\etl\inputs
EXIT=1
```

That is the deliverable of this task and also its limit: the resolver now points every worktree at
`C:/Users/phineasf/Documents/GitHub/scenic_drive/services/etl/inputs`, and **that directory holds no payload
today** — `ls -la` there shows `manifest.yaml` and nothing else. No `verified NAME bytes=N retrieved=DATE MODE ok`
line can be quoted from it, and this task fetched nothing (no download was in scope, and the unverified
2026-09-08 copies must not be laundered into it — R7).

### 2026-09-19T01:14:38Z agent/claude-opus-5 — ACCEPTANCE re-run at the final pre-review commit

1. **"`python -m etl.fetch` and `ops/etl-fetch-inputs` resolve the inputs directory to ONE path shared by every
   worktree (the main checkout's `services/etl/inputs/`, or an env var `SCENIC_ETL_INPUTS` documented in
   `queue/README.md`), never `<worktree>/services/etl/inputs/`; RED by name: a test that runs the resolver from a
   fake worktree path and asserts the shared path, red today"** — MET. Red by name quoted above (7 failed,
   1 passed), including `test_a_worktree_resolves_to_the_main_checkouts_inputs` (a `tmp_path` shaped
   `<root>/.worktrees/T-9999/services/etl` → `<root>/services/etl/inputs`) and
   `test_the_env_var_overrides_the_worktree_mapping`. Green above. `ops/etl-fetch-inputs --verify-only` run from
   `.worktrees/T-0177` printed `inputs directory:
   C:\Users\phineasf\Documents\GitHub\scenic_drive\services\etl\inputs` — the main checkout, not this worktree.
   `SCENIC_ETL_INPUTS` and the mapping are documented in `queue/README.md` under
   "ETL inputs live in ONE directory, outside `.worktrees/`".
2. **"`--verify-only` over the shared directory is the acceptance for every task that consumes an input; the
   verified line quoted"** — PARTIALLY MET, stated rather than claimed. `--verify-only` now names the directory
   it used and `queue/README.md` says that run is the acceptance. NO `verified ...` line exists to quote: the
   shared directory holds only `manifest.yaml` today, so the run above is `VERIFY FAILED: 15 input(s)`, EXIT=1.
   STILL OPEN below.
3. **"`cd services/etl && python -m pytest tests -rs` → count line and zero skips at the final commit"** — MET
   (`__pycache__` purged first):

```
$ cd services/etl && python -m pytest tests -rs
842 passed in 108.35s (0:01:48)
```

   `-rs` printed no skip section: zero skipped.

Also run bare at this commit:

```
$ wc -l services/etl/etl/fetch.py services/etl/tests/test_inputs_dir.py
  292 services/etl/etl/fetch.py
   77 services/etl/tests/test_inputs_dir.py
  369 total

$ bash ops/lib/check-line-cap; echo "EXIT=$?"
P-SRC-02: 71 Swift files tracked (Sources=26, Tests=37, apps/ios=8), none over 300 lines
EXIT=0

$ bash ops/queue-check; echo "EXIT=$?"
QUEUE OK (175 tasks)
EXIT=0

$ git ls-files -s ops/etl-fetch-inputs ops/etl-extract .gitignore
100644 f6703fa97b8f4f0f5b0fd1467525f6bb7b553fe0 0	.gitignore
100755 ad4f7f3e6bc6d51c5ada5634e834d160968099a9 0	ops/etl-extract
100755 bb01509704da4de4426015b61c67e160e6399923 0	ops/etl-fetch-inputs
```

`check-line-cap` covers Swift only (T-0058 is the open task for that); `fetch.py` at 292 and the new test file at
77 are under the 300-line cap by the `wc -l` above.

### STILL OPEN after this task

- **The shared directory is empty of payloads.** Nobody has fetched into
  `<main>/services/etl/inputs/` yet, so acceptance item 2 has no `verified ...` line. The next task that needs
  California runs `ops/etl-fetch-inputs --only california-osm.pbf` from ANY worktree and it lands in the shared
  directory once, for everyone. This task deliberately did not download (~1.3 GB was not in scope and would not
  have been verifiable as part of this change).
- **`etl/extract.py`, `etl/dem.py`, `etl/landcover.py`, `etl/oracle.py` still compute `ROOT / "inputs"`** and are
  outside this task's `touches:` (R3). `ops/etl-extract` therefore still reads the *current* checkout; until a
  task whose `touches:` names those modules moves them onto `resolve_inputs_dir`, pass
  `--input <main checkout>/services/etl/inputs/california-osm.pbf`. `SCENIC_ETL_INPUTS` reaches `etl.fetch` only —
  `queue/README.md` says exactly that, so nobody reads it as a global switch.
- **`byway_source.load(inputs_dir)`** takes the directory as an argument and so is already callable against the
  shared path; no caller was audited here.
- **Nothing garbage-collects the old per-worktree copies.** The 2026-09-08 hardlinked set in `.worktrees/T-0028`
  and `.worktrees/T-0107` is untouched (R7) and still occupies the disk it occupied before this task.
