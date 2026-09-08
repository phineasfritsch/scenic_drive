---
id: T-0087
title: three ops entry points print a Python traceback instead of a usage line
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T04:05:00Z
lease_expires_at: 2026-09-08T10:05:00Z
worktree: wt/T-0087
branch: task/T-0087
exclusive: []
touches: [ops/lib/queue.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Three small, verified findings from the round-three verification of [[T-0077]], grouped because they are the
same kind of thing: an `ops/*` entry point behaving unlike every other one.

**1. A raw traceback instead of a usage line.** `ops/claim`, `ops/lock` and `ops/new-task` given no arguments
print

    IndexError: list index out of range

from `cmd_new`. Verified pre-existing rather than a regression — `git show HEAD~1:ops/new-task` reproduces it
identically. Every other `ops/*` entry point prints a usage line and exits 2, and `ops/merge` and
`ops/merge-rehearse` both refuse unknown arguments explicitly. A traceback tells an agent the tool is broken
when the tool is fine and the call was wrong.

**2. `check-exec-bits` and `check-line-cap` report GREEN about a foreign repository** when invoked directly
from inside one:

    P-OPS-01: 19 files, 15 required present, all modes correct    EXIT=0

Their vacuity guards (`MIN_FILES=17`, `MIN_FILES=5`) hide this on a thin fake repo — the fake has to be stocked
past the floor before it shows, which is why nobody hit it. That is the [[T-0086]] class in two more files, and
the fix belongs with that task rather than here; recorded so it is not lost. Ownership sits with T-0036 and
with the T-0035/T-0037/T-0043/T-0058/T-0062 chain.

**3. An adversarial fixture for `ops/test` cannot live inside the worktree.** SwiftPM walks UP the directory
tree looking for `Package.swift`, so a synthetic repo built under `.artifacts/` made `swift test` find and run
the **real** package's 16 tests, silently. Any future fixture that needs a fake repo for `ops/test` must be
built outside the worktree — and note this interacts with the `/tmp` rule in CLAUDE.md, since `/tmp` is not one
directory here. Worth a line in CLAUDE.md once somebody needs it.

Also recorded from the same run, and NOT a defect: `services/etl` does not exist on `main`, so [[T-0076]]'s
symptom is unreproducible there — the ETL tier is skipped entirely. A reviewer verifying T-0076 must
materialise the tier (a `pyproject.toml` and one test) or they will see a green `ops/test` and wrongly conclude
the defect is absent.

- Item 1 is the actual work here and is small: usage line, exit 2, matching the other entry points.
- Items 2 and 3 are recorded for the tasks that own them; do not fix them under this id without saying so.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-three verification of T-0077. All three were executed
  by an agent that did not write the fix.
- 2026-09-08T04:05:00Z claimed by agent/claude-opus-5; lease until 2026-09-08T10:05:00Z
