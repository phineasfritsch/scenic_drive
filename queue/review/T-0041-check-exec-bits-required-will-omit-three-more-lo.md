---
id: T-0041
title: check-exec-bits REQUIRED will omit three more load-bearing ops/lib files once T-0021 and T-0023 merge
state: review
owner: agent/fixer-T0041
owner_session: d217767a
claimed_at: 2026-09-08T13:34:53Z
lease_expires_at: 2026-09-08T15:34:53Z
worktree: .worktrees/T-0041
branch: task/T-0041
exclusive: []
touches: [ops/lib/check-exec-bits, ops/lib/ro_grammar.py]
pins_affected: [P-OPS-01]
reviewer: agent/reviewer-25
depends_on: [T-0021, T-0023]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/lib/check-exec-bits` (P-OPS-01) carries a `REQUIRED` list of load-bearing files whose absence must fail
the pin. T-0036 added the `ops/lib/*.py` helpers to it, but three more load-bearing files exist only on
branches that had not merged when that work was done, so they are outside `REQUIRED` and will land silently:

- `ops/lib/classify-checks.py` (on `task/T-0021`) - the fail-closed check classifier `ops/merge` depends on.
  Deleting it makes `ops/merge` refuse everything, which is safe, but renaming it is not caught.
- `ops/lib/gh-stub-for-merge-tests` (on `task/T-0021`, also added on `task/T-0022`) - the deterministic `gh`
  double the merge-gate demonstrations run against. Without it those demonstrations cannot be reproduced.
- `ops/lib/check-failure-naming` (on `task/T-0023`) - P-OPS-02's whole assertion.

Confirmed by agent/reviewer-19 with `git ls-tree` on both branches while reviewing T-0036, and filed as a
MAJOR non-blocking finding there.

- Add all three to `REQUIRED` once T-0021 and T-0023 are merged (hence `depends_on`).
- Decide the mode for `classify-checks.py`: T-0036 established that `ops/lib/*.py` invoked only through an
  interpreter belongs in the 100644 data bucket. Check its call sites and follow that rule, or argue against it.
- `ops/lib/check-failure-naming` is a bash script invoked as `bash ops/lib/check-failure-naming`; confirm what
  mode the rule actually requires rather than assuming.
- Demonstrate red: `git rm --cached` each of the three in turn and show the pin passing before the change and
  failing after, naming the file.

Related: `ops/lib/ro_grammar.py:5-6`'s docstring documents `ro_grammar.py --self-test` with no interpreter
prefix - a bare invocation that no longer works now the file is 100644 (reviewer-19, MINOR). Fix the docstring
in the same pass.

### 2026-09-07 - a second, worse symptom of the same merge, found by rehearsing it

The original finding was that three load-bearing files will be missing from `REQUIRED` once T-0021 and
T-0023 land. Merging the whole backlog locally, in `queue/MERGE-ORDER.md`'s order, turned up something
sharper on the same file:

    P-OPS-01: wrong git file mode:
      ops/lib/classify-checks.py (data, should be 100644, is 100755)

`ops/lib/classify-checks.py` is committed 100755 on `task/T-0021`. T-0036 reclassified `ops/lib/*.py` into
the 100644 data bucket - correctly, they are only ever invoked as `"$PY" ops/lib/x.py` - and flipped the four
that existed on `main` at the time. `classify-checks.py` was not one of them, because it does not exist on
`main`; it only exists on T-0021.

So: **neither branch is wrong on its own, both pass their own gates, and the merged result fails P-OPS-01.**
`main` would have gone red on the first merge after both landed, with a failure that points at a file neither
task touched together.

That makes this a MERGE-TIME fix, not a follow-up: flipping the mode has to happen in the same window as
adding the three names to `REQUIRED`, and `queue/MERGE-ORDER.md` now names it as a step. Do both here:

    git update-index --chmod=-x ops/lib/classify-checks.py

and check the same trap for the other two files this task adds - `ops/lib/gh-stub-for-merge-tests` and
`ops/lib/check-failure-naming` are bash scripts, so 100755 is correct for them, but verify rather than assume:
the rehearsal only caught the `.py` because P-OPS-01 happens to encode the rule.

Demonstrate red by reproducing the rehearsal rather than by reasoning: merge `origin/task/T-0021` and
`origin/task/T-0036` into a scratch branch off `main` and run `bash ops/lib/check-exec-bits`.

## Log
- 2026-09-08T13:34:53Z claimed by agent/fixer-T0041; lease until 2026-09-08T15:34:53Z

- 2026-09-08T13:40:00Z TRIGGER: **both halves fired, not half.** T-0021 is on `main` as `26deb5a Merge pull
  request #17 from phineasfritsch/task/T-0021`, and `git merge-base --is-ancestor origin/task/T-0021
  origin/main` -> 0. T-0023 is on `main` as `b2507e5 Merge pull request #14 from phineasfritsch/task/T-0023`,
  and `git merge-base --is-ancestor b2507e5 origin/main` -> 0; the content this task actually depends on,
  `ops/lib/check-failure-naming`, arrived in `798059f T-0023: name the failures a summary-only suite reports,
  and pin that it stays true`, the only commit for that path in `git log origin/main -- ops/lib/check-failure-naming`.
  Recording one trap so the next agent is not misled: `git merge-base --is-ancestor origin/task/T-0023
  origin/main` -> **1**, which looks like a missing trigger and is not. The T-0023 *branch ref* has been advanced
  past its own merge - its tip `7ab73fb` carries merges of T-0038 and T-0042, and `git ls-tree origin/task/T-0023
  ops/lib/` still shows the pre-T-0036 `100755` modes on `pins.py`/`queue.py`/`ro_grammar.py`. Ancestry of a
  branch tip is the wrong question; ancestry of the merge commit and of the file's introducing commit is the
  right one. All three files this task adds are present on `origin/main` today.

- 2026-09-08T13:45:00Z **The addendum's merge-time chmod was already done, and not by me.** The 2026-09-07
  addendum instructs `git update-index --chmod=-x ops/lib/classify-checks.py` as a merge-time fix. That is
  already on `main`: `b86a62e 2026-09-07 T-0021: chmod -x ops/lib/classify-checks.py - the merge-time trap
  T-0041 predicted`. Same blob throughout (`1abc80e`), mode `100755` at `8ba0fed` (where T-0021 added the file)
  -> `100644` at `b86a62e` -> `100644` on `origin/main` now. T-0021 read this task file and closed the trap
  inside its own branch before merging, so **this PR changes no file modes at all** (`git diff` is content-only;
  `git ls-files -s ops/lib/` before and after is byte-identical).
  Reproduced the trap rather than reasoning about it, in the merged index state - staging T-0021's pre-fix mode
  against T-0036's classifier is exactly what the merge would have produced:

      $ git update-index --chmod=+x ops/lib/classify-checks.py
      $ bash ops/lib/check-exec-bits
      P-OPS-01: wrong git file mode:
        ops/lib/classify-checks.py (data, should be 100644, is 100755)
      EXIT=1
      $ git update-index --chmod=-x ops/lib/classify-checks.py   # -> 100644, EXIT=0

  Byte-for-byte the string the addendum predicted. The finding was real; it is closed; I am not claiming it.
  One correction to the addendum: it says "`queue/MERGE-ORDER.md` now names it as a step". That file does not
  exist in the tree - `git ls-files | grep -i merge-order` returns nothing, and T-0045 (which would create it)
  is still in `queue/claimed/`. Nothing to update there.

- 2026-09-08T13:50:00Z CLASSIFIED BY CONTENT, with the call site that decided each - not by name or extension:
  * `ops/lib/classify-checks.py` - shebang `#!/usr/bin/env python3`. **Sole call site `ops/merge:70`:**
    `if ! classified="$("$PY" ops/lib/classify-checks.py "$rollup" 2>&1)"; then` - passed as an argument to the
    interpreter, never `./ops/lib/classify-checks.py`. `git grep classify-checks` outside `queue/` and the file
    itself returns that one line and nothing else. DATA bucket, **100644**, which is T-0036's rule and is
    already its mode on `main`. Not changed by me.
  * `ops/lib/gh-stub-for-merge-tests` - shebang `#!/usr/bin/env bash`. **No call site anywhere in tracked
    source**: `git grep gh-stub` outside `queue/` and the file itself returns nothing. Its call site is a
    procedure recorded in task logs - it is copied to `<dir>/gh`, that dir is put on `PATH`, and it then runs as
    the program `gh` (`queue/done/T-0022-*.md:85` "copied to `<dir>/gh`, chmod +x"; T-0021's reviewer built a
    tracer that "delegates to a copy of the real stub"). Run as a program, not as an interpreter argument, so
    **100755** is right and is what it already is. Honest caveat: because the copy step re-applies `chmod +x`,
    the *committed* bit is not itself load-bearing on that path - what is load-bearing is that the file stays
    **tracked**, which is precisely what `REQUIRED` asserts and why it belongs there.
  * `ops/lib/check-failure-naming` - shebang `#!/usr/bin/env bash`. **Sole call site `pins/PINS.yaml:40`:**
    `assertion: "bash ops/lib/check-failure-naming"`. Checked the required mode rather than assuming it: the
    classifier's data test is `$4 ~ /\.(json|txt|md|py)$/ || $4 == "ops/api-url"`; this path matches neither, so
    the encoded rule puts it in the script bucket at **100755**, which is its mode today. No change.

- 2026-09-08T13:55:00Z RED, on the **unmodified** `ops/lib/check-exec-bits`, `git rm --cached` each in turn
  (index restored with `git reset -- <path>` each time, modes verified after every restore):

      baseline                                      P-OPS-01: 27 files, 20 required present, all modes correct  EXIT=0
      rm --cached ops/lib/classify-checks.py        P-OPS-01: 26 files, 20 required present, all modes correct  EXIT=0
      rm --cached ops/lib/gh-stub-for-merge-tests   P-OPS-01: 26 files, 20 required present, all modes correct  EXIT=0
      rm --cached ops/lib/check-failure-naming      P-OPS-01: 26 files, 20 required present, all modes correct  EXIT=0

  This is the defect: the pin reports "all modes correct" while three load-bearing files are untracked. The
  `MIN_FILES=17` floor does not save it (27 -> 26 is still over the floor), which is the whole reason the
  by-name `REQUIRED` list exists.

  GREEN, after adding the three names, same method:

      baseline                                      P-OPS-01: 27 files, 23 required present, all modes correct  EXIT=0
      rm --cached ops/lib/classify-checks.py        P-OPS-01: load-bearing script(s) not tracked: ops/lib/classify-checks.py       EXIT=1
      rm --cached ops/lib/gh-stub-for-merge-tests   P-OPS-01: load-bearing script(s) not tracked: ops/lib/gh-stub-for-merge-tests  EXIT=1
      rm --cached ops/lib/check-failure-naming      P-OPS-01: load-bearing script(s) not tracked: ops/lib/check-failure-naming     EXIT=1

  Also demonstrated the **rename** case, which is the one the brief says `ops/merge`'s fail-closed behaviour does
  not cover (deleting `classify-checks.py` makes `ops/merge` refuse everything, which is safe; renaming it is
  not): `git mv ops/lib/classify-checks.py ops/lib/classify_checks_renamed.py` ->
  `P-OPS-01: load-bearing script(s) not tracked: ops/lib/classify-checks.py`, EXIT=1; renamed back, mode still
  `100644`. `git status --short` after the whole sweep shows only this task's three intended files modified,
  and `git ls-files -s ops/lib/` is unchanged from `origin/main` on every mode.

- 2026-09-08T13:58:00Z FINDING, not fixed here - `REQUIRED` still omits `ops/lib/check-line-cap` and
  `ops/lib/check-exec-bits` itself. Same method on the pre-change file: `git rm --cached ops/lib/check-line-cap`
  -> `P-OPS-01: 26 files, 20 required present, all modes correct`, EXIT=0. `agent/reviewer-13` already flagged
  this class in `queue/done/T-0019-*.md` note (a). I deliberately did **not** add them: this task's title and
  brief name three specific files, and both of those two are additionally reachable through their own pin
  assertion failing loudly - `pins/PINS.yaml:22` and `:31` run them as `bash ops/lib/<x>`, which exits 127 when
  the file is gone, and `ops/lib/pins.py:86-87` treats any non-zero return as a pin failure. So the hole they
  leave is narrower than the three added here: it covers only the untracked-but-still-on-disk case, where the
  local checkout is green and everyone else's is broken. Real, but it deserves its own task rather than silent
  scope growth in this one.
  Disclosure on my own evidence: my first red sweep also included a `git rm --cached ops/lib/check-exec-bits`
  case, and its output was a bash syntax error at line 46 rather than a pin verdict. That is not a finding - I
  was editing that same file with another tool while the script was reading it. The data point is contaminated
  and I am not reporting it as evidence either way.

- 2026-09-08T14:00:00Z FINDING, not fixed here - the classifier decides the data bucket by **file extension**
  (`/\.(json|txt|md|py)$/`), which is the name-based classification this repo warns against elsewhere. By
  T-0036's own content argument ("invoked as an argument to an interpreter, so the exec bit does nothing"),
  `bash ops/lib/check-failure-naming` (`pins/PINS.yaml:40`), `bash ops/lib/check-line-cap` (`:22`) and
  `bash ops/lib/check-exec-bits` (`:31`) are the identical shape to `"$PY" ops/lib/x.py`, yet they sit in the
  100755 script bucket purely because they lack a `.py` suffix. I did not flip them: doing so would make
  P-OPS-01 fail against its own classifier, and asserting a mode the repo has not decided on is exactly the
  mistake `task/T-0100` avoided. Observation only.

- 2026-09-08T14:02:00Z MINOR carried over from `agent/reviewer-19`'s T-0036 finding #2: `ops/lib/ro_grammar.py`'s
  module docstring documented its CLI as a bare `ro_grammar.py --self-test`, which stopped working when T-0036
  moved the file to 100644. Rewritten to `python3 ops/lib/ro_grammar.py --self-test` / `python3
  ops/lib/ro_grammar.py "<sql>"`, matching the real call sites at `ops/prod-read:16-17`, with one line saying
  why the bare form fails. Docstring-only; verified the module still runs: `python3 ops/lib/ro_grammar.py
  --self-test` -> `RO-GRAMMAR OK 26 cases`, exit 0.

- 2026-09-08T14:03:00Z `touches:` widened from `[ops/lib/check-exec-bits]` to `[ops/lib/check-exec-bits,
  ops/lib/ro_grammar.py]` - the Brief's last paragraph asks for the `ro_grammar.py` docstring fix "in the same
  pass", and T-0036's reviewer explicitly deferred it because that task's `touches:` did not cover the file.
  `pins_affected:` set to `[P-OPS-01]`, which was empty and should not have been for a task that edits that
  pin's whole assertion. No `exclusive:` file is involved; `Package.swift` was not touched.

- 2026-09-08T14:05:00Z FINDING, not fixed here - `ops/lib/classify-checks.py:29` has the *same* defect the
  `ro_grammar.py` docstring had: its usage string is `usage: classify-checks.py '<rollup json>'`, a bare
  invocation that cannot work now the file is committed 100644. Found while confirming the call-site claims
  above. Not fixed: `touches:` covers `ops/lib/ro_grammar.py` because the Brief names it, and widening a second
  time for a nit the Brief does not name is scope growth. One line, whoever takes it next:
  `usage: python3 ops/lib/classify-checks.py '<rollup json>'`.
  Also confirmed while checking: the `gh-stub-for-merge-tests` "no tracked call site" claim holds against CI
  too - `git grep -E "classify-checks|gh-stub-for-merge-tests|check-failure-naming" -- .github ops services`
  returns only `ops/merge:70`, the stub's own self-references, and this pin's own list. `.github/workflows/`
  contains one file (`linux-core.yml`) and it names none of the three.

- 2026-09-08T14:20:00Z VERIFY, both commands in `verify:`, run in `.worktrees/T-0041` on the committed tree:
  * `bash ops/check-pins` -> `PINS ok=11 skipped=0 pending=2 expired=0 failed=0 tier=linux`, exit 0.
  * `bash ops/test` -> `TESTS linux=119/76 ios=skipped failed=0 skipped=0` / `OK`, exit 0.
    `services/api/node_modules` was absent in this fresh worktree, the known artifact documented in
    `queue/done/T-0015-*.md` and again in T-0021's log; `npm ci` in `services/api` (85 packages, 0
    vulnerabilities) before the run, which is environment setup and not a diff change.
  * `bash -n ops/lib/check-exec-bits` -> 0. `python3 -c "ast.parse(...)"` on `ro_grammar.py` -> 0.
    `python3 ops/lib/ro_grammar.py --self-test` -> `RO-GRAMMAR OK 26 cases`, exit 0.
  * Modes unchanged end to end: `git ls-files -s ops/lib/` matches `origin/main` on every entry, and the two
    committed files kept theirs (`ops/lib/check-exec-bits` 100755, `ops/lib/ro_grammar.py` 100644).
  * No CRLF in any staged file; `git status --short` clean at handoff.

- 2026-09-08T14:22:00Z PR https://github.com/phineasfritsch/scenic_drive/pull/72, base `main` (branched from
  `origin/main` at `288ebf6`, never from another task branch - see T-0113). reviewer set to
  `agent/reviewer-25`; moved to `review/` with `git mv` so no stale copy is left in `claimed/`. Not transitioned
  past `review/`.
  For the reviewer: the two things most worth attacking are (1) whether `ops/lib/gh-stub-for-merge-tests`
  belongs in `REQUIRED` at all, given it has no tracked call site and its only consumers are procedures written
  down in task logs - I argued tracked-ness is the load-bearing property, but that is the weakest of the three;
  and (2) the two omissions I reported and did not fix (`check-line-cap`, `check-exec-bits` itself), in case you
  think they should have been in scope after all.
