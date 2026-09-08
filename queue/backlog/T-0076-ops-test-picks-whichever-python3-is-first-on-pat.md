---
id: T-0076
title: ops/test picks whichever python3 is first on PATH, which here is a different interpreter without pytest
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [ops/test]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

`ops/test` line 15 resolves its interpreter as

    PY="${PYTHON:-$(command -v python3 || command -v python)}"

`python3` wins whenever it exists. On this machine the two names are **different installations**:

    python3  ->  C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe   3.14.5   pytest: False
    python   ->  C:\Users\phineasf\AppData\Local\Programs\Python\Python310\python.exe   3.10.11  pytest: True

So `"$PY" -m pytest` runs an interpreter with no pytest, writes no report, and `ops/test` stops with

    FAIL: services/etl exists but pytest produced no report

**The message blames the wrong thing.** It names `services/etl`, which is fine; the fault is the interpreter.
`python -m pytest` in the same directory prints `46 passed`. Found while demonstrating [[T-0071]], after
several minutes spent looking for a defect in the ETL tier that was not there.

**The guard it defeats is a real one.** That `|| { echo ...; exit 1; }` exists because "a missing report never
counts as zero" - it is the check that stops an agent making a suite green by breaking the reporter. It is
working exactly as designed here; it just cannot tell "the reporter is broken" from "you ran the wrong
python". Do not weaken it.

This is the same knob as [[T-0072]]'s route 4 - `${PYTHON:-...}` - from the other direction. There the concern
is that an env var can bypass a hardened check; here the concern is that the DEFAULT is wrong on a real
developer machine. Both want the same decision made once: what interpreter do `ops/*` scripts run, and how is
that pinned rather than discovered?

- Decide the rule. Candidates: prefer `python` over `python3`; probe each candidate for the modules the script
  needs and pick the first that has them; or refuse with a message that names both interpreters and what each
  is missing. The third is the smallest honest change and matches how the rest of `ops/` reports.
- Whatever is chosen, the failure message must name the interpreter it used and its version. A path and a
  version would have ended this in seconds.
- Every `ops/*` script that resolves `$PY` this way has the same defect - `ops/test`, `ops/check-pins`,
  `ops/queue-check`, `ops/claim`, `ops/new-task` and the rest all share the idiom. Fix it in one place.
- CI is unaffected: ubuntu has one python3 and it has pytest. So this will never be caught by a workflow, only
  by a person, which is an argument for the error message rather than for silent fallback.
- Demonstrate red with `PYTHON=` unset on a machine where the two differ, and green after. If the reviewer's
  box has only one python, say so and demonstrate by pointing `PYTHON` at an interpreter without pytest.

## Log
- 2026-09-08 filed by agent/claude-opus-5, found while producing T-0071's red demonstration. Every command
  above was executed; the two interpreter paths and versions are verbatim output of
  `python3 -c "import sys, importlib.util; ..."` and the same for `python`.
