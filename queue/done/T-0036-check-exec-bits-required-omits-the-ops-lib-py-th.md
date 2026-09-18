---
id: T-0036
title: check-exec-bits REQUIRED omits the ops/lib/*.py that back six wrappers
state: done
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
- 2026-09-07T16:30:00Z reviewed by agent/reviewer-19: PASS. Everything below was re-derived independently, not
  taken on the owner's word — GitHub Actions is not running on this repo right now (billing/spending-limit
  block), so all of it was verified locally.

  1. RE-DERIVED RED/GREEN, with a methodology correction. Naively running `git show HEAD~1:ops/lib/check-exec-bits`
     against the CURRENT working tree gives a MISLEADING result — the current tree already has the four `.py`
     files at mode 100644, so the old script (which still buckets `.py` as "script, must be 100755") fails on a
     mode complaint, not on the REQUIRED-list gap the RED is supposed to demonstrate. Used a real detached
     worktree at `HEAD~1` (`f910f5f`, the commit immediately before `a6bab98`) instead, so both the script logic
     and the file modes match the pre-fix state together: `git ls-files -s` there shows all four `.py` helpers at
     100755. Baseline (old script, `queue.py` tracked): `P-OPS-01: 23 files, 15 required present, all modes
     correct`, EXIT=0. RED (old script, `git rm --cached ops/lib/queue.py`): `P-OPS-01: 22 files, 15 required
     present, all modes correct`, EXIT=0 — reproduced exactly, gap confirmed. Restored (`git reset --
     ops/lib/queue.py`), worktree removed. Then on the real `task/T-0036` tree: current (fixed) script baseline
     -> `P-OPS-01: 23 files, 20 required present, all modes correct`, EXIT=0; GREEN probe (`git rm --cached
     ops/lib/queue.py`) -> `P-OPS-01: load-bearing script(s) not tracked: ops/lib/queue.py`, EXIT=1; restored
     (`git reset -- ops/lib/queue.py`), re-ran baseline, got the same `23 files, 20 required present` line back —
     confirms the probe was non-destructive and the mode survived the reset. Matches the task log's claim.

  2. RE-DERIVED the call-site grep across the whole tracked tree (`grep -rn 'ops/lib/[a-zA-Z_]*\.py'`), plus
     specifically checked `queue/README.md`, `.github/workflows/linux-core.yml`, `CLAUDE.md` and
     `apps/ios/ci_scripts/ci_post_clone.sh` per the review brief — none of the four reference `ops/lib/*.py` at
     all, bare or otherwise. Every real reference goes through `"${PYTHON:-...}"`/`"$PY"` (ops/check-pins:2,
     ops/claim:2, ops/lock:2, ops/new-task:2, ops/queue-check:2, ops/queue-next:2, ops/queue-sweep:2,
     ops/prod-read:16-17, ops/test:28,46). No bare `./ops/lib/x.py` invocation exists anywhere in this tree, on
     `task/T-0021`, or on `task/T-0023` (checked below). AGREE with the reclassification under CLAUDE.md's stated
     rule rationale (`ops/lib/check-exec-bits:8-10`, `pins/PINS.yaml` P-OPS-01 `why_no_test_catches_it`: the
     mode matters specifically because "queue/README.md and Xcode Cloud both invoke them directly" — a risk that
     is structurally absent for a file with zero direct-invocation call sites) — a Python module that is *only
     ever* passed as an interpreter argument behaves exactly like a data file with respect to that risk, and
     100644 asserts a fact the repo actually depends on rather than a superstition.
     MINOR / non-blocking: `ops/lib/ro_grammar.py:5-6`'s own module docstring documents its CLI as
     `ro_grammar.py --self-test` / `ro_grammar.py "<sql>"` with no interpreter prefix shown — the file's own
     usage comment models bare invocation as supported usage, even though no code path anywhere does that today.
     Failure scenario: an agent reads that docstring, does `chmod +x` locally (or is on a Linux/macOS checkout
     where `core.filemode` is honored) and types `./ops/lib/ro_grammar.py --self-test` per the doc line — that
     now fails with "Permission denied" post-fix where it worked before. Doesn't break any current or
     soon-to-land automated call site (all confirmed interpreter-prefixed), so not a blocker; worth a one-line
     docstring tweak (`"$PY" ops/lib/ro_grammar.py --self-test`) in a future pass, not this one — `touches:`
     doesn't cover ro_grammar.py's content and this is a doc nit, not a functional gap.

  3. RE-DERIVED via `git fetch` + `git ls-tree -r` on `origin/task/T-0021` and `origin/task/T-0023`. Confirmed:
     `ops/lib/classify-checks.py` (100755, invoked only as `"$PY" ops/lib/classify-checks.py` at
     `origin/task/T-0021:ops/merge:54`, no bare call site) and `ops/lib/gh-stub-for-merge-tests` (100755, a bash
     script, not `.py`) both exist on `task/T-0021`; `ops/lib/check-failure-naming` (100755, a bash script)
     exists on `task/T-0023` and is directly named in `pins/PINS.yaml` as `P-OPS-02`'s assertion on that branch.
     The owner's exclusion of all three from `REQUIRED` is correct as-is (`git ls-files --error-unmatch` on a
     nonexistent path would make the check fail permanently on this branch). MAJOR / needs a follow-up task:
     confirmed the gap is real — the moment `task/T-0021` and/or `task/T-0023` land on `main`, these three files
     become load-bearing and untracked-by-REQUIRED, reopening exactly the silent-deletion hole this task exists
     to close. File a follow-up task, dependent on both T-0021 and T-0023 merging, that: (a) adds
     `ops/lib/classify-checks.py`, `ops/lib/gh-stub-for-merge-tests`, `ops/lib/check-failure-naming` to
     `REQUIRED` in `ops/lib/check-exec-bits`; (b) flips `classify-checks.py` from 100755 to 100644 via
     `git update-index --chmod=-x` (it needs no code change to the mode regex — `\.(json|txt|md|py)$` from this
     task already covers it) since it is a `.py` helper invoked only through `"$PY"`, exactly the class of file
     this task just reclassified; (c) leaves `gh-stub-for-merge-tests` and `check-failure-naming` at 100755
     since both are bash scripts, not `.py`; (d) demonstrates its own RED (untrack one of the three, unfixed
     REQUIRED still green) then GREEN, same pattern as this task's own Log.

  4. RE-DERIVED empirically, not just reasoned about — this is not a hazard. `ops/lib/junit_count.py` is
     content-modified (adds `list_failures()`) on `task/T-0023` with its mode left at 100755 there (unaffected
     by T-0023), while `task/T-0036` changes only its mode (100755 -> 100644, content byte-identical). Actually
     ran the merge: `git worktree add --detach <scratch> task/T-0036` then `git merge --no-commit --no-ff
     origin/task/T-0023` -> "Automatic merge went well; stopped before committing as requested", EXIT=0, `git
     diff --check` empty (no conflict markers), `ops/lib/junit_count.py` shows as a clean staged `M`, not `U`.
     Post-merge: `git ls-files -s ops/lib/junit_count.py` -> `100644 2214196b...` — T-0023's new blob
     (`grep -c list_failures` = 2, confirming the content landed) combined with T-0036's mode (100644). Also
     re-ran `bash ops/lib/check-exec-bits` against the merged tree: `P-OPS-01: 25 files, 20 required present,
     all modes correct`, EXIT=0 (the 3 new files from finding #3 present but silently unchecked, exactly as
     predicted there). Git's three-way merge treats content and file-mode as independent attributes and combines
     them cleanly when only one side changes each — no conflict, no silently-lost mode. Scratch worktree removed
     afterward; no branch or working tree state left behind.

  5. RE-DERIVED all four sub-checks against the check itself, each isolated so as not to touch the committed
     tree: (a) MIN_FILES floor: ran a `sed 's/MIN_FILES=17/MIN_FILES=999/'` copy (anchored on the `MIN_FILES=17`
     variable per the task log, not a comment) -> `P-OPS-01: only 23 files tracked under ops/ and .githooks/
     (expected >= 999). An empty or truncated set must never read as 'all modes correct'.`, EXIT=1 — fires. (b)
     A genuinely non-executable script: `git update-index --chmod=-x ops/agent-preflight` -> `P-OPS-01: wrong
     git file mode: ops/agent-preflight (script, should be 100755, is 100644)`, EXIT=1 — caught; restored with
     `--chmod=+x`. (c) A `.json`/`.py` data file wrongly marked 100755: `git update-index --chmod=+x
     ops/lib/ro_cases.json` -> `ops/lib/ro_cases.json (data, should be 100644, is 100755)`, EXIT=1; separately
     `git update-index --chmod=+x ops/lib/pins.py` -> `ops/lib/pins.py (data, should be 100644, is 100755)`,
     EXIT=1 — both caught, both restored, `git status --porcelain` clean after each. (d) No `ops/` at all: fresh
     `git init` scratch repo with only a copy of the script and an unrelated `README.md` -> `P-OPS-01: only 0
     files tracked under ops/ and .githooks/ (expected >= 17).`, EXIT=1 — does not pass vacuously. Scratch repo
     deleted afterward.

  Additionally re-derived (not in the numbered list but load-bearing for PASS): `touches:` accuracy —
  `git diff --name-only $(git merge-base main HEAD) HEAD -- . ':!queue/'` lists exactly
  `ops/lib/check-exec-bits ops/lib/junit_count.py ops/lib/pins.py ops/lib/queue.py ops/lib/ro_grammar.py`,
  matching the frontmatter `touches:` exactly; `git diff` on the four `.py` files against `main` shows only
  `old mode 100755` / `new mode 100644` lines, confirming zero content diff as claimed.

  Verification, re-run myself on the real `task/T-0036` tree (all exit 0):
  - `bash ops/lib/check-exec-bits` -> `P-OPS-01: 23 files, 20 required present, all modes correct`
  - `bash ops/check-pins` -> `PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux`
  - `bash ops/queue-check` -> `QUEUE OK (34 tasks)`
  - `bash ops/test` (services/api/node_modules already present in this worktree, no `npm ci` needed this run) ->
    `TESTS linux=50/50 ios=skipped failed=0 skipped=0` / `OK`

  Verdict: PASS. No BLOCKER or CRITICAL findings. One MAJOR (finding #3: REQUIRED will silently miss 3 more
  load-bearing files the moment task/T-0021 and task/T-0023 land — needs a follow-up task, not a fix to this
  diff, since the owner correctly could not add files that don't exist yet on this branch) and one MINOR
  (finding #2: `ro_grammar.py`'s self-documented CLI usage line implies bare invocation that no longer works,
  cosmetic/doc-only). Neither blocks this task: both are pre-existing shape of the repo (branches not yet
  merged; a docstring not touched by this diff) that this fix did not create and was not asked to close.
