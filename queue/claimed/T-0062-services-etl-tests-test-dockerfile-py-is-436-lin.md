---
id: T-0062
title: services/etl/tests/test_dockerfile.py is 436 lines on task/T-0046
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:08:19Z
lease_expires_at: 2026-09-08T08:08:19Z
worktree: wt/T-0062
branch: task/T-0062
exclusive: []
touches: [services/etl/tests/, ops/lib/check-line-cap]
pins_affected: []
reviewer: null
depends_on: [T-0046, T-0058]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`services/etl/tests/test_dockerfile.py` is **436 lines** on `task/T-0046`, against the 300-line cap. It was
125 lines on `task/T-0038` and grew across T-0046's four review rounds of pip-parser work.

Nothing reported it, because `ops/lib/check-line-cap` globbed Swift only. T-0058 extends the cap to Python and
TypeScript - and the merge rehearsal that found this file is the reason T-0058 carries an exemption for it:
without one, the first merge of the Dockerfile chain after T-0058 turns `main` red on a file that was over the
cap long before either task existed.

So this is not a regression and not T-0058's fault; it is a debt the new check made visible, which is what the
check is for. The exemption is the deliberate, auditable way to carry it for exactly as long as it takes to
land this task, and `check-line-cap` refuses an exemption whose file has dropped back under the cap, so it
cannot quietly become permanent.

- Split it along whatever seams the file already has. T-0046's log describes distinct concerns - the pip
  destination-flag whitelist, the PEP 508 marker segmentation, the shlex tokenizer, and the Dockerfile
  parsing itself - which is a good sign the file is several tests wearing one filename.
- Do NOT delete tests to get under the number. The file is long because T-0046 was attacked four times and
  each round added real cases; every one of them is load-bearing and a reviewer should refuse any diff that
  drops coverage to satisfy a line count.
- When it is under 300, DELETE the exemption entry from `ops/lib/check-line-cap`. Leaving it is itself a
  failure the check reports: "exemption(s) no longer needed - the file is under the cap, so delete the entry".
- Verify with the merge rehearsal, not just on the branch: merge `task/T-0046` and `task/T-0058` into a
  scratch branch and run `bash ops/lib/check-line-cap`. That combination is the only place the problem exists.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a full merge rehearsal - 30 branches merged in dependency order
  into a throwaway, gates run after each. This file is invisible on every branch individually and only appears
  when the Dockerfile chain meets T-0058.
- 2026-09-08T02:08:19Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:08:19Z

- 2026-09-08 agent/claude-opus-5 — split, exemption removed, verified on the branch combination that is the
  only place the problem exists.

  **The seam was already there.** The file was two things wearing one filename: pip's `install` argument
  grammar, which knows nothing about Docker, and a set of assertions about this repo's image. Lines 36-248
  were the parser, entire and self-contained. They moved verbatim into
  `services/etl/tests/pip_install_grammar.py`; `test_dockerfile.py` imports the two entry points it uses.

        services/etl/tests/test_dockerfile.py       436 -> 226 lines
        services/etl/tests/pip_install_grammar.py     0 -> 234 lines

  The module is deliberately NOT named `test_*`, so pytest does not collect it, and it imports nothing from
  the Dockerfile side. `tests/` is already a package and `pyproject.toml` sets `pythonpath = ["."]`, so
  `from tests.pip_install_grammar import ...` needed no configuration change.

  **No test was deleted, and this was proved rather than asserted.** The brief is explicit that the file is
  long because T-0046 was attacked four times and every case is load-bearing. Collected node ids before and
  after, sorted and diffed:

        before: 46   after: 46
        diff -> no output.  IDENTICAL TEST SET (same node ids, same count)

  `46 passed in 3.56s` both sides. Every docstring moved with its function: they carry the history of four
  review rounds - the hallucinated `--build` flag that abbreviated `--build-constraint` into a real bypass,
  the short-flag bundling that resolves through the FIRST value-taking letter, the PEP 508 marker torn apart
  by splitting on an unquoted `;` - and each is the reason its rule exists, so losing them would lose the
  argument for the code.

  **Red then green on the exemption, which is the second half of the task.** With the split done and the
  entry still in `ops/lib/check-line-cap`:

        P-SRC-02: exemption(s) no longer needed - the file is under the cap, so delete the entry:
          services/etl/tests/test_dockerfile.py (226 lines, exempt for T-0062)
        exit 1

  That exit code was checked directly (`bash ops/lib/check-line-cap >/dev/null 2>&1; echo $?`) and not
  through a pipe: `... | tail -8; echo $?` reports **tail's** status, which is 0, and would have read as a
  message printed by a passing check. After deleting the entry (transcript CORRECTED 2026-09-08, see
  "The evidence above was stale" below - it read 28):

        P-SRC-02: 10 Swift files, 29 source files under the cap, 1 exempt
        exit 0

  The one remaining exemption is `ops/lib/queue.py` for T-0059, untouched.

  **Verified on the merge, not just on the branch**, as the brief requires. This worktree is
  `task/T-0046` + `origin/task/T-0058` + `origin/main` merged - T-0046 carries the 436-line file, T-0058
  carries the Python cap and the exemption, and neither branch alone can see the problem. Both merges were
  clean. Gates on that tree:

        pytest (services/etl)   46 passed
        ops/queue-check         QUEUE OK (71 tasks)
        check-line-cap          P-SRC-02: 10 Swift files, 29 source files under the cap, 1 exempt
                                ^ CORRECTED 2026-09-08; this line read 28 and the check had not seen the
                                  new file. See "The evidence above was stale" below and Re-run 2.
        check-exec-bits         P-OPS-01: 25 files, 15 required present, all modes correct

  Handing to review. The reviewer should re-run the node-id diff rather than trusting the count: a count is
  equally satisfied by deleting one test and adding another, which is the shape this task was warned about.

