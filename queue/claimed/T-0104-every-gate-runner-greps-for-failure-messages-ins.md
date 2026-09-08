---
id: T-0104
title: every gate-runner greps for failure messages instead of reading the exit code it already has
state: claimed
owner: agent/claude-opus-5
owner_session: d217767a
claimed_at: 2026-09-08T11:03:47Z
lease_expires_at: 2026-09-08T14:03:47Z
worktree: null
branch: task/T-0104
exclusive: []
touches: [CLAUDE.md]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**Both criticals of the 2026-09-08 review round are the same defect in two files, and neither reviewer said
so because each was only shown one tool.** `ops/merge-rehearse`'s `gates()` and `ops/pr-ci-preflight`'s gate
block each call a check, **throw away its exit code**, and then `grep` its output for the failure messages
their author happened to know about. Every message the author did not enumerate reads as success.

The checks they call already answer correctly. `ops/lib/check-exec-bits` and `ops/lib/check-line-cap` both
exit 1 on every failure they have. The information was there and was discarded.

**Measured, by two independent reviewers, on real trees:**

    ops/pr-ci-preflight                     the check says          preflight says
    ------------------------------------------------------------------------------------------
    import SwiftUI in Sources/ScenicKit     P-SRC-01 fails, exit 1   gates clean, exit 0
    5 of 9 tracked .swift files removed     P-SRC-02 truncated set   gates clean, exit 0
    ops/deploy deleted                      P-OPS-01 not tracked     gates clean, exit 0

    ops/merge-rehearse gates()
    ------------------------------------------------------------------------------------------
    ops/prod-read dropped in a merge        P-OPS-01 exit 1          merged, gates clean
    only 2 tracked .swift files left        P-SRC-02 exit 1          merged, gates clean

`import SwiftUI` in `Sources/` is the workflow file's **own headline example** of what CI exists to catch.

**It gets worse as the checks improve, which is the part that makes this structural.** `check-line-cap` has
two failure messages today and `pr-ci-preflight` matches one of them; on `task/T-0058` it has **six**, and
the gate still matches one. Every improvement to a check silently widens the hole in the runner that calls
it. A guard whose coverage shrinks as the thing it guards gets better is not a guard.

**Two more shapes of the same mistake, both measured:**

- `gates()` keeps only `tail -1` of `queue-check`, and the INHERITED-failure suppression compares that single
  line. A branch that introduces a **brand-new duplicate task id** therefore reports as "unchanged by this
  branch" and does not increment `gatefails` — and duplicate ids are the defect [[T-0101]] was filed for and
  the reason `--pairwise` exists.
- `run_on` chains `git reset --hard && git clean && gates` with all output discarded, so **a failed checkout
  prints nothing and empty output means clean**. A tree containing one path git cannot check out on Windows
  flips from `GATES FAIL` to `gates clean`. GitHub builds merge trees on Linux, where such paths are legal.

Do:

1. **Read the exit code.** A gate-runner records failure when the check exits non-zero, full stop. Output is
   for the operator to read, never for the runner to interpret.
2. Keep the message extraction for the SUMMARY LINE only, and when the exit code is non-zero but no message
   matched, say exactly that — `check-line-cap exit 1 (message not recognised)` — rather than printing
   nothing. An unrecognised failure is still a failure.
3. `run_on` must check the checkout succeeded before reading the gates. Empty output must never mean clean;
   distinguish "ran and said nothing" from "did not run".
4. Compare the FULL output of `queue-check` for the inherited-failure suppression, not one line.
5. Add the rule to `CLAUDE.md` next to the verification section, because this is a fleet rule and not a bug
   in two files: **a runner that invokes a check consumes its exit status; grepping its output for known
   failure strings is forbidden.** Anchor it on identifiers, per the existing rule about comments.

**Red demos are already written**: the reviewers built the attack trees with `git mktree` / `commit-tree`
and recorded the SHAs. Reuse them rather than inventing new ones, and cite them.

**Scope, because two agents are already in these files.** The per-file fixes for `ops/merge-rehearse`
(PR #55's critical and highs) and `ops/pr-ci-preflight` (PR #48's critical and highs) are in flight on
`task/T-0065` and `task/T-0075` as of 2026-09-08. **Do not redo them.** What is left for this task, and what
neither reviewer could see because each was shown one tool:

  * the observation that these are ONE defect in two files, so a fix in one that the other does not adopt
    leaves the class open;
  * the `CLAUDE.md` rule, which is the only artifact that outlives both files;
  * **verifying that both fixes read the exit code rather than adding the missing patterns.** If either one
    landed as a longer regex, the class is not closed and this task says so with the transcript.

**Do not** fix this by adding the missing message patterns. That is what was done last time, it is why the
patterns are out of date again, and it is the shape [[T-0080]] proved does not converge for pin assertions:
enumerating the ways something can fail never finishes.

## Log
- 2026-09-08T11:03:47Z claimed by agent/claude-opus-5; lease until 2026-09-08T14:03:47Z
