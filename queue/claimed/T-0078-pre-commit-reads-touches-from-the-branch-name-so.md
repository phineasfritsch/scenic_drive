---
id: T-0078
title: pre-commit reads touches from the branch name, so a follow-up task's touches field is decorative
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:05Z
lease_expires_at: 2026-09-08T08:59:05Z
worktree: wt/T-0078
branch: task/T-0078
exclusive: []
touches: [.githooks/pre-commit]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`.githooks/pre-commit` builds its `touches:` allowlist from the **branch name**: `task/T-XXXX` ->
`queue/claimed/T-XXXX*.md`. So on a branch carrying a follow-up task - [[T-0072]] worked on `task/T-0066`,
[[T-0073]] on `task/T-0068`, [[T-0074]] on `task/T-0069` - the hook enforces the **parent's** list and ignores
the follow-up's entirely.

**A follow-up task's `touches:` field is therefore decorative.** It is written, committed, reviewed, and never
consulted. Both files had to be widened by hand during T-0072 to get the commit through, which is the symptom:
the field that was consulted was not the field that described the work.

Found by the T-0072 fixer while trying to commit, and stated in its report rather than worked around silently.

This is the same class as [[T-0039]] - `touches:` enforcement being dead for a category of task - and the
third time the queue's identity has been inferred from something other than the task being worked. Deciding
which task a commit belongs to by parsing a branch name works exactly until two tasks share a branch, which is
a thing this repo now does deliberately, because a follow-up belongs on the branch that carries the fix it
follows.

- The commit must say which task it is for, or the hook must consider EVERY claimed task whose `branch:` field
  names this branch. The second is mechanical and needs no new convention: `ops/claim` already writes
  `branch:` into the task file, and T-0072/T-0073/T-0074 set it explicitly to the parent's branch.
- Union the `touches:` of every task claimed onto this branch, or refuse when more than one is claimed and the
  commit does not name one. Either is defensible; pick one and say why in the file.
- Do not simply widen the parent's `touches:` to cover the child. That is what was done under duress here, and
  it makes the parent's declared scope a lie.
- Demonstrate red: on a branch with two claimed tasks, commit a path that is in the follow-up's `touches:` and
  not the parent's, and show the hook allowing it today. Then show it refusing a path in neither.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the T-0072 fix agent's report. It hit this while committing and
  widened both task files' `touches:` to proceed, which is recorded there.
