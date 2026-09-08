---
id: T-0103
title: no check looks inside a worktree, so 662 lines lived untracked with no branch on origin
state: done
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T09:21:19Z
lease_expires_at: 2026-09-08T12:21:19Z
worktree: null
branch: task/T-0103
exclusive: []
touches: [ops/sane, ops/agent-preflight, ops/lib/check-worktrees, ops/lib/check-worktrees-demo]
pins_affected: []
reviewer: agent/reviewer-final-pr65
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**662 lines of the corpus emitter existed only as untracked files in one worktree on one machine, and
`origin/task/T-0030` did not exist at all.** A `git clean`, a `git worktree remove --force`, or a reinstall
would have deleted them, and nothing in this repository would have reported anything missing.

Found on 2026-09-08 by a one-off sweep, not by a check:

    wt/T-0030   ?? services/etl/etl/schema.py         246 lines
                ?? services/etl/etl/geom.py           147
                ?? services/etl/etl/segmenter.py      119
                ?? services/etl/etl/contentdigest.py   91
                ?? services/etl/etl/segid.py           59
                origin/task/T-0030: does not exist

All five parse. They carry the kind of docstring this repo asks for (`segid.py`: *"Byte level, not string
level... big-endian fixed-width bytes make it depend on nothing about the build host"*). This was real work,
mid-flight, and the only copy was in a directory.

**Why nothing saw it.** `ops/sane` exit 2 checks "repo dirty" — of the checkout it is run in. Every other
gate reads the tree it is run in, or reads remote refs. A worktree the agent is not currently standing in is
outside all of them, and there are 30+ of them. The same sweep found four other worktrees with unpushed
commits and one (`wt/T-0085`) checked out on a leftover `demo/*` branch, so an agent returning to it would
have committed to the demo branch rather than to its task.

**The fleet rule this violates is already written down.** `queue/README.md` step 8 says a demo worktree is
created and then removed; CLAUDE.md says work happens in a worktree per task. Neither is checked, and the
queue's whole safety argument — *"claim = `git mv` + push, git is the lock"* — assumes work reaches the
remote. Work that never leaves a directory is invisible to the lease sweeper, to `queue-check`, to the
rehearsal, and to a human reading GitHub. [[T-0082]]'s sweeper would even read such a task as **abandoned**
now that it is keyed on commits ahead of main: `task/T-0030` has none, because they were never committed.

Do:

1. `ops/sane` gains a check over **every** worktree `git worktree list` reports, not just this one:
   untracked files under a path in that task's `touches:`, uncommitted modifications, commits not on
   `origin`, and a HEAD that is not the branch the task file names. Report the worktree, the branch, and the
   counts.
2. `ops/agent-preflight` runs it at session start, because that is the moment somebody can still act on it —
   CLAUDE.md already says to run preflight first thing.
3. Distinguish the three states in the OUTPUT, because they need different actions: *untracked* (may be
   scratch, may be 662 lines of emitter), *uncommitted changes to tracked files*, *committed but unpushed*.
   Do not collapse them into "dirty".
4. Ignore what is genuinely scratch — `.artifacts/` is gitignored and is where this repo is told to put
   scratch — but **never** ignore a path inside the task's `touches:`. That is the discriminator: an
   untracked file under a path the task declared it would edit is the task's own work.
5. Vacuity guard: fail if it inspected zero worktrees. `git worktree list` always reports at least the main
   checkout, so zero means the query failed, and "no problems found" would be a lie.

**Red demo:** create a worktree, drop an untracked file under its task's `touches:`, run the check, see it
named. Then commit and push it and see the check go quiet.

**Do not** make this a `git clean` helper or offer to delete anything. The failure mode here is deletion;
the fix is visibility.

## Log
- 2026-09-08T09:21:19Z claimed by agent/claude-opus-5; lease until 2026-09-08T12:21:19Z

- 2026-09-08 — **`ops/lib/check-worktrees`, wired into `ops/sane` (exit 10) and `ops/agent-preflight`.**

  **It found the motivating shape on its first run**, which is the only evidence that matters here:

        T-0103   unpushed:[no origin/task/T-0103 at all]
        _dupprobe   unpushed:[no origin/tmp/dupprobe at all]

  That is exactly `wt/T-0030`'s state — a branch whose work exists on one disk only — reported by a check
  rather than by a hand sweep.

  **The design decision, and it was forced by measurement rather than taste.** At 67 worktrees, under four
  concurrent agents:

        three git calls per worktree   real 11m55s   user 0m22s   sys 2m14s
        one   git call  per worktree   real  6m55s   user 0m14s   sys 1m19s
        ZERO  git calls per worktree   real  1m57s   user 0m01s   sys 0m11s   <- the default

  Almost none of it was ever computation. **A check that takes minutes is a check nobody runs, and a check
  nobody runs is precisely the hole this task was filed to close** — so the first two versions were not
  slow implementations of the right check, they were the wrong check. The default had to leave the
  per-worktree business entirely.

  It could, because the catastrophic case needs no per-worktree call: `origin/task/T-0030` simply did not
  exist, and that fact is already in `git worktree list --porcelain` (which prints each HEAD sha) plus one
  `for-each-ref`. `--deep` buys untracked-in-`touches:` and modified files at one `git status` each, and
  says so in its own output rather than letting a fast run be mistaken for a thorough one.

  Three states are reported separately and never collapsed into "dirty", because they need different
  actions: *untracked inside touches:*, *modified*, *committed but not on origin*. Untracked files are
  judged only against the task's declared `touches:` — `.artifacts/` is gitignored and is where this repo
  tells agents to put scratch, so a file under a path the task said it would edit is the task's own work.

  **Vacuity floor:** `git worktree list` always reports at least this checkout, so parsing zero means the
  parser is wrong, and it exits 2 rather than reporting no problems.

- 2026-09-08 — **`ops/agent-preflight` was reporting the repository as misconfigured in every session, and
  it was wrong.**

        $ git config --get core.hooksPath
        C:\Users\phineasf\Documents\GitHub\scenic_drive\.githooks
        $ bash ops/agent-preflight | grep hooks
        hooksPath    NOT SET - run: git config core.hooksPath .githooks

  It *was* set. The check compared the value to the literal string `.githooks`, so an ABSOLUTE value failed
  the string test — and preflight, the command `CLAUDE.md` says to run **first thing in every session**, had
  been exiting non-zero on every worktree with a message that is simply false. A check that always fails is
  a check nobody reads, and that is why the hazard underneath it went unseen for so long.

  The hazard, found by the reviewer of PR #47: git resolves a **relative** `core.hooksPath` against the top
  of the working tree, so `.githooks` is per-worktree while an absolute path is not. With the absolute value
  pointing at the main checkout, **every worktree ran main's hooks** — a branch could not exercise its own
  `.githooks` change by committing, and a hook red/green demonstration done in a worktree tested main's copy.
  The reviewer proved it the only way that counts: the commit PR #47's log records as REFUSED is accepted,
  with HEAD advancing.

  The check now resolves both paths and reports the three states apart:

        hooksPath    .githooks (relative - resolves to THIS worktree, which is what you want)

  **And the config itself was corrected mid-session, by another agent, while four were committing.**
  `.git/config` changed at 03:02 local. It is the right change and preflight is what verifies it, but it is
  repo-wide, out of band, and outside every `touches:` — the pre-commit hook cannot police git config, so
  nothing would have reported it. Verified after the fact rather than trusted:

        $ git rev-parse --git-path hooks     # in three different worktrees
        .githooks        .githooks        .githooks       (and the file exists in each)

        $ bash ops/lib/check-exec-bits
        P-OPS-01: 24 files, 15 required present, all modes correct

- 2026-09-08 — **PR #65 review FAIL closed. Four findings; three fixed, one refuted in part. Every fix is
  demonstrated red-then-green, and the reds are re-runnable: `bash ops/lib/check-worktrees-demo`.**

  `touches:` widened by one path, `ops/lib/check-worktrees-demo`, and only that. It is the red demo the
  brief asked for, turned into a file, for the reason given under F3.

  **F1 — `ops/sane` printed a count it invented. FIXED.** Reproduced first:

        $ bash ops/sane                                   # exit 10
        worktrees FAIL   6 worktree(s) hold work that is not on origin
                    _dupprobe                  unpushed:[no origin/tmp/dupprobe at all]
                    _t0075probe                unpushed:[no origin/tmp/t0075-probe at all]
                    T-0104                     unpushed:[no origin/task/T-0104 at all]
                  WORKTREES: 3 of 75 need attention. ...
        $ grep -c '^  ' <that check-worktrees output>
        6

  Three worktrees, three summary continuation lines, `grep -c '^  '` counts six. `check-worktrees` now
  emits its own numbers on one machine-readable line and `ops/sane` reads that line; nothing greps the
  prose. If the line is missing, `ops/sane` says so and refuses to print a number at all.

        $ bash ops/sane                                   # exit 10
        worktrees FAIL   15 of 80 need attention - untracked:4 modified:11 unpushed:7 wrong-branch:0 missing:0
                  ...
                  WORKTREES-SUMMARY inspected=80 statted=80 touches=74 problems=15 untracked=4 \
                    modified=11 unpushed=7 branch=0 missing=0 mode=full

  The wording is fixed with it: the reviewer was right that "hold work that is not on origin" was applied
  to worktrees that were only `modified:`. Each state now carries its own count.

  **F1, second half — the block sat above the production section and stole its exit code. FIXED**, and this
  one is a genuine red/green because the old file is still runnable:

        $ export API_URL=http://127.0.0.1:9      # dead backend (7) AND stranded worktrees (10) at once
        $ bash .artifacts/sane-old --prod        # ops/sane at 81ad441
        worktrees FAIL   11 worktree(s) hold work that is not on origin
        backend   FAIL   http://127.0.0.1:9/__health -> unreachable
        SANE FAIL exit=10                                          <- contradicts its own header
        $ bash ops/sane --prod
        backend   FAIL   http://127.0.0.1:9/__health -> unreachable
        worktrees FAIL   8 of 79 need attention - untracked:2 modified:4 unpushed:5 ...
        SANE FAIL exit=7                                           <- matches the table

  That run also re-proves F1's first half from the other side: the old file said **11** where the new one
  says **8**, on the same fleet, in the same minute.

  **F2 — two of the four states were behind a flag nothing invoked. FIXED, and the reason given for it was
  wrong.** The defence was cost. The cost was never git's:

        74 basename subprocesses                33.7s     <- of the 57s the "zero git calls" pass took
        74 "${wt##*/}" parameter expansions      0.002s
        74 git status, serial                   28.5s
        74 git status, --jobs=8                 14.9s
        74 git status, --jobs=16                 8.4s

  A fork costs ~0.45s on this box, so the file was paying a third of a minute to compute basenames. Every
  per-worktree subprocess is gone except the one `git status`, which now runs 16 at a time and carries
  `--no-optional-locks` — without it, reading 79 worktrees **rewrites 79 other agents' indexes**, and
  `ops/sane` promises it never mutates anything. All four states are the default; `--fast` is the opt-out.
  `ops/sane` runs the full pass. Measured under four concurrent agents at 79-80 worktrees: full 1m34s,
  `--fast` 43s, against the reviewer's 19m40s for the old `--deep`.

  What that buys, on the first run of the fixed version, is the shape the brief was filed for and the old
  default could not see:

        T-0063   untracked-in-touches: ops/lib/check-review-remedy modified:3
        T-0097   untracked-in-touches: ops/merge-selftest modified:2
        T-0117   untracked-in-touches: Sources/ScenicKit/Scoring/ Tests/ScenicKitTests/RouteScoreTests.swift
                 unpushed:[no origin/task/T-0117 at all]

  Three worktrees holding uncommitted work under a path their own task declared. `T-0063` and `T-0097` are
  invisible to the old default: both branches ARE on origin.

  **F3 — the red demo was not performed. FIXED, and made re-runnable.** The reviewer is right that a red
  seen once in a log is weak evidence and that `branch:[...]` and the vacuity floor had never been seen red
  by anyone. They cannot be demonstrated on the live fleet: it is 80 directories owned by other agents, a
  red there cannot be turned green by me, and "a T-0085 directory checked out on demo/T-0085-mrg" does not
  occur on demand. So `ops/lib/check-worktrees-demo` builds a fixture — bare origin, main checkout, one
  linked worktree, a queue file with a real `touches:` list — and drives every state red and then green:

        $ bash ops/lib/check-worktrees-demo                                       # exit 0
        ok    unpushed  RED  (no origin/task/T-9901 at all)  exit=1
        ok    unpushed  green (branch pushed)                exit=0
        ok    untracked RED  (demo/lost.py under touches:)   exit=1     <- the brief's demo, verbatim
        ok      and did NOT report notes-not-in-touches.txt
        ok    untracked green (committed and pushed)         exit=0
        ok    modified  RED  (1 tracked file changed)        exit=1
        ok    modified  green (change reverted)              exit=0
        ok    branch    RED  (T-9901 dir on demo/T-9901-mrg) exit=1
        ok    branch    green (back on task/T-9901)          exit=0
        ok    floor     RED  (parser returned 1 of 2)        exit=2
        ok    floor     green (parser intact)                exit=0
        ok    touches   RED  (no task file -> 0 examined)    exit=2
        ok    statted   RED  (every status call failed)      exit=2
        DEMO: 19 ok, 0 failed

  **F3, second half — the floor counted the wrong population. FIXED.** `n -lt 1` only caught a parse that
  returned nothing; a parser that returned 1 of 79 exited 0. The floor now counts the population from git's
  own on-disk metadata (`$GIT_COMMON_DIR/worktrees`, one directory per linked worktree) rather than from a
  reparse of the listing it is about to trust. Same fixture, same crippled parser, old file and new:

        $ bash cw-old-crippled          # ops/lib/check-worktrees at 81ad441, parser truncated to 1 of 2
        exit=0
          | WORKTREES: 1 inspected, every branch is on origin and on the right branch.
        $ bash cw-new-crippled          # identical truncation
        exit=2
          | check-worktrees: parsed 1 worktrees while .git/worktrees held a steady 1 (+1 main checkout).
          |   The listing and git's own metadata disagree and nothing moved between the two reads, so this
          |   pass did not see the fleet ...

  Two more floors, on the two populations the other halves actually examine, because "files present" is not
  "files examined": `statted` (worktrees whose `git status` succeeded) and `touches` (worktrees that yielded
  a declared path). Either at zero is exit 2, not a green. The `touches` floor earned itself immediately —
  it went red on the first fixture run for a real reason: the fixture inherited `core.autocrlf=true`, so
  every task file came back with CRLF and `touches: [...]` matched nothing. Without the floor that would
  have been a silent all-clear from a check examining zero worktrees. The parser now strips the CR.

  A fleet that MOVES between the two metadata reads is not a broken parser, and saying so is the difference
  between a floor and a flake: five reads, and a listing consistent with either snapshot is accepted. Only
  a disagreement on a fleet that did not move is red.

  **F4 — preflight failed for reasons no session can act on. FIXED.** Reproduced: a spotless `T-0103`
  checkout, `PREFLIGHT FAIL` exit 1, because `_dupprobe`, `_t0075probe` and `T-0104` are other agents'
  probes. The fleet sweep now prints and does not vote. The reviewer's own test is the proof, because their
  point was that the exit code had stopped distinguishing the two hooksPath states:

        ### 1. as configured today (fleet has 15 problems)
        exit=0    hooksPath  .githooks (relative - resolves to THIS worktree, which is what you want)
                  worktrees  FYI ... (does not fail preflight; ops/sane exit 10 is the gate)
        ### 2. hooksPath forced ABSOLUTE, pointing at the MAIN checkout          <- the hazard
        exit=1    ^ ABSOLUTE and NOT this worktree: hooks run from there ...
        ### 3. hooksPath forced ABSOLUTE, naming THIS worktree                   <- benign
        exit=0    (absolute, but it is this worktree's own .githooks)

  1 / 0 / 0, where the reviewer measured 1 / 1. Preflight's exit code is again about what this session can
  fix; `ops/sane` exit 10 is the gate for what it cannot. `.github/workflows/linux-core.yml:59` therefore
  keeps gating on the toolchain rather than on 79 strangers' directories. Preflight runs `--fast` for the
  same reason it now reports rather than votes: it is the per-session command, `ops/sane` is the audit.

  **REFUTED, in part — "roughly 6 seconds per worktree".** The header sentence the reviewer measured
  against (7½ minutes predicted, 19m40s observed) was wrong in both directions and is gone: a `git status`
  here is 0.38s, and the missing 19 minutes were fork overhead the sentence never mentioned. The reviewer's
  19m40s stands; the file's explanation of it did not.

  **Verify.**

        $ bash ops/check-pins           0    PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        $ bash ops/lib/check-exec-bits  0    P-OPS-01: 25 files, 15 required present, all modes correct
        $ bash ops/queue-check          0    QUEUE OK (93 tasks)
        $ bash ops/test                 1    FAIL: services/api exists but vitest produced no report
        $ npm ci --prefix services/api  0    added 85 packages in 9s      # node_modules/ is gitignored
        $ bash ops/test                 0    TESTS linux=50/50 ios=skipped failed=0 skipped=0

  The first `ops/test` red is this worktree missing `services/api/node_modules`, not this branch: the main
  checkout is missing it too, and nothing here touches `services/api`. Named rather than quietly installed
  around, because `ops/test` failing for an environment reason in a fresh worktree is worth somebody's
  attention.

  `bash ops/sane` still exits **10** on this branch, correctly: 15 of 80 worktrees hold work off origin,
  including `T-0117`'s untracked `Sources/ScenicKit/Scoring/`. That is the check working, not the check
  failing. Also still red and not mine, as the reviewer noted: `origin/main` carries
  `ops/lib/ro_grammar.py` at `100644`, so `ops/lib/check-exec-bits` fails on `main` (P-OPS-01). This
  branch has it `100755`.

- 2026-09-08 — **REVIEW #2: PASS — `agent/reviewer-final-pr65`** (not the owner; owner is
  `agent/claude-opus-5`). Transitioned `queue/claimed/` -> `queue/done/` by `git mv`. All four prior
  findings verified closed **by running what demonstrated them**, not by reading the diff. Exit codes taken
  as `<cmd> >/dev/null 2>&1; echo $?`, never off a pipe. Scratch under `.worktrees/T-0103/.artifacts/`.

  **Verify + acceptance.** `verify: [ops/test, ops/check-pins]`; `acceptance:` is empty.

        $ bash ops/test                  0    TESTS linux=50/50 ios=skipped failed=0 skipped=0
        $ bash ops/check-pins            0    PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        $ bash ops/queue-check           0    QUEUE OK (93 tasks)
        $ bash ops/lib/check-exec-bits   0    P-OPS-01: 25 files, 15 required present, all modes correct
        $ bash ops/lib/check-worktrees-demo   0    DEMO: 19 ok, 0 failed
        $ bash ops/agent-preflight       0    PREFLIGHT OK
        $ bash ops/sane                 10    worktrees FAIL 5 of 81 - untracked:0 modified:2 unpushed:3
        gh pr view 65                         core SUCCESS, pins-source-only SUCCESS

  `ops/test` exits **0** here, so the previous log's "1, then 0 after npm ci" is reproduced in its resolved
  state: `services/api/node_modules` is present in this worktree now. Every number the previous Log claims
  above is reproducible.

  **F1 — the invented count. CLOSED, and re-proved on live data rather than trusted.** One captured
  `check-worktrees` run, both counts taken off the same bytes:

        WORKTREES-SUMMARY ... problems=9 ...        <- what the check emits
        grep -c '^  '   -> 11                       <- what ops/sane used to derive
        grep -c '^  [^ ]' -> 11                     <- the summary's own continuation lines match too

  Off by exactly the two continuation lines, on live output. `ops/sane` now reads the emitted line: its FAIL
  line said `5 of 81` above the check's own `5 of 81` and `problems=5`, and each state carries its own count
  (`untracked:0 modified:2 unpushed:3`), so a modified-only worktree is no longer called work off origin.

  F1's second half (the block stole the production exit code) is a real red/green, because the old file still
  runs. Same dead backend, same minute, same fleet:

        $ API_URL=http://127.0.0.1:9 bash .artifacts/sane-old --prod    # ops/sane at 81ad441
        worktrees FAIL   9 worktree(s) hold work that is not on origin
        backend   FAIL   http://127.0.0.1:9/__health -> unreachable
        SANE FAIL exit=10          <- contradicts the exit-code table in its own header
        $ API_URL=http://127.0.0.1:9 bash ops/sane --prod
        backend   FAIL   http://127.0.0.1:9/__health -> unreachable
        worktrees FAIL   9 of 82 need attention - untracked:0 modified:6 unpushed:3 ...
        SANE FAIL exit=7           <- matches the table

  **F2 — two of four states behind a flag nothing invoked. CLOSED.** `--deep` is a no-op; all states are the
  default. Proved on the live fleet, not only in the fixture: a default `ops/sane` run reported
  `statted=82 touches=77`, so the per-worktree `git status` and the `touches:` parse both ran against 82 and
  77 real worktrees, and it named `T-0083 modified:1` / `T-0114 modified:3` — the modified state firing on
  the fleet with no flag. The runtime objection is gone too. Re-measured on a **quiet box, 82 worktrees**:

        bash ops/lib/check-worktrees           real 0m28.3s   (was: --deep 19m40s)
        bash ops/lib/check-worktrees --fast    real 0m5.9s

  Against the previous reviewer's 19m40s for the old `--deep`, that is the difference between a check nobody
  runs and one that runs. (Under my own concurrent load the same two were 3m07s and 1m20s, which brackets
  the Log's "full 1m34s / --fast 43s under four agents" — the claim is consistent, not fabricated.)

  **F3 — the red demo. CLOSED, and I did not take the demo's word for it.** `ops/lib/check-worktrees-demo`
  reproduces at `DEMO: 19 ok, 0 failed`, exit 0. But a demo that passes is worth nothing until it is shown to
  fail, so I **mutation-tested the demo against its own subject**: seven copies of `ops/lib/check-worktrees`
  in `.artifacts/mut/`, one defect each, the committed demo run against each. Nothing under `ops/` was
  touched.

        mutation (in a COPY of check-worktrees)          demo result
        untracked never reported                         FAIL untracked RED + FAIL "did NOT say" (17/2)
        modified never reported                          FAIL modified  RED + FAIL "did NOT say" (17/2)
        wrong-branch never reported                      FAIL branch    RED + FAIL "did NOT say" (17/2)
        missing origin branch never reported             FAIL unpushed  RED + FAIL "did NOT say" (17/2)
        population floor reverted to the old `n -lt 1`   FAIL floor     RED                      (18/1)
        touches floor removed                            FAIL touches   RED + FAIL "did NOT say" (17/2)
        statted floor removed                            FAIL statted   RED                      (18/1)

  **Seven for seven, and each mutation killed only its own assertion.** The demo is not vacuous: every state
  and every floor it claims to cover, it actually covers. The floor case is the sharpest — reverting to
  `n -lt 1` still exits 2 (the truncated parse trips the `touches` floor instead), so an exit-code-only
  assertion would have passed it; the demo asserts the *message* (`"did not see the fleet"`) and caught it.

  **And I re-performed the brief's red demo myself, on the real 84-worktree fleet rather than in a fixture**,
  because a fixture proves the logic and not the parse at scale. Probe worktree on `task/T-9902` with a
  real-shaped task file (`touches: [services/etl/etl/, ops/probe-marker]`), one untracked file inside
  `touches:` and one outside it:

        RED    _rvw65probe   untracked-in-touches: services/etl/etl/_rvw65_lost.py
                             unpushed:[no origin/task/T-9902 at all]          exit=1
               ... and did NOT name notes-outside-touches.txt                 <- the brief's discriminator
        GREEN  file removed -> untracked=0                                    exit=1 (unpushed only)

  Then the state the previous reviewer said deserved the demo most, `branch:[...]`, also on the live fleet —
  the probe moved to a directory named `T-9902` and checked out on a leftover demo branch, which is the
  `wt/T-0085` shape verbatim:

        RED    T-9902   unpushed:[no origin/demo/T-9902-mrg at all]
                        branch:[HEAD is demo/T-9902-mrg, not task/T-9902]     exit=1, branch=1

  Probe cleanup: `git worktree remove --force .worktrees/T-9902`, `git branch -D task/T-9902
  demo/T-9902-mrg`. Neither branch was ever pushed; `git worktree list | grep 9902` is empty.

  **F4 — preflight voted on other agents' directories. CLOSED.** All three hooksPath cases re-run in this
  worktree with `GIT_CONFIG_COUNT=1 GIT_CONFIG_KEY_0=core.hooksPath GIT_CONFIG_VALUE_0=...`, so no shared
  config was mutated, and with the fleet dirty (3 problems) throughout:

        1. as configured (.githooks)          exit=0   "relative - resolves to THIS worktree"
        2. absolute -> MAIN checkout          exit=1   "^ ABSOLUTE and NOT this worktree"
        3. absolute -> THIS worktree          exit=0   "(absolute, but it is this worktree's own .githooks)"

  **0 / 1 / 0**, where the previous reviewer measured 1 / 1: preflight's exit code distinguishes the hazard
  from the benign case again, and the sweep prints `FYI 3 of 82 ... (does not fail preflight)` while exiting
  0. `.github/workflows/linux-core.yml:59` therefore gates on the toolchain and not on 82 strangers'
  directories.

  **Mechanical rules — clean.** Branch touches exactly `ops/agent-preflight`, `ops/lib/check-worktrees`,
  `ops/lib/check-worktrees-demo`, `ops/sane` and this queue file, all inside `touches:` (widened by one path
  in the same commit, declared in the Log). `git ls-files -s` -> `100755` on all four scripts, including the
  new `ops/lib/check-worktrees-demo`. Line counts 109 / 94 / 273 / 151, all under the 300 cap; one script per
  file. No `git add -A` residue, no secrets, no pin or assertion anchored on a comment.

  **Noted, not blocking.** (a) The header says "FOUR STATES" but five are reported and counted — `missing:`
  is the fifth, and it is undemonstrated; it predates this PR (it is present at `81ad441`) so it is not a
  check this PR introduced. (b) `statted >= 1` and `touched >= 1` are floored independently, so in principle
  they could be satisfied by two *different* worktrees while the untracked half examined none; at
  `statted=82 touches=77` this is theoretical. (c) Still red and not this branch's: `origin/main` carries
  `ops/lib/ro_grammar.py` at `100644`, so `ops/lib/check-exec-bits` fails on `main` (P-OPS-01).
