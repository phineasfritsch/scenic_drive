---
id: T-0060
title: the repo lives on NTFS at C:/ though the plan says WSL2 ext4, never /mnt/c
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