- 2026-09-08T02:59:05Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:05Z
- 2026-09-08 agent/claude-opus-5 — fixed. **Decision: union.** Every task file in `queue/claimed/` or
  `queue/review/` whose `branch:` names the current branch governs the commit, and the allowlist is the union of
  their `touches:`. Chosen over "refuse until the commit message names one task" because `ops/claim` already
  writes `branch: task/<id>` (`ops/lib/queue.py:289`) and the round-two follow-ups already set it by hand, so the
  union needs no new convention and no change to any tool that commits; because one commit on a stacked branch
  legitimately spans both tasks (the follow-up's fix plus both task logs); and because naming a task in the
  message would put a second load-bearing convention in a commit body that already carries the floor ratchet,
  and would have to be taught to `ops/claim`, `ops/queue-sweep` and every agent. The parent's `touches:` was NOT
  widened. Two further properties fell out of making the field load-bearing and are part of the fix:
  task files are read from the **index**, not the working tree, so the `touches:` that governs a commit is the
  `touches:` the commit contains; and an allowlist entry matches a path **exactly or as a directory prefix**,
  never as a bare string prefix.

  All transcripts below come from a throwaway git repo (`.artifacts/T-0078/lab`, gitignored) driven by real
  `git commit` calls through `core.hooksPath=.githooks`, rebuilt per scenario. Harness:
  `.artifacts/T-0078/{lab-setup,probe,probe-rightreason,probe-unstaged,probe-forge,probe-misc,run-matrix}.sh`.
  Full before/after runs: `.artifacts/T-0078/matrix-{before,after}.txt` (253 lines each, same script, same order).
  Shape used throughout: branch `task/T-0100` carrying claimed `T-0100` (`touches: [src/parent.txt]`) and
  claimed follow-up `T-0101` (`branch: task/T-0100`, `touches: [src/child.txt]`) — the T-0072/73/74 shape.

  ### Route 1 — a follow-up's `touches:` is never consulted (closed)

  RED (hook at HEAD 6d93b13), identical probe script:

      --- probe: src/child.txt
          pre-commit: src/child.txt is outside T-0100 touches: [src/parent.txt ]
          pre-commit: refusing commit
          RESULT: REFUSED (exit 1)

  `src/child.txt` is the follow-up's *declared* scope and the hook names T-0100 — the wrong task. This is the
  face of the defect T-0072 hit: it did not silently allow, it wrongly refused, and the recorded workaround was
  to widen both task files by hand, which made the parent's declared scope a lie.

  GREEN (same command):

      --- probe: src/child.txt
          [task/T-0100 6ff7f61] probe src/child.txt
           1 file changed, 1 insertion(+)
           create mode 100644 src/child.txt
          RESULT: ALLOWED (commit created)
      --- probe: src/neither.txt
          pre-commit: src/neither.txt is outside touches: of queue/claimed/T-0100-parent.md queue/claimed/T-0101-followup.md [src/parent.txt src/child.txt]
          pre-commit: refusing commit
          RESULT: REFUSED (exit 1)

  Allowed *for the right reason*, proved by taking the reason away — repoint the follow-up at another branch,
  stage that edit, re-run the identical probe:

      --- follow-up now declares (in the index):
          id: T-0101
          branch: task/T-0999
          touches: [src/child.txt]
          pre-commit: src/child.txt is outside touches: of queue/claimed/T-0100-parent.md [src/parent.txt]
          pre-commit: refusing commit
          RESULT: REFUSED (exit 1)

  SELF-ATTACK at this route — the neighbouring forms, all executed:

  - *One more task on the branch* (three claimed tasks): union of all three; `src/third.txt` ALLOWED,
    `src/neither.txt` REFUSED naming all three files. Closed.
  - *One directory over — follow-up in `queue/review/`*: still governs
    (`... of queue/claimed/T-0100-parent.md queue/review/T-0101-followup.md [src/parent.txt src/child.txt]`).
  - *One directory over — follow-up in `queue/done/`*: does **not** widen. `src/child.txt` REFUSED.
    Fail-closed, not an evasion.
  - *Same value, different spelling* — `branch: "task/T-0100"` and `branch: refs/heads/task/T-0100`: both
    normalise and govern; `src/child.txt` ALLOWED, `src/neither.txt` REFUSED in both.
  - *Widen the allowlist without committing the widening* — worktree-only edit of the governing task file.
    RED: `touches: [src/parent.txt, src/evil.txt]` in the worktree, `[src/parent.txt]` in the index →
    `RESULT: ALLOWED`. GREEN, identical probe:
    `pre-commit: src/evil.txt is outside touches: of ... [src/parent.txt src/child.txt]` → REFUSED.
  - *Plant an extra claimed task naming this branch, untracked*: REFUSED (`in index: 0`).
  - *Plant it in `queue/ready/` and stage it*: REFUSED — only claimed/ and review/ are scanned.
  - *Plant it in `queue/claimed/` and stage it*: **ALLOWED** —
    `2 files changed ... create mode 100644 queue/claimed/T-0200-forged.md, create mode 100644 src/evil.txt`.
    This one is not a hole, it is the shape of the choice: the hook bounds a commit to *declared* scope and
    cannot bound what an agent is willing to declare. It is strictly better than before, because the
    declaration is now necessarily inside the commit and therefore in the diff a reviewer reads.

  ### Route 2 — a branch carrying only a follow-up is ungoverned (closed)

  Branch `task/T-0102`, one claimed task `T-0101` with `branch: task/T-0102`; no `queue/claimed/T-0102*.md`
  exists, so the branch-name glob found nothing and skipped the whole section.

  RED:

      --- probe: src/neither.txt
          [task/T-0102 48229af] probe src/neither.txt
          RESULT: ALLOWED (commit created)
      --- probe: ops/anything.sh
          [task/T-0102 b219bec] probe ops/anything.sh
          RESULT: ALLOWED (commit created)

  GREEN (same commands):

      --- probe: src/child.txt
          [task/T-0102 06d3d67] probe src/child.txt
          RESULT: ALLOWED (commit created)
      --- probe: src/neither.txt
          pre-commit: src/neither.txt is outside touches: of queue/claimed/T-0101-followup.md [src/child.txt]
          RESULT: REFUSED (exit 1)
      --- probe: ops/anything.sh
          pre-commit: ops/anything.sh is outside touches: of queue/claimed/T-0101-followup.md [src/child.txt]
          RESULT: REFUSED (exit 1)

  SELF-ATTACK — make no task match the branch, so the section switches off again:

  - `branch: null` on the only claimed task, branch `task/T-0100`: the by-id compat path still governs.
    `src/parent.txt` ALLOWED, `src/neither.txt` REFUSED. Closed.
  - Branch `task/T-0106` that no task claims: RED allowed everything; GREEN
    `pre-commit: no claimed or review task declares \`branch: task/T-0106\` - nothing bounds this commit`,
    both probes REFUSED. Closed (this now also refuses commits on `task/T-0029`, `task/T-0057`, `task/T-0070`,
    whose branches exist locally but whose tasks sit in blocked/ready/backlog — a deliberate tightening).
  - Non-task branch `wip/scratch` that a claimed task *does* declare: now governed by that task
    (both probes REFUSED where RED allowed both). A task's declared branch governs whatever it is called.
  - Non-task branch `wip/nobody` that no task declares: ALLOWED, unchanged — this is the `main` case, and
    `main` behaves exactly as before.

  ### Route 3 — a path in NEITHER list is still refused (closed)

  RED found three ways to be in neither list and still get through:

      --- probe: src/parent.txt.bak
          [task/T-0100 886eaad] probe src/parent.txt.bak
          RESULT: ALLOWED (commit created)          # `$f == $a*` is a bare string prefix
      --- probe: queue/evil.sh
          [task/T-0100 d6c403b] probe queue/evil.sh
          RESULT: ALLOWED (commit created)          # blanket `queue/*` exemption
      LAB READY mode=emptytouches ...
      --- probe: src/neither.txt
          [task/T-0100 6d84e60] probe emptytouches-neither
          RESULT: ALLOWED (commit created)          # `touches: []` -> empty -> section skipped entirely

  That last one is the two-character evasion: `touches: []` disabled the check completely.

  GREEN (identical probes):

      --- probe: src/parent.txt.bak
          pre-commit: src/parent.txt.bak is outside touches: of queue/claimed/T-0100-parent.md queue/claimed/T-0101-followup.md [src/parent.txt src/child.txt]
          RESULT: REFUSED (exit 1)
      --- probe: queue/evil.sh
          pre-commit: queue/evil.sh is outside touches: of queue/claimed/T-0100-parent.md queue/claimed/T-0101-followup.md [src/parent.txt src/child.txt]
          RESULT: REFUSED (exit 1)
      --- probe: src/neither.txt        (mode=emptytouches)
          pre-commit: src/neither.txt is outside touches: of queue/claimed/T-0100-parent.md []
          RESULT: REFUSED (exit 1)

  SELF-ATTACK:

  - *One character longer*: `src/child.txt.evil` REFUSED (was already refused; now for the boundary reason).
  - *Unparseable list instead of an empty one* — YAML block-style `touches:` over two lines. RED refused
    everything with a nonsense allowlist `[touches: ]`; GREEN refuses with
    ``pre-commit: queue/claimed/T-0100-parent.md has no single-line `touches: [...]` list; cannot bound this commit``.
    Fail-closed either way, and now it says why. No form of a broken `touches:` opens the gate.
  - *Still under queue/*: `queue/claimed/T-0999-forged.md` and `queue/LOCKS/x.lock` remain ALLOWED. Deliberate
    and documented in the hook: `ops/claim` stages `queue/` wholesale and `ops/lock` writes `queue/LOCKS/*.lock`.
    The exemption is now `queue/**.md`, `queue/LOCKS/*.lock` and `.gitkeep` only, so `queue/` is no longer a
    place to hide a script. Any task can still rewrite any other task's `.md`; that is queue bookkeeping, not
    this task, and it is visible in the diff.

  ### Route 4 — the section can still be switched off from outside the task files (NOT CLOSED)

  Four bypasses survive. Verbatim, against the fixed hook:

      --- probe: src/neither.txt         (detached HEAD)
          [detached HEAD 0867c68] probe detached-neither
          RESULT: ALLOWED (commit created)

  `git checkout --detach` leaves `git rev-parse --abbrev-ref HEAD` = `HEAD`, no task declares that, and the
  branch is not `task/*`-shaped, so nothing is enforced — for any path. I did not close it: refusing on a
  detached HEAD would refuse the `git commit` that finishes a conflicted rebase, which is a worse failure than
  the hole. `git checkout --detach && git commit && git branch -f task/X HEAD` is a working evasion today.

      --- probe: src/neither.txt         (mode=donefallback, branch task/T-0104, task in queue/done/)
          pre-commit: T-0104 is in queue/done/ - touches: NOT enforced (T-0039)
          [task/T-0104 33e2d9c] probe donefallback-neither
          RESULT: ALLOWED (commit created)

  That is T-0039's filed hole, left working on purpose so T-0039 can still reproduce it. It is now loud instead
  of silent, and the scan is a single pathspec list, so T-0039's fix is adding `queue/done/*.md` to line 94.

      --- A. git commit --no-verify with an out-of-scope path
          [task/T-0100 cc5d6de] no-verify probe
          RESULT: ALLOWED
      --- B. staged DELETION of a file outside touches: (src/seed.txt)
          [task/T-0100 b3ee724] deletion probe
           1 file changed, 1 deletion(-)
          RESULT: ALLOWED

  `--no-verify` cannot be closed from inside a hook. The deletion bypass is `--diff-filter=ACMR` on line 10 and
  is T-0048's filed defect, unchanged here. (A *rename* into an out-of-scope name is caught: the new path is R.)

  ### Cost

  The first correct version read each task file with `git show`: 46 claimed tasks = 92 process spawns.

      $ time bash .githooks/pre-commit
      real  0m39.179s

  A hook that costs 40s per commit is a hook the fleet routes around with `--no-verify`, so it is a correctness
  problem. Replaced with one `git grep --cached` over the index plus pure-parameter-expansion parsing (`$( )`
  per YAML line was itself ~10s of forks on this box):

      $ time bash .githooks/pre-commit
      real  0m1.260s

  ### Gates (this worktree)

      $ bash ops/queue-check           -> QUEUE OK (76 tasks)
      $ bash ops/check-pins            -> PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      $ bash ops/check-pins --source-only -> PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      $ bash ops/sane                  -> SANE OK
      $ bash ops/agent-preflight       -> PREFLIGHT OK

  `ops/test` was not run: this change touches only `.githooks/pre-commit`, which no target, pin or test in
  `ops/test` reads (`ops/test` references `.githooks/commit-msg` only, for the floor ratchet). `.githooks/pre-commit`
  is 146 lines, well under the 300-line cap, and keeps mode 100755.

  ### Behaviour changes a reviewer should weigh

  1. A `task/T-XXXX` branch with no claimed or review task declaring it is now **refused**, not ungoverned.
  2. A non-`task/` branch that a claimed task declares is now **governed**; `main` and unclaimed branches are not.
  3. `touches:` entries match exactly or as a directory prefix. A task declaring `ops/lib/check-line-cap` can no
     longer commit `ops/lib/check-line-cap-helper` without declaring it. That is stricter than yesterday and may
     turn someone's next commit red; the fix is to declare the path, not to widen a parent.
  4. A task file edited but not staged no longer counts. Declare the scope in the same commit.