- 2026-09-08 agent/claude-opus-5 — two MEDIUM review findings, both real. Fixed. Finding 1 is the evidence
  above; finding 2 is a hole in `check-line-cap` that the brief's own argument leaned on.

  **The evidence above was stale, and it was the piece the brief demanded most.** The two `check-line-cap`
  transcripts in the entry above - the one after deleting the exemption, and the one in the merge table,
  which sits under the heading "Verified on the merge, not just on the branch, as the brief requires" - both
  read `28 source files under the cap`. The committed tree yields **29**. The cause: `check-line-cap`
  enumerates with `git ls-files`, not `find`, so an **untracked** file is invisible to it, and both
  transcripts were captured while `services/etl/tests/pip_install_grammar.py` - the 234-line file this task
  created - was still unstaged. So the cap check recorded as proof that the split satisfies the cap had
  never examined the file the split produced. It could not have reported a violation in that file, whatever
  its length. The reviewer reproduced the old number exactly by `git rm --cached
  services/etl/tests/pip_install_grammar.py`, which is what pins the cause to staging rather than to
  anything about the split. Confirmed independently from the trees: `git ls-tree -r` on the parent commit
  `11d2788` yields 28 matching source files, and on the split commit `b4b0481` yields 29.

  Saying this plainly rather than editing the number and moving on: the failure was not an arithmetic slip,
  it was running the check at a moment when it structurally could not see the work, and then filing the
  result as verification. Both stale lines are corrected in place to 29 and both carry a marker pointing
  here, so the diff is legible as a correction rather than as a tidy-up. The throwaway merge branch behind
  the merge table was never preserved as a commit, so that line is restated from the re-run below rather
  than re-measured on the identical tree; the other three lines in that table are the originals and were
  not challenged. The re-run merge is against a much newer `origin/main`, so that substitution is only
  legitimate if the newer main cannot move the count, and it was checked rather than assumed:

        $ git diff --name-only $(git merge-base HEAD origin/main) origin/main | grep -v '^queue/'
        (no output - origin/main adds nothing outside queue/ since the merge-base)
        $ diff <(git ls-tree -r --name-only b4b0481 | grep -E '\.(swift|py|ts)$' | grep -v /node_modules/ | sort) \
               <(git ls-tree -r --name-only 0786049 | grep -E '\.(swift|py|ts)$' | grep -v /node_modules/ | sort)
        (no output - IDENTICAL capped file set on the split commit and on the merge)

  **Re-run 1 - the committed tree.** `task/T-0062` at `18cbc9a`. The working-tree state is shown rather
  than asserted, because an unshown working tree is exactly what went wrong the first time - the one
  modified path is this log file, a `.md`, which is not in the capped set and cannot move the number:

        $ git rev-parse --short HEAD
        18cbc9a
        $ git status --short
         M queue/claimed/T-0062-services-etl-tests-test-dockerfile-py-is-436-lin.md
        $ bash ops/lib/check-line-cap
        P-SRC-02: 10 Swift files, 29 source files under the cap, 1 exempt
        exit 0
        $ git ls-files '*.swift' '*.py' '*.ts' | grep -v '/node_modules/' | wc -l
        29

  And the same number read straight out of the commit object, with no working tree involved at all, which
  is the form that cannot be fooled by staging:

        $ git ls-tree -r --name-only 18cbc9a | grep -E '\.(swift|py|ts)$' | grep -v /node_modules/ | wc -l
        29

  **Re-run 2 - the merge, which is what the brief actually asked for.** `task/T-0062` (`18cbc9a`) merged
  with `origin/main` (`7ac0ae0`) on a throwaway branch, merge commit `0786049`, clean merge. Recreate with
  `git checkout -b scratch task/T-0062 && git merge origin/main`; the merge SHA will differ, the tree will
  not:

        $ bash ops/lib/check-line-cap
        P-SRC-02: 10 Swift files, 29 source files under the cap, 1 exempt
        exit 0
        $ git ls-files '*.swift' '*.py' '*.ts' | grep -v '/node_modules/' | wc -l
        29
        $ bash ops/lib/check-exec-bits
        P-OPS-01: 25 files, 15 required present, all modes correct
        $ bash ops/queue-check
        QUEUE OK (87 tasks)
        $ cd services/etl && python -m pytest
        46 passed in 3.46s

  **Finding 2: the exemption rule the brief leans on has a hole, and the brief states the hole as a
  guarantee.** The brief argues the exemption "cannot quietly become permanent" because "check-line-cap
  refuses an exemption whose file has dropped back under the cap". That rule only fires for a path still
  present in the `capped` array: the cap loop walks `capped` and looks each path up in `EXEMPT`, never the
  other way round. An exemption naming a path that was RENAMED or DELETED is visited by nothing, so it is
  carried forever in silence - and is still counted in the reassuring `N exempt` tally on the last line.
  The one shape the exemption mechanism most needs to catch, a file that left the tree, was the one shape
  that could never expire.

  RED - the defect, on the check as it stood at `b4b0481` (taken from the commit, so it stays reproducible
  after the fix), with `["services/etl/tests/does_not_exist_anymore.py"]="T-0062"` added to the map:

        $ git show b4b0481:ops/lib/check-line-cap > .artifacts/clc-prefix
        $ awk -v e='  ["services/etl/tests/does_not_exist_anymore.py"]="T-0062"' \
              '{print} /^declare -A EXEMPT=\(/{print e}' .artifacts/clc-prefix > .artifacts/clc-prefix-ghost
        $ bash .artifacts/clc-prefix-ghost; echo "exit $?"
        P-SRC-02: 10 Swift files, 29 source files under the cap, 2 exempt
        exit 0

  Exit 0, and it prints `2 exempt` while one of the two names nothing at all.

  GREEN - `ops/lib/check-line-cap` now collects `capped` into a `CAPPED_SET` and walks `EXEMPT`'s KEYS
  against it, so an entry the cap loop never visits is refused. `git ls-files --error-unmatch` then
  separates the two causes, because they have different fixes. Same one-line injection, against the FIXED
  check, once per shape:

        $ # ["services/etl/tests/does_not_exist_anymore.py"]="T-0062"   - path is not tracked
        P-SRC-02: exemption(s) the cap never examines - nothing can make these expire:
          services/etl/tests/does_not_exist_anymore.py (exempt for T-0062) - not a tracked file; it was renamed or deleted
          Point the entry at the file's current path, or delete it.
        exit 1

        $ # ["CLAUDE.md"]="T-0062"                                      - tracked, but the cap never reads it
        P-SRC-02: exemption(s) the cap never examines - nothing can make these expire:
          CLAUDE.md (exempt for T-0062) - tracked, but outside the capped set; the cap never reads it
          Point the entry at the file's current path, or delete it.
        exit 1

  The second shape is the same bug wearing different clothes: a `.md` or a path under `node_modules/` is
  never in `capped` either, so no edit to that file could ever trip the stale rule.

  And the pre-existing under-the-cap rule still fires, unchanged - re-demonstrated red on the FIXED check
  so that the new rule is shown not to shadow or replace it:

        $ # ["services/etl/tests/test_dockerfile.py"]="T-0062"          - tracked, capped, now 226 lines
        P-SRC-02: exemption(s) no longer needed - the file is under the cap, so delete the entry:
          services/etl/tests/test_dockerfile.py (226 lines, exempt for T-0062)
        exit 1

  Anchored on `capped` - the same `git ls-files` set the cap loop walks - deliberately, and not on the
  working tree. A file present on disk but untracked is invisible to this check either way, which is
  exactly the mechanism behind finding 1; an exemption naming one would be just as dead.

  Each of the three transcripts above is a COPY of `ops/lib/check-line-cap` with that one extra line
  inserted directly after `declare -A EXEMPT=(`, written into the gitignored `.artifacts/` and run from
  there - so no bad exemption is ever committed in order to demonstrate the refusal, and the real check is
  never edited while a copy of it is running (bash reads a script incrementally, and editing one mid-run
  has broken this repo before). To reproduce any of them, substitute the path from the `#` line:

        awk -v e='  ["PATH/HERE"]="T-0062"' \
            '{print} /^declare -A EXEMPT=\(/{print e}' \
            ops/lib/check-line-cap > .artifacts/clc
        bash .artifacts/clc; echo "exit $?"

  All three were re-run through exactly that recipe after it was written down, rather than the recipe being
  reconstructed afterwards from memory of a different command.

  Gates on the branch after the fix:

        $ bash ops/test
        TESTS linux=96/76 ios=skipped failed=0 skipped=0
        OK
        $ bash ops/check-pins
        PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux

  `ops/test` first came back `FAIL: services/api exists but vitest produced no report` in this worktree
  because `services/api/node_modules` had never been installed here. That is the reporter-missing guard
  doing its job, not a regression; `npm ci` in `services/api`, then the run above. Recording it because a
  missing report is precisely the shape `ops/test` refuses to score as zero.
