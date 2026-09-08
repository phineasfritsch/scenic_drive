---
id: T-0060
title: the repo lives on NTFS at C:/ though the plan says WSL2 ext4, never /mnt/c
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T03:07:18Z
lease_expires_at: 2026-09-08T07:07:18Z
worktree: wt/T-0060
branch: task/T-0060
exclusive: []
touches: [CLAUDE.md, queue/README.md]
pins_affected: []
reviewer: null
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
