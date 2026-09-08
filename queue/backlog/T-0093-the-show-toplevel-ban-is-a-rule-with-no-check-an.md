---
id: T-0093
title: the show-toplevel ban is a rule with no check, and three call sites survive both fixes
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/check-no-toplevel, ops/lib/check-exec-bits, ops/lib/check-line-cap, ops/merge, pins/PINS.yaml]
pins_affected: [P-OPS-02]
reviewer: null
depends_on: [T-0055, T-0060, T-0077]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**T-0060 writes a rule into CLAUDE.md that nothing enforces, and after both branches that were supposed
to fix the tree have merged, three call sites are still standing.** Found by the reviewer of PR #54, then
re-measured here.

The rule (CLAUDE.md, T-0060's section): *never `git rev-parse --show-toplevel` in anything under `ops/`* —
because from WSL against this Windows checkout the `.git` file says `gitdir: C:/...`, WSL's git cannot
follow it, and every wrapper that locates itself that way dies (T-0055).

Measured on 2026-09-08:

    $ git grep -l show-toplevel origin/main -- ops .githooks | wc -l
    15

    $ git grep -n show-toplevel origin/task/T-0077 -- ops | grep -v ':[0-9]*: *#'
    origin/task/T-0077:ops/lib/check-exec-bits:12:cd "$(git rev-parse --show-toplevel)"
    origin/task/T-0077:ops/lib/check-line-cap:15:cd "$(git rev-parse --show-toplevel)"
    origin/task/T-0077:ops/merge:16:cd "$(git rev-parse --show-toplevel)"

    $ git grep -n show-toplevel origin/task/T-0055 -- ops | grep -v ':[0-9]*: *#' | wc -l
    7

T-0055 converts eight wrappers, T-0077 converts the rest of the module lookup, and **neither touches
`ops/lib/check-exec-bits`, `ops/lib/check-line-cap` or `ops/merge`.** `grep -rn show-toplevel queue/`
hits only T-0055, T-0060, T-0077 and T-0086 — no task covers those three, so the rule is written for a
tree that will still violate it after every planned fix lands.

**Why this is the repository's own recurring defect, not a leftover.** A rule whose only enforcement is a
sentence in CLAUDE.md is exactly the shape `ops/check-pins --source-only` exists to replace. CLAUDE.md
already says so about itself: *"`ops/check-pins --source-only` enforces the mechanical parts."* This one
is mechanical and is not enforced. It is also un-anchorable on a comment — every one of the 13 remaining
hits on `task/T-0077` is *inside a comment*, so any check that greps naively reports 16 violations on a
tree that has 3. The check must ignore comment lines and still catch the live calls.

Do:

1. Convert the three surviving sites to whatever `ops/lib/boot.sh` (T-0086) offers, matching T-0055's
   conversion exactly. Do not invent a second idiom.
2. Add `ops/lib/check-no-toplevel`: fail when any executable under `ops/` or `.githooks/` executes
   `git rev-parse --show-toplevel` outside a comment. Anchor on the call, not on a comment marker, and
   **prove it can tell the two apart** — the red demo must show a comment-only file passing and a live
   call failing, on the same file.
3. Pin it as **P-OPS-02** in `pins/PINS.yaml` (`runs_on: [linux]`, `anchor: source`) next to P-OPS-01.
4. Vacuity guard: the check must fail if it inspected fewer than a floor of files (P-OPS-01's own
   MIN_FILES idiom). A `find` that matches nothing reports zero violations and exits 0, and that is this
   repository's most-repeated defect.

`git update-index --chmod=+x ops/lib/check-no-toplevel` — `core.filemode` is false here, CI (`bash ops/x`)
stays green while direct invocation breaks, and P-OPS-01 is the pin that catches it.

**Ordering.** This lands after T-0055 and T-0077; both are unmerged. Claiming it before them means fixing
files those branches also rewrite. `ops/merge-rehearse` will surface the collision — run it first.

## Log
