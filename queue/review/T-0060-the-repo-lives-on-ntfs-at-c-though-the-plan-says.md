---
id: T-0060
title: the repo lives on NTFS at C:/ though the plan says WSL2 ext4, never /mnt/c
state: review
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:07:18Z
lease_expires_at: 2026-09-08T07:07:18Z
worktree: wt/T-0060
branch: task/T-0060
exclusive: []
touches: [CLAUDE.md, queue/README.md]
pins_affected: []
reviewer: agent/reviewer-pr54
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

The plan's Dev box row is explicit:

    Repo in **WSL2 ext4 home**, never `/mnt/c`   |   CRLF and NTFS break every `ops/*` script

The repo is at `C:/Users/phineasf/Documents/GitHub/scenic_drive` - NTFS, reached from WSL as `/mnt/c/...`.
That single fact is the root cause of a family of symptoms this fleet has now spent several tasks on:

- **T-0055.** A Windows worktree's `.git` file contains `gitdir: C:/...`, which WSL's git cannot follow. So
  `git rev-parse --show-toplevel` and every `git ls-files` inside a pin assertion fail from WSL - and WSL is
  the only shell that can reach the pinned Docker image. Hence no single shell can run all four gates, and
  every Verification block in every task log is stitched together from two.
- **T-0051.** CRLF. The plan's own rationale for the rule names it.
- **T-0025.** `ops/etl-curvature-fixture` silently continued in whatever directory it started in, because its
  `cd "$(git rev-parse ...)"` failed under WSL without `set -e`. It happened to be the right directory.
- The recurring need to write scripts with the Write tool rather than heredocs, because of shell quoting
  differences between the two environments.

None of these are hard to work around individually, and all of them have been worked around. The question this
task exists to settle is whether that is the right trade, and it is the OWNER'S call, not an agent's:

- **Move the checkout to WSL2 ext4** (`~/scenic_drive`), as the plan says. Removes the whole family at once.
  Costs: re-cloning, re-creating ~20 worktrees, re-fetching the ~2.5 GB of pinned ETL inputs, and Windows-side
  tools (an editor, Xcode-adjacent work later) then reach the repo over the 9p filesystem, which is slow.
- **Stay on NTFS and keep paying the tax.** Every new `ops/` script must avoid `git rev-parse`, and the
  two-shell seam stays. T-0055 and T-0061 are that tax being paid.
- **Stay, and write the decision down.** If NTFS is deliberate, CLAUDE.md should say so and the plan row
  should be amended, so the next agent does not read the plan, see `/mnt/c`, and file this again.

Whichever is chosen, the deliverable is the SAME: the decision recorded where an agent will read it. The worst
outcome is the current one, where the plan says one thing, the disk says another, and nobody has reconciled
them.

- If the answer is "move": do it as an owner-run migration, not an agent task - it invalidates every worktree
  path in every claimed task file.
- If the answer is "stay": amend CLAUDE.md's File discipline section with the rule agents must follow
  (`${BASH_SOURCE[0]}`, never `git rev-parse`, in anything under `ops/`), and close T-0061 by fixing the
  assertions the same way.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from T-0055, which fixed eight wrappers and then found that the
  cause was one level below all of them.
- 2026-09-08T03:07:18Z claimed by agent/claude-opus-5; lease until 2026-09-08T07:07:18Z

