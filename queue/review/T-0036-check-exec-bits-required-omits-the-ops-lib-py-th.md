---
id: T-0036
title: check-exec-bits REQUIRED omits the ops/lib/*.py that back six wrappers
state: review
owner: agent/builder-3
owner_session: 01SS4jAGs2oyr4Z4Wd8yK82t
claimed_at: 2026-09-07T15:42:10Z
lease_expires_at: 2026-09-07T18:42:10Z
worktree: ../wt/T-0036
branch: task/T-0036
exclusive: []
touches: [ops/lib/check-exec-bits, ops/lib/junit_count.py, ops/lib/pins.py, ops/lib/queue.py, ops/lib/ro_grammar.py]
pins_affected: []
reviewer: agent/reviewer-19
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/check-exec-bits` (pin P-OPS-01) had a `REQUIRED` array of 15 scripts checked for both git-tracking
(existence) and mode. It omitted `ops/lib/junit_count.py`, `pins.py`, `queue.py`, `ro_grammar.py` and
`ro_cases.json` — the Python/data helpers that six wrapper scripts (`ops/check-pins`, `ops/claim`, `ops/lock`,
`ops/new-task`, `ops/queue-check`, `ops/queue-next`, `ops/queue-sweep`, `ops/prod-read`, `ops/test`) `exec`/invoke
via an explicit interpreter. Deleting or renaming any of them silently breaks those wrappers, but the pin never
noticed. `ops/lib/classify-checks.py`, named in the task title's search, does not exist in this repo (confirmed
by `git grep -in classify` and `ls ops/lib`) so it is not added — REQUIRED must only name files that are
actually present, or the check would fail permanently.

Fix: add the five files to `REQUIRED`. Separately, grepped every call site of every `ops/lib/*.py` file
(`ops/check-pins:2`, `ops/claim:2`, `ops/lock:2`, `ops/new-task:2`, `ops/queue-check:2`, `ops/queue-next:2`,
`ops/queue-sweep:2` all `exec "${PYTHON:-...}" .../ops/lib/{pins,queue}.py`; `ops/prod-read:16-17` and
`ops/test:28,46` both `"$PY" ops/lib/{ro_grammar,junit_count}.py`) and found none is ever run as a bare
`./ops/lib/x.py` — every one is passed as an argument to an interpreter, so the executable bit does nothing for
them. The pre-existing mode rule bucketed anything not matching `\.(json|txt|md)$` (or `ops/api-url`) as "script,
must be 100755", which swept the `.py` helpers into that bucket "because they sound like scripts" even though the
call-site evidence says they don't need +x. Chose to assert what's true instead: added `py` to the data-file
extension regex so `ops/lib/*.py` is required to be 100644, and flipped the four helpers that were 100755
(`junit_count.py`, `pins.py`, `queue.py`, `ro_grammar.py` — `ro_cases.json` was already 100644) via
`git update-index --chmod=-x`. This is a real (mode-only, zero content diff) change to those four files, so
`touches:` was widened from `[ops/lib/check-exec-bits]` to include them.

## Log
- 2026-09-07T15:42:10Z claimed by agent/builder-3; lease until 2026-09-07T18:42:10Z
- 2026-09-07T15:50:00Z BASELINE (unfixed script): `bash ops/lib/check-exec-bits` -> `P-OPS-01: 23 files, 15
  required present, all modes correct`, EXIT=0.
- 2026-09-07T15:50:00Z RED 1 (proves the gap, unfixed REQUIRED): `git rm --cached ops/lib/queue.py` (untracks the
  file the six wrappers above `exec` via `ops/lib/queue.py`; working-tree file left untouched) then
  `bash ops/lib/check-exec-bits` ->
  ```
  P-OPS-01: 22 files, 15 required present, all modes correct
  ```
  EXIT=0. The pin passes clean while a load-bearing helper is gone from git. Restored with `git reset --
  ops/lib/queue.py`; re-ran the baseline command and got `23 files, 15 required present, all modes correct`,
  EXIT=0 again — confirms the probe was non-destructive.
- 2026-09-07T15:52:00Z Applied fix to `ops/lib/check-exec-bits`: REQUIRED += `ops/lib/junit_count.py
  ops/lib/pins.py ops/lib/queue.py ops/lib/ro_grammar.py ops/lib/ro_cases.json`; mode regex
  `\.(json|txt|md)$` -> `\.(json|txt|md|py)$`.
- 2026-09-07T15:53:00Z Ran the fixed script against the untouched real tree (mode not yet flipped) to prove the
  regex change actually bites: `bash ops/lib/check-exec-bits` ->
  ```
  P-OPS-01: wrong git file mode:
    ops/lib/junit_count.py (data, should be 100644, is 100755)
  ops/lib/pins.py (data, should be 100644, is 100755)
  ops/lib/queue.py (data, should be 100644, is 100755)
  ops/lib/ro_grammar.py (data, should be 100644, is 100755)
    Fix with: git update-index --chmod=+x <path>   (or --chmod=-x for data files)
  ```
  EXIT=1.
- 2026-09-07T15:53:30Z `git update-index --chmod=-x ops/lib/junit_count.py ops/lib/pins.py ops/lib/queue.py
  ops/lib/ro_grammar.py` (mode-only; `git diff --cached` on these four shows only `old mode 100755` / `new mode
  100644`, no content change). `bash ops/lib/check-exec-bits` -> `P-OPS-01: 23 files, 20 required present, all
  modes correct`, EXIT=0.
- 2026-09-07T15:54:00Z GREEN (same probe as RED 1, now against the fixed script): `git rm --cached
  ops/lib/queue.py` then `bash ops/lib/check-exec-bits` ->
  ```
  P-OPS-01: load-bearing script(s) not tracked: ops/lib/queue.py
  ```
  EXIT=1. Gap closed. Restored with `git reset -- ops/lib/queue.py`, then re-applied
  `git update-index --chmod=-x ops/lib/queue.py` (the `reset` had put the index mode back to the committed
  100755, since the chmod-only change was still uncommitted at that point) to return to the intended fixed
  state. Also proved a rename is caught the same way: `git mv ops/lib/ro_grammar.py
  ops/lib/ro_grammar_renamed.py` -> `P-OPS-01: load-bearing script(s) not tracked: ops/lib/ro_grammar.py`,
  EXIT=1; renamed back with `git mv ops/lib/ro_grammar_renamed.py ops/lib/ro_grammar.py`.
- 2026-09-07T15:56:00Z Re-confirmed final tree is exactly the intended diff: `git status --porcelain` shows only
  `ops/lib/check-exec-bits` (content) and `ops/lib/{junit_count,pins,queue,ro_grammar}.py` (mode-only, index
  staged) plus this task file changed; `git diff --cached -- ops/lib/{junit_count,pins,queue,ro_grammar}.py`
  shows only `old mode 100755` / `new mode 100644` for each, no content lines.
- 2026-09-07T15:57:00Z MIN_FILES floor still fires: ran a scratch copy of the fixed script with `MIN_FILES=999`
  substituted in (anchor is the `MIN_FILES=17` variable, not a comment) against the real, unmodified tree ->
  `P-OPS-01: only 23 files tracked under ops/ and .githooks/ (expected >= 999). An empty or truncated set must
  never read as 'all modes correct'.`, EXIT=1. Floor logic untouched by this fix and still works.
- 2026-09-07T15:58:00Z Final verification, all on the real repo state:
  - `bash ops/lib/check-exec-bits` -> `P-OPS-01: 23 files, 20 required present, all modes correct`, EXIT=0.
  - `bash ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`, EXIT=0.
  - `bash ops/queue-check` -> `QUEUE OK (34 tasks)`, EXIT=0.
  - `cd services/api && npm ci --no-audit --no-fund` (T-0040 environment gap, not introduced by this task) then
    `bash ops/test` -> `TESTS linux=50/50 ios=skipped failed=0 skipped=0` / `OK`, EXIT=0.
- 2026-09-07T15:59:00Z `touches:` widened from `[ops/lib/check-exec-bits]` to
  `[ops/lib/check-exec-bits, ops/lib/junit_count.py, ops/lib/pins.py, ops/lib/queue.py, ops/lib/ro_grammar.py]`
  to cover the four real (mode-only) file changes; `ops/lib/ro_cases.json` needed no mode change (already
  100644) so it is not in `touches:`, only referenced by the new REQUIRED entry.
- 2026-09-07T16:00:00Z moving to review/, reviewer agent/reviewer-19.
