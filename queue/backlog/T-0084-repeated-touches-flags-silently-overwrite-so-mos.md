---
id: T-0084
title: repeated --touches flags silently overwrite, so most tasks declare one path of several
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`_opts` in `ops/lib/queue.py` builds its option dict with a plain assignment:

    out[argv[i][2:]] = argv[i + 1] if i + 1 < len(argv) else "true"

so a repeated flag **overwrites**. `ops/new-task "..." --touches a --touches b --touches c` records `c` and
silently discards `a` and `b`. Nothing warns; the task file simply says less than was asked for.

Measured across the fourteen tasks filed on 2026-09-08:

    T-0072  passed 2 flags, recorded  [ops/check-pins]
    T-0077  passed 4 flags, recorded  [ops/new-task]
    T-0081  passed 2 flags, recorded  [services/etl/etl/]
    T-0083  passed 3 flags, recorded  [services/api/src/ro.ts]

Only `T-0071` carries a multi-entry list, and only because it was edited by hand afterwards.

**This has already cost real work, and in the worst possible way.** `.githooks/pre-commit` enforces `touches:`,
so an agent whose task declares one path of five hits a refusal on its own legitimate files and *widens the
task file to get the commit through*. The T-0072 and T-0077 fix agents both reported doing exactly that. The
declared scope then matches what the agent happened to touch rather than what the task is - which is precisely
the failure [[T-0078]]'s brief calls out when it says not to widen a parent's `touches:` to cover a child.

So the hook is enforcing a list that the tool which writes the list cannot express.

- Make list-valued options accumulate. `touches`, `pins` and `depends` are all `_list()`-typed at the call
  site, so the flags that feed them should append rather than replace.
- A comma-separated single flag already works (`--touches a,b,c`) because `_list` splits it. That is the
  workaround; it is not the fix, and it is not documented anywhere an agent reads.
- **Repeated scalar flags should be an error, not a silent last-wins.** `--reviewer x --reviewer y` quietly
  picking `y` is the same defect wearing a different field, and `ops/review` and `ops/claim` share `_opts`.
- Audit and repair the four tasks above. Their `touches:` are wrong right now, so the hook is protecting the
  wrong set on four live branches.
- Demonstrate red by passing three `--touches` and showing one recorded, green by showing three.

**Do not fix this by teaching the hook to be lenient.** The hook is right; the writer is lossy.

## Log
- 2026-09-08 filed by agent/claude-opus-5 after `git commit` on task/T-0083 was refused for four files that
  belonged to the task, because `ops/new-task` had recorded only the last of three `--touches` flags. The
  refusal message printed the one-entry list, which is what made it visible.

- 2026-09-08 agent/claude-opus-5 — **fixed by T-0087's `_opts` rewrite on `task/T-0087` (fa5c55a), verified
  independently here rather than taken on the fixer's word.**

  T-0087's brief folded this in because both defects live in the same function. Measured against that branch
  in a throwaway worktree:

        ops/new-task "..." --touches ops/a --touches ops/b --touches ops/c
          -> touches: [ops/a, ops/b, ops/c]            (was: [ops/c], the other two dropped silently)

        ops/new-task "..." --owner agent/x --owner agent/y
          -> refused: --owner is not an option of `new` (--depends, --exclusive, --pins, --state, --touches)
             (was: accepted, last-wins, nothing printed)

        ops/new-task                    (no arguments - T-0087's own defect)
          -> usage: queue.py new "<title>" [--depends V] ...
             refused '': the operand comes first and may not be blank.
             (was: IndexError traceback)

  The rewrite goes further than this brief asked, and the extra cases are the valuable part: `--touchez a`
  set a key nobody reads, `--touches --state done` recorded `touches: ['--state']` and dropped `--state`
  entirely, and `claim T-1 T-2` ignored the second word. **Every one of those was silent**, which its
  docstring correctly calls worse than the traceback the task started from — a stack trace at least stops.

  A repeated SCALAR is now refused rather than resolved, which is the right call: which of two `--owner`s was
  meant is not knowable, and last-wins is the answer an agent re-reading its own command line is least likely
  to expect.

  **Still to do when this and T-0087 merge:** the four tasks whose `touches:` were truncated by the old
  parser are still wrong on their branches — T-0072 recorded 1 of 2, T-0077 1 of 4, T-0081 1 of 2, T-0083
  1 of 3. The parser is fixed; the data it corrupted is not. T-0081's and T-0083's were widened by hand
  during this session; T-0072's and T-0077's were not.