- 2026-09-08 agent/claude-opus-5 — the third option in this brief, taken deliberately: **the decision is
  recorded, and the migration is left where the brief puts it — with the owner.**

  This task says the move is the owner's call and I have not made it. What I have removed is the state the
  brief calls the worst outcome: *"the plan says one thing, the disk says another, and nobody has reconciled
  them."* CLAUDE.md now says the repo is on NTFS, that this binds until the owner migrates, and what an agent
  must therefore do. Moving still costs exactly what the brief says — every `worktree:` path in every claimed
  task file, plus a ~2.5 GB re-fetch — so it stays an owner-run migration.

  **Six rules, each of which cost this fleet real time in the last day**, all executed rather than recalled:

  1. No `git rev-parse --show-toplevel` under `ops/` or `.githooks/`. Fails from WSL against a Windows
     worktree, and without `set -e` it fails SILENTLY (T-0025). T-0055 fixed the wrappers' `cd`; T-0077 fixes
     how they locate their module, which is the same bug one layer down.
  2. Python heredoc stdout carries CRLF. `ops/merge-rehearse` reported `0 conflicts, 0 gate failures` having
     merged **one** branch of thirty-one, because every name arrived as `task/T-0014\r`.
  3. Write scripts to a file. Inline heredoc quoting ate backslash escapes three separate times in one task.
  4. MSYS rewrites `/bin/true` in argv into a Windows path with a space, so a command fails for the wrong
     reason and reads as "the guard caught it" — a round-two verifier lost an evasion to exactly this.
  5. `python3` here is 3.14.5 with no pytest; `python` is 3.10.11 with it. `ops/test` runs the former and
     blames `services/etl` (T-0076).
  6. Never edit a running script; never `git reset --hard` with uncommitted work. Both happened today, both
     cost real work, and both are cheap to repeat.

  **Not done, and deliberately:** `queue/README.md` is in this task's `touches:` and needed nothing — the
  rules belong where agents already read them on every task, and duplicating them into a second file creates
  two copies to drift apart.

  Gates: `PINS ok=9 failed=0`, `--source-only ok=3 failed=0`, `QUEUE OK`.

  **If the owner chooses to move**, this section is what gets deleted, and T-0061 evaporates with it. That is
  still the better end state; it is just not an agent's call, and pretending otherwise would leave twenty
  worktrees pointing at paths that no longer exist.

- 2026-09-08 agent/claude-opus-5 — a seventh rule, earned the same day. `/tmp` is not one directory here:
  git-bash maps it into its own install, and a python child resolves the identical literal as `C:\tmp`.
  Writing a file with `git show ... > /tmp/x` and reading it back from python raised

        FileNotFoundError: [Errno 2] No such file or directory: '\tmp\t49-pins.yaml'

  mid-way through resolving a real merge conflict, which is the worst possible moment to lose a scratch file.
  Scratch goes in a gitignored directory inside the repo.

- 2026-09-08 agent/claude-opus-5 — an eighth rule, and the only one here that is not about this checkout being
  on NTFS. Added because it changes how every future check must be written, and CLAUDE.md is where agents
  actually look.

  Three environment variables were used to turn red gates green against scripts that had ALREADY been hardened
  to derive their root from `${BASH_SOURCE[0]}`, with no edit to any tracked file:
  `GIT_CONFIG_PARAMETERS`, `PYTHONPATH` (via `sitecustomize.py`, which `site` imports from `sys.path` at
  interpreter startup), and a `git` shim on `PATH`. The second produced `PINS ok=99 ... failed=0` and
  `QUEUE OK (999 tasks)` — the exact two strings the hardening commit's own header cited as proof of the
  defect it had just fixed.

  The rule is stated as "assume the caller controls PATH and every GIT_*/PYTHON* variable, and ask what your
  check still proves", not as a list of three names to unset — because the list is the losing move, and
  [[T-0086]] exists to fix it properly rather than by adding a fourth name.

