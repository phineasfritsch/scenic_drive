---
id: T-0061
title: pin assertions shell out to git ls-files, so they cannot run from WSL either
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/lib/, pins/PINS.yaml]
pins_affected: []
reviewer: null
depends_on: [T-0055]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0055 fixed the ops WRAPPERS so they no longer ask git where the repo is. That exposed the layer underneath:
the pin ASSERTIONS shell out to `git ls-files` themselves, so `ops/check-pins` now RUNS from WSL and then
fails.

    P-OPS-01 output: only 0 files tracked under ops/ and .githooks/ (expected >= 17).
      An empty or truncated set must never read as 'all modes correct'.
    P-SRC-02 output: An empty or truncated set must never read as 'no file exceeds 300 lines'.

**Read those two lines carefully, because they are the good news.** They are T-0019's and T-0037's vacuity
guards firing. Without them, `ops/check-pins` from WSL would have reported that every file mode is correct and
no file exceeds 300 lines - over an EMPTY SET, on a machine where nothing had been examined at all. That is a
false pass on the repo's own integrity checks, and it is exactly the failure both guards were written for
against a hypothetical. The first time the door was actually opened, they held.

So this task is not urgent in the fail-open sense. It is the other half of T-0055's job.

- Every `ops/lib/check-*` that calls `git ls-files`, `git rev-parse` or `git cat-file` needs to work from a
  shell whose git cannot read the worktree - or to say plainly that it cannot run there, which is already
  what happens and is arguably fine.
- Decide which. "Make them work" and "make them refuse legibly" are different products: the first needs a way
  to enumerate tracked files without git (or a git invocation that works over `/mnt/c`), the second is a
  clearer message than a vacuity-guard failure that reads like a real violation.
- **Do not weaken the vacuity guards to make this quieter.** They are the reason this is a visible failure
  instead of a silent pass, and a reviewer should refuse any diff that relaxes a MIN_FILES-style floor.
- Demonstrate red: run `ops/check-pins` from WSL before and after, and show the difference between "0 files
  tracked" and whatever the fixed behaviour is.
- Note the ordering: if T-0060 is settled by moving the repo to ext4, this task evaporates. Check T-0060's
  state before starting.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from T-0055.
