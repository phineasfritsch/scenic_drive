---
id: T-0057
title: two different pins are both numbered P-OPS-02, on branches that will merge
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0023, T-0049]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`task/T-0023` and `task/T-0049` each add a pin called **P-OPS-02**, and they are different pins:

    T-0023  P-OPS-02  A failing test run names the tests that failed
                      assertion: bash ops/lib/check-failure-naming
    T-0049  P-OPS-02  ops/merge's --no-task-reason line is valid UTF-8 and one line; the cap counts characters
                      assertion: bash ops/lib/check-merge-reason-cap

Both are good pins. Both branches are green on their own gates. Neither author could have seen the other,
because `main`'s `pins/PINS.yaml` stops at P-OPS-01 and the next id is only visible on a branch nobody has
merged. This is the same shape as the finding recorded in T-0041 - two branches that are individually correct
producing a broken `main` - and it is the second confirmed instance, which is what makes it worth a task
rather than a rename.

**Two things to fix, and the second is the point.**

1. Renumber one of them. T-0023's is older and its `check-failure-naming` is already referenced by
   T-0041's `REQUIRED` list work, so T-0049's should become P-OPS-03 - but confirm that against whatever has
   merged by the time this is claimed rather than taking it on trust.

2. `ops/check-pins` does not notice. A duplicate id is not an error today; the YAML parse simply yields two
   entries with the same id, and the printed `ok=N` counts them both while any lookup by id silently resolves
   to one of them. `ops/queue-check` already refuses a duplicate TASK id for exactly this reason and says so.
   Pins deserve the same, and it is a handful of lines.

Anchoring the id-allocation problem itself is out of scope and probably not worth solving: `ops/new-task`
allocates task ids by scanning the tree, but pins are hand-written, and a scheme that reserves pin ids across
unmerged branches costs more than renaming a pin twice a year. Say so in the log rather than leaving it open.

- Demonstrate red: construct a `pins/PINS.yaml` with two entries sharing an id and show `ops/check-pins`
  reporting `ok=N failed=0` - i.e. passing - before the change, and naming the duplicate after it.
- Demonstrate that the fix does not fire on the real file, so it is not simply refusing everything.
- Check the same class for `pins/floor_*.txt` and the `P-SRC-*` / `P-SAFE-*` families while in there; if no
  other duplicate exists today, record that you looked.

## Log
- 2026-09-07T23:40:15Z claimed by agent/unknown; lease until 2026-09-08T01:40:15Z

- 2026-09-08T08:30Z claimed by agent/claude-opus-5, then RELEASED because half this brief is wrong. The
  claim I filed was:

      "ops/check-pins does not notice. A duplicate id is not an error today; the YAML parse simply yields two
       entries with the same id, and the printed ok=N counts them both while any lookup by id silently
       resolves to one of them."

  MEASURED, before writing any code. `ops/lib/pins.py:112-116` already carries the check, and it fires:

      duplicated id: P-SRC-01
      real pins file:  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      two pins, one id: PINS ok=3 skipped=8 pending=1 expired=0 failed=1 tier=linux source-only
                         - P-SRC-01: duplicate id
                        exit=1

  It also runs BEFORE the `--source-only` skip, so it fires in both modes. PINS.yaml restored, sha256 verified.

  I wrote an unverified assertion into a brief - in a task filed BECAUSE of unverified assertions - and it
  would have led whoever claimed it to build a check that already exists. Corrected rather than quietly
  deleted, because the brief is the thing the next agent reads.

  **What this changes about the merge-time traps.** T-0041 and this task both describe branches that are green
  alone and broken together. That framing implied the breakage would be SILENT. It would not: `check-pins`
  catches the duplicate id, and `check-exec-bits` catches T-0041's file mode, so the merged `main` goes RED
  rather than quietly wrong - provided CI runs, which is T-0053. The traps are real and worth pre-empting;
  they are not the silent-corruption class I filed them as.

  **What remains, and it is only the renumber.** Two different pins are still both called P-OPS-02, on
  `task/T-0023` (`check-failure-naming`) and `task/T-0049` (`check-merge-reason-cap`). That is a one-line edit
  to `pins/PINS.yaml`, which `task/T-0049` is actively editing right now, so doing it here would be the
  two-agents-one-file collision CLAUDE.md forbids. It belongs to whoever merges the second of those two
  branches, and `ops/check-pins` will refuse to let them forget.

  Returned to ready/ with the scope reduced to that, rather than left claimed against work that does not exist.