- 2026-09-08 agent/claude-opus-5 — **an independent reviewer of PR #54 found one MEDIUM and two LOW defects in
  the CLAUDE.md section this task added. All three are fixed here.** Two are prose corrections, so there is no
  red/green to run; what replaces it is the grep output that establishes each number, run before the number was
  written down and pasted verbatim below.

  **FINDING 1 [medium] — the `git rev-parse --show-toplevel` rule shipped with a false sentence.** The bullet
  said *"T-0055 fixed the wrappers; T-0077 fixes how they locate their module"*, present tense, as if the tree
  already obeyed the rule. Neither branch is merged. The rule was therefore written ahead of the tree and said
  nothing about it, and it also hid three sites that survive both fixes.

      $ git grep -n show-toplevel origin/main -- ops .githooks
      origin/main:ops/agent-preflight:5:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/check-pins:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/pins.py" "$@"
      origin/main:ops/claim:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/queue.py" claim "$@"
      origin/main:ops/deploy:8:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/lib/check-exec-bits:12:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/lib/check-line-cap:15:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/lock:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/queue.py" lock "$@"
      origin/main:ops/merge:16:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/new-task:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/queue.py" new "$@"
      origin/main:ops/prod-read:9:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/queue-check:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/queue.py" check "$@"
      origin/main:ops/queue-next:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/queue.py" next "$@"
      origin/main:ops/queue-sweep:2:exec "${PYTHON:-$(command -v python3 || command -v python)}" "$(git rev-parse --show-toplevel)/ops/lib/queue.py" sweep "$@"
      origin/main:ops/sane:15:cd "$(git rev-parse --show-toplevel)"
      origin/main:ops/test:14:cd "$(git rev-parse --show-toplevel)"

      $ git grep -n show-toplevel origin/main -- ops .githooks | wc -l
      15
      $ git grep -n show-toplevel origin/main -- .githooks | wc -l
      0
      $ git grep -n show-toplevel HEAD -- ops .githooks | wc -l      # this PR's own branch
      15

  15 hits, all live code, all under `ops/`, none under `.githooks/` — and the branch that writes the rule ships
  the same 15. On `task/T-0077` the count is 16 because that branch documents the old line in comments; only
  three are still executable:

      $ git grep -n show-toplevel origin/task/T-0077 -- ops | wc -l
      16
      $ git grep -n show-toplevel origin/task/T-0077 -- ops
      origin/task/T-0077:ops/agent-preflight:5:# The repo comes from ops/lib/boot.sh, not from the caller: `cd "$(git rev-parse --show-toplevel)"` printed
      origin/task/T-0077:ops/check-pins:5:#     exec "$py" "$(git rev-parse --show-toplevel)/ops/lib/pins.py" "$@"
      origin/task/T-0077:ops/check-pins:6:# and `git rev-parse --show-toplevel` answers "the repo the CALLER is standing in". Run this file from
      origin/task/T-0077:ops/claim:3:# `git rev-parse --show-toplevel` here located ops/lib/queue.py in whatever repo the caller was standing
      origin/task/T-0077:ops/deploy:7:# The repo comes from ops/lib/boot.sh, not from the caller: `cd "$(git rev-parse --show-toplevel)"` would
      origin/task/T-0077:ops/lib/boot.sh:8:# Every wrapper used to say `git rev-parse --show-toplevel`, which answers "the repo the CALLER is
      origin/task/T-0077:ops/lib/check-exec-bits:12:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0077:ops/lib/check-line-cap:15:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0077:ops/lock:3:# `git rev-parse --show-toplevel` here located ops/lib/queue.py in whatever repo the caller was standing
      origin/task/T-0077:ops/merge:16:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0077:ops/new-task:3:# `git rev-parse --show-toplevel` here located ops/lib/queue.py in whatever repo the caller was standing
      origin/task/T-0077:ops/queue-check:3:# `git rev-parse --show-toplevel` here located ops/lib/queue.py in whatever repo the caller was standing
      origin/task/T-0077:ops/queue-next:3:# `git rev-parse --show-toplevel` here located ops/lib/queue.py in whatever repo the caller was standing
      origin/task/T-0077:ops/queue-sweep:3:# `git rev-parse --show-toplevel` here located ops/lib/queue.py in whatever repo the caller was standing
      origin/task/T-0077:ops/sane:16:# --show-toplevel)"` reported on whatever repo the caller was standing in: from a synthetic repo carrying one
      origin/task/T-0077:ops/test:15:# --show-toplevel)"` walked into whatever repo the caller was standing in and then read ITS pins/floor_*.txt

  13 comment lines, 3 live: `ops/lib/check-exec-bits:12`, `ops/lib/check-line-cap:15`, `ops/merge:16`. The same
  filter on `task/T-0055` leaves 7 live, and the two branches are independent, so neither subsumes the other:

      $ git grep -n show-toplevel origin/task/T-0055 -- ops | grep -v ':[0-9]*:#'
      origin/task/T-0055:ops/deploy:8:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0055:ops/lib/check-exec-bits:12:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0055:ops/lib/check-line-cap:15:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0055:ops/merge:16:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0055:ops/prod-read:9:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0055:ops/sane:15:cd "$(git rev-parse --show-toplevel)"
      origin/task/T-0055:ops/test:14:cd "$(git rev-parse --show-toplevel)"

      $ git merge-base --is-ancestor origin/task/T-0055 origin/task/T-0077 && echo YES || echo NO
      NO
      $ git merge-base --is-ancestor origin/task/T-0055 origin/main && echo YES || echo NO
      NO
      $ git merge-base --is-ancestor origin/task/T-0077 origin/main && echo YES || echo NO
      NO

  So after **both** land, the intersection — those three sites — survives. Nothing else covers them:

      $ grep -rl "show-toplevel" queue/
      queue/claimed/T-0055-ops-check-pins-and-ops-queue-check-cannot-run-fr.md
      queue/claimed/T-0060-the-repo-lives-on-ntfs-at-c-though-the-plan-says.md
      queue/claimed/T-0077-every-ops-wrapper-locates-its-module-from-the-ca.md
      queue/claimed/T-0086-the-environment-defeats-every-ops-checker-regard.md

  (T-0086 mentions the string only in passing; it does not touch those files.) The bullet now says the rule is
  written ahead of the tree, gives the 15/7/3 counts with the command that produces them, names both unmerged
  branches, names the three survivors by `file:line`, and tells the next reader to re-run the grep rather than
  believe the number. **Nothing that could not be reproduced above was written down.**

  **FINDING 2 [low] — "three times in three files" inflated the count.** It is three *ways*, and they all went
  around the defences in one file. `ops/lib/boot.sh` is the only file under `ops/` carrying either an unset
  denylist or an interpreter probe:

      $ git grep -l "unset " origin/task/T-0077 -- ops
      origin/task/T-0077:ops/lib/boot.sh
      $ git grep -l "find_spec\|PYTHONPATH\|PYTHONHOME" origin/task/T-0077 -- ops
      origin/task/T-0077:ops/lib/boot.sh

  Corroborated in the file itself: `boot.sh:90-92` is a single `unset` of exactly fifteen `GIT_*` names, none of
  them `GIT_CONFIG_PARAMETERS`, which is what the first evasion used; `boot.sh:117` is the `u.find_spec` probe
  that `sitecustomize.py` gets to run inside; and no line of it touches `PATH`. T-0086's own brief says
  *"defeated that sentence three ways"* (line 25), not three files. Corrected to "three ways in one file", with
  the reason it matters: three files would have been three chances to notice, and there was one.

  **FINDING 3 [low] — the task file was never transitioned.** PR #54 is OPEN
  (`gh pr view 54` → `{"headRefName":"task/T-0060","number":54,"state":"OPEN"}`) while the task file sat in
  `queue/claimed/` with `state: claimed` and `reviewer: null`, which is `queue/README.md` step 6 unperformed.
  Moved with `git mv` — not copy-then-delete, because a stale copy in two directories is what makes
  `ops/queue-check` report a duplicate id:

      $ git mv queue/claimed/T-0060-...md queue/review/T-0060-...md
      $ git status --short
       M CLAUDE.md
      RM queue/claimed/T-0060-...md -> queue/review/T-0060-...md
      $ ls queue/claimed/ queue/review/ | grep -c T-0060
      1

  RED and GREEN, because the reviewer gate is a check and a check nobody has seen fail is untested. In `review/`
  with `reviewer: null`:

      $ bash ops/queue-check
      QUEUE CHECK FAIL
       - queue/review/T-0060-the-repo-lives-on-ntfs-at-c-though-the-plan-says.md: in review/ without a reviewer
      EXIT=1

  and with `reviewer:` set to the owner, which is the failure step 6 exists to prevent:

      $ bash ops/queue-check
      QUEUE CHECK FAIL
       - queue/review/T-0060-...md: reviewer == owner (agent/claude-opus-5) - a worker may not grade its own work
      EXIT=1

  GREEN with `reviewer: agent/reviewer-pr54`:

      $ bash ops/queue-check
      QUEUE OK (81 tasks)
      EXIT=0

  Gates re-run after all three fixes:

      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only   EXIT=0
      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux               EXIT=0
      $ bash ops/queue-check
      QUEUE OK (81 tasks)                                                       EXIT=0

  **Scope held:** `CLAUDE.md` and this task file only. The three live `show-toplevel` sites are named in
  CLAUDE.md rather than fixed here, because `ops/lib/check-exec-bits`, `ops/lib/check-line-cap` and `ops/merge`
  are outside this task's `touches:` and belong to whoever owns those files next.
