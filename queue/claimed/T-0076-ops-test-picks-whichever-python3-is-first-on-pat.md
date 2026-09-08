---
id: T-0076
title: ops/test picks whichever python3 is first on PATH, which here is a different interpreter without pytest
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:59:03Z
lease_expires_at: 2026-09-08T08:59:03Z
worktree: wt/T-0077
branch: task/T-0077
exclusive: []
touches: [ops/test, ops/lib/boot.sh]
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
- 2026-09-08T02:59:03Z claimed by agent/claude-opus-5; lease until 2026-09-08T08:59:03Z
- 2026-09-08 agent/claude-opus-5, round three. Fixed on task/T-0077, which carries [[T-0077]] too: the two
  tasks are the same expression in the same files. `touches:` widened to `[ops/test, ops/lib/boot.sh]`.

  **The box still has the two interpreters this task was filed against** (verbatim):

      python3 -> /c/Users/phineasf/AppData/Local/Microsoft/WindowsApps/python3
        C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe   3.14.5    pytest: False
      python  -> /c/Users/phineasf/AppData/Local/Programs/Python/Python310/python
        C:\Users\phineasf\AppData\Local\Programs\Python\Python310\python.exe    3.10.11   pytest: True

  `services/etl/` does NOT exist on main, so the ETL tier is skipped there and the reported symptom cannot
  appear. It was reproduced by materialising the tier the branch that found it had: an untracked
  `services/etl/pyproject.toml` and `tests/test_smoke.py` (removed again before committing; nothing under
  services/etl is in this diff).

  **RED**, `PYTHON` unset, `bash ops/test`:

      PYTHON is: <unset>
      ... Test run with 16 tests in 3 suites passed after 0.046 seconds.
      FAIL: services/etl exists but pytest produced no report
      EXIT=1

  and the cause, in the same directory:

      $ python3 -m pytest -q
      C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe: No module named pytest
      EXIT=1
      $ python -m pytest -q
      . [100%]  1 passed in 0.01s
      EXIT=0

  The guard was doing its job; it just could not tell "the reporter is broken" from "you ran the wrong
  python", and its message named services/etl. It was not weakened.

  **FIX** - `ops/lib/boot.sh`, one place for all eleven wrappers. `scenic_python [module ...]` asks each
  candidate what it CAN DO instead of taking the first NAME that exists: it runs a probe that prints
  `SCENICPY|<sys.executable>|<x.y.z>|<missing modules>` and takes the first candidate at or above Python 3.9
  that has everything asked for. `ops/test` requests the ETL tier's needs up front -
  `if [[ -f services/etl/pyproject.toml ]]; then scenic_python pytest; else scenic_python; fi` - so a python
  without pytest is refused by path and version BEFORE any tier runs, not three tiers later as a missing
  file. The pytest message now names the interpreter (`scenic_py_id`) and prints the exact rerun command,
  and says explicitly that the interpreter was already checked, so this is not the T-0076 case.
  The probe output is PIPE-delimited, not space-delimited, because `sys.executable` is routinely
  `C:\Program Files\...` and a space-split would report the version as `Files\Python312\python.exe`.
  `ops/agent-preflight` stops printing `python3 --version` (the report that hid this) and prints the two
  interpreters ops/* will actually use.

  **GREEN**, identical command, ETL tier present, `PYTHON` unset:

      PYTHON is: <unset>
      ... Test run with 16 tests in 3 suites passed after 0.062 seconds.
      TESTS linux=51/50 ios=skipped failed=0 skipped=0
      OK
      EXIT=0

  and `ops/agent-preflight` now answers the question that cost the original reporter several minutes:

      python        C:\Users\phineasf\AppData\Local\Python\pythoncore-3.14-64\python.exe (3.14.5, via PATH)
      python+pytest C:\Users\phineasf\AppData\Local\Programs\Python\Python310\python.exe (3.10.11, via PATH)

  **SELF-ATTACK on the fix.**

  B1 pin `PYTHON` at a real interpreter that lacks pytest - the neighbour where the operator, not PATH,
  picks wrong. Refused, before any tier ran, naming it:

      test: no usable python.
        needs: python >= 3.9 with pytest
        PYTHON=/c/.../pythoncore-3.14-64/python.exe   candidates tried, in order:
          /c/.../python.exe -> C:\Users\...\pythoncore-3.14-64\python.exe (3.14.5) has no pytest
        PYTHON is set, so it is the ONLY candidate - unset it to search PATH.
      EXIT=2

  B2 the harder neighbour: a PATH shim where NEITHER `python3` NOR `python` has pytest, so there is no
  right answer to fall back to. Refuses instead of picking one, and names all three candidates:

      test: no usable python.
        needs: python >= 3.9 with pytest
        PYTHON=<unset>   candidates tried, in order:
          python3 -> ...pythoncore-3.14-64\python.exe (3.14.5) has no pytest
          python  -> ...pythoncore-3.14-64\python.exe (3.14.5) has no pytest
          py      -> ...pythoncore-3.14-64\python.exe (3.14.5) has no pytest
      EXIT=2

  B3 `PYTHON=true`, which [[T-0072]] refused in ops/check-pins ONLY. Now refused everywhere:
  ops/check-pins EXIT=2, ops/queue-check EXIT=2, ops/sane EXIT=2 (queue-check used to exit 0, silently).

  B4 the four-line script that defeated T-0072's probe by echoing `pins-probe-ok`: now refused
  ("not a usable python3 (probe produced no answer)", EXIT=2).

  B5 **a NEW two-line script written against MY probe. IT PASSES. THIS ROUTE IS NOT CLOSED:**

      $ cat .artifacts/adv/fakepy2.sh
      #!/usr/bin/env bash
      echo "SCENICPY|/opt/definitely-python/python3|3.99.0|-"
      exit 0
      $ PYTHON="$PWD/.artifacts/adv/fakepy2.sh" bash ops/check-pins
      check-pins: note: PYTHON=.../fakepy2.sh -> /opt/definitely-python/python3 (3.99.0), not the PATH default
      SCENICPY|/opt/definitely-python/python3|3.99.0|-
      EXIT=0

  That is not a bug in the probe; it is what a probe IS. A probe asks the thing under test to describe
  itself, using a token printed in the script the adversary is reading, so any token can be echoed and any
  new token can be echoed too - the next fake is two characters longer, not harder. **The written decision,
  recorded in ops/lib/boot.sh and ops/check-pins rather than left to omission: `PYTHON=` is honoured, it is
  a real local need, and it is NOT a security boundary. The probe exists for the ACCIDENT - no python, a
  python2, a python without the modules the script needs - which is what T-0076 actually was, and it names
  the interpreter, its real sys.executable and its version when it refuses.** Anyone who can set PYTHON can
  also edit the wrapper; the defence there is the reviewer and the pre-commit hook, not a shell test.
  The only thing added against B5 is an audit line, not a gate: when PYTHON is set, every wrapper prints
  `note: PYTHON=... -> <exe> (<ver>), not the PATH default` to stderr, so a forged run does not look
  identical in the transcript to an honest one. With PYTHON unset, stderr is 0 bytes (measured).

  B6 the parser neighbour: a shim answering with `SCENICPY|C:\Program Files\Py 3.12\python.exe|3.12.1|-`.
  Parsed whole - `C:\Program Files\Py 3.12\python.exe (3.12.1, via PYTHON=)` - not split on the spaces.

  **Not touched: `FAIL: services/api exists but vitest produced no report`.** That message is misleading for
  the same reason (it names the tier, the cause is a missing node_modules) and it is [[T-0040]]'s subject,
  whose `touches:` is ops/test. I hit it on this box before running `npm ci` and left it alone.

  Gates: `TESTS linux=50/50 ios=skipped failed=0 skipped=0 / OK` (ETL tier removed again),
  `PINS ok=9 ... failed=0`, `QUEUE OK (76 tasks)`, `SANE OK`, `PREFLIGHT OK`.
