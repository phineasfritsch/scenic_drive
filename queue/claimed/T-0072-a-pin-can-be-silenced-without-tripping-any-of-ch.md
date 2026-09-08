---
id: T-0072
title: a pin can be silenced without tripping any of check-pins' new floors
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T02:03:31Z
lease_expires_at: 2026-09-08T06:03:31Z
worktree: wt/T-0066
branch: task/T-0066
exclusive: []
touches: [ops/lib/pins.py, ops/check-pins]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Follow-up to [[T-0066]], whose fix added `MIN_PINS`, `MIN_RAN`, `MIN_RAN_SOURCE_ONLY`, a `REQUIRED` list of
pin ids and a `REQUIRED_SOURCE` anchor check to `ops/lib/pins.py`. A second agent reproduced that fix's
transcript, then executed thirteen evasions against it. **Nine went red. Four did not.** The full report is
in T-0066's `## Log`; the four open routes are:

**1. A pin can be silenced one line at a time, and no floor notices.** Set one pin's `runs_on: [linux, mac]`
to `runs_on: []`. Its id is still in `REQUIRED`, its `anchor` is still `source`, `MIN_PINS` is satisfied, and
`MIN_RAN` is satisfied by the pins that still run. The verifier did this to **P-SRC-01**, then injected the
exact import violation P-SRC-01 exists to catch into `Sources/ScenicKit/Model/Coordinate.swift` wrapped in
`#if canImport(CoreLocation)` — so the tree still compiles and every other pin stays green. That is precisely
the "code compiles and tests pass on the Mac" scenario P-SRC-01's own `why_no_test_catches_it` field
describes. `check-pins` reported success.

**2. The floor has headroom, and it was measured.** The verifier bisected: several REQUIRED pins can be
silenced this way before `MIN_RAN` trips. `MIN_RAN = 6` against 9 running today is not a ratchet, it is a
suggestion. This is the same slack problem as [[T-0071]] in a different file.

**3. `assertion: "true"` keeps the ran count high and asserts nothing.** Rewriting every `assertion:` value in
`pins/PINS.yaml` to `"true"` leaves `ran` at its full value, every floor satisfied, `failed=0`, exit 0. The
`ran` counter proves an assertion was *executed*, not that it *asserted anything* — the guard counts calls,
not content.

**4. `PYTHON=` bypasses the hardened module entirely, with no file edit.** `ops/check-pins` is
`exec "${PYTHON:-$(command -v python3 || command -v python)}" .../pins.py "$@"`, so the environment chooses
the interpreter. Pre-existing, not introduced by T-0066, and it defeats every guard in the file at once. The
same shape exists in `ops/queue-check`, `ops/new-task`, `ops/claim` and every other `ops/*` wrapper. Decide
whether that is acceptable (it is a local convenience knob, and an attacker with the environment already has
the box) or whether CI should pin the interpreter — but decide it explicitly rather than by omission, and if
it stays, say so in the file.

**The pattern, which is the point.** Each of the three fixes verified this round hardened the specific hole it
was pointed at and left the property reachable by a neighbouring route. T-0066 hardened *how many* pins run;
routes 1 and 3 change *which* and *what*. See [[T-0073]] and [[T-0074]] for the same shape in two other files.

- Route 1 is the one that matters: a REQUIRED pin must be required to RUN, not merely to exist. `runs_on: []`
  on a pin in `REQUIRED` should be a failure, not a skip.
- Route 3 wants the assertion to be non-trivial. A cheap, honest version: refuse an assertion that is a
  bare truth literal, and keep `TODO` failing as it already does.
- Re-ratchet the floors to just under today's counts and say in the log what they were when set.
- Demonstrate each red then green. Route 1's demonstration must include the injected import violation, or it
  proves only that the flag changed and not that the pin came back to life.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the adversarial verification of T-0066, every case executed by
  an agent that did not write the fix.
- 2026-09-08T02:03:31Z claimed by agent/claude-opus-5; lease until 2026-09-08T06:03:31Z
- 2026-09-08 agent/claude-opus-5 fixed in `ops/lib/pins.py` (297 lines, under the cap) and `ops/check-pins`
  (18 lines). Round two of [[T-0066]]: only the four routes its adversarial verification left open, plus the
  adjacent route to each. Every transcript below was executed in wt/T-0066 on branch task/T-0066; red is
  taken against HEAD dac14c3 (the T-0066 fix), green against the working tree, with the SAME command.

  WHAT CHANGED. `REQUIRED_RAN` (9 ids) and `REQUIRED_RAN_SOURCE` (2 ids): a pin named there must have
  EXECUTED its assertion for the mode being run, tracked in an `executed` set beside the existing `ran`
  counter and reported after the summary line. Floors re-ratcheted from MIN_PINS=10/MIN_RAN=6/
  MIN_RAN_SOURCE_ONLY=2 to 12/9/3 — the counts measured on this tree, recorded in the file next to the
  constants. `vacuous()` + `TRUTHY`: an assertion that cannot fail now fails the pin the way `TODO` does.
  `ops/check-pins` probes its interpreter and writes the `PYTHON=` decision down. The `runs_on` skip logic is
  untouched. Incidental, to fit the 300-line cap: `import os` (unused), two comment lines, and the
  five-line `bad` printer folded to three with byte-identical output.

  BASELINE, unchanged before and after (byte-for-byte the same as T-0066's):

      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0
      $ bash ops/check-pins --tier mac
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac
      EXIT=0

  ---- ROUTE 1: a REQUIRED pin silenced by `runs_on: []` --------------------------------------------------

  Setup for both transcripts (one line of data, plus the violation P-SRC-01 exists to catch, wrapped in
  `#if canImport(CoreLocation)` so the tree still compiles and no other pin goes red):

      $ git diff -U0 -- pins/PINS.yaml | grep -E '^[-+]  runs_on'
      -  runs_on: [linux, mac]
      +  runs_on: []
      $ grep -n "import CoreLocation" Sources/ScenicKit/Model/Coordinate.swift
      3:import CoreLocation
      $ bash -o pipefail -c "! grep -rEn '^\s*(@testable\s+)?import\s+(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)' Sources/"
      Sources/ScenicKit/Model/Coordinate.swift:3:import CoreLocation
      P-SRC-01 assertion EXIT=1          <- the guarded property is genuinely violated

  RED (HEAD dac14c3):

      $ bash ops/check-pins --source-only
      PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0
      $ bash ops/check-pins
      PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --tier mac
      PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=mac
      EXIT=0

  GREEN (same edit, same three commands, banned import still in Sources/):

      $ bash ops/check-pins --source-only
      PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
       - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
            Skipping is correct; reporting success after skipping everything is not.
       - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01
            Present is not enforced: runs_on, pending and anchor each silence a pin whose id, anchor and assertion all still read correct.
      EXIT=1
      $ bash ops/check-pins
      PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
       - only 8 assertion(s) actually ran for tier=linux (expected >= 9)
            Skipping is correct; reporting success after skipping everything is not.
       - required pin(s) never executed their assertion for tier=linux: P-SRC-01
            Present is not enforced: runs_on, pending and anchor each silence a pin whose id, anchor and assertion all still read correct.
      EXIT=1
      $ bash ops/check-pins --tier mac
      PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=mac
       - only 8 assertion(s) actually ran for tier=mac (expected >= 9)
            Skipping is correct; reporting success after skipping everything is not.
       - required pin(s) never executed their assertion for tier=mac: P-SRC-01
            Present is not enforced: runs_on, pending and anchor each silence a pin whose id, anchor and assertion all still read correct.
      EXIT=1

  CONTROL, both runs: PINS.yaml restored, banned import left in place — the pin does its job either way, so
  it is the `runs_on` edit that was defeating the gate, not the import being undetectable:

      PINS ok=2 skipped=8 pending=1 expired=0 failed=1 tier=linux source-only
       - P-SRC-01: Root-package targets import Foundation only - never CoreLocation, MapKit, UIKit, SwiftUI, MapLibre, Ferrostar
            output: Sources/ScenicKit/Model/Coordinate.swift:3:import CoreLocation
      EXIT=1

  ROUTE 1, ADJACENT — the same silencing through two other fields, same injected import. Both were green at
  HEAD and both are red now; `runs_on: []` was only the cheapest of three.

      1b-i   -  runs_on: [linux, mac]            1b-ii  +  pending: T-0072   (a task live in queue/claimed/)
             +  runs_on: [mac]

      RED  1b-i  $ bash ops/check-pins             PINS ok=8 skipped=1 pending=3 ... failed=0   EXIT=0
      RED  1b-i  $ bash ops/check-pins --source-only  PINS ok=2 skipped=9 pending=1 ... failed=0   EXIT=0
      RED  1b-ii $ bash ops/check-pins             PINS ok=8 skipped=0 pending=4 ... failed=0   EXIT=0
      RED  1b-ii $ bash ops/check-pins --source-only  PINS ok=2 skipped=8 pending=2 ... failed=0   EXIT=0

      GREEN 1b-i  $ bash ops/check-pins
      PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
       - only 8 assertion(s) actually ran for tier=linux (expected >= 9)
       - required pin(s) never executed their assertion for tier=linux: P-SRC-01
      EXIT=1
      GREEN 1b-i  $ bash ops/check-pins --source-only
      PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
       - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
       - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01
      EXIT=1
      GREEN 1b-ii $ bash ops/check-pins
      PINS ok=8 skipped=0 pending=4 expired=0 failed=0 tier=linux
       - only 8 assertion(s) actually ran for tier=linux (expected >= 9)
       - required pin(s) never executed their assertion for tier=linux: P-SRC-01
      EXIT=1
      GREEN 1b-ii $ bash ops/check-pins --source-only
      PINS ok=2 skipped=8 pending=2 expired=0 failed=0 tier=linux source-only
       - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
       - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01
      EXIT=1

  A third adjacent shape was tried and was ALREADY closed at HEAD, so it is recorded, not fixed: satisfy
  REQUIRED_RAN with a decoy — silence the real P-SRC-01 and append a second `- id: P-SRC-01` whose assertion
  is real but harmless (`test -f Package.swift`). The pre-existing duplicate-id check catches it in both:

      RED and GREEN alike:  PINS ok=9 skipped=1 pending=3 expired=0 failed=1 tier=linux
                             - P-SRC-01: duplicate id
                            EXIT=1

  ---- ROUTE 2: the floor's headroom, measured then removed ------------------------------------------------

  RED (HEAD). Silencing REQUIRED pins one at a time with `runs_on: []`, ids and anchors untouched:

      1 silenced  PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux   EXIT=0
      2 silenced  PINS ok=7 skipped=2 pending=3 expired=0 failed=0 tier=linux   EXIT=0
      3 silenced  PINS ok=6 skipped=3 pending=3 expired=0 failed=0 tier=linux   EXIT=0
      4 silenced  PINS ok=5 skipped=4 pending=3 expired=0 failed=0 tier=linux
                   - only 5 assertion(s) actually ran for tier=linux (expected >= 6)
                  EXIT=1
      both REQUIRED_SOURCE silenced, --source-only:
                  PINS ok=1 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only
                   - only 1 assertion(s) actually ran for tier=linux --source-only (expected >= 2)
                  EXIT=1

  So the headroom was exactly 3 REQUIRED pins on the full run and 1 on the push gate.

  GREEN. Identical script, first silencing now red:

      1 silenced  PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
                   - only 8 assertion(s) actually ran for tier=linux (expected >= 9)
                   - required pin(s) never executed their assertion for tier=linux: P-SRC-01
                  EXIT=1
      2 silenced  ... expected >= 9 ... never executed: P-SRC-01 P-GIT-01                     EXIT=1
      3 silenced  ... expected >= 9 ... never executed: P-SRC-01 P-GIT-01 P-DATA-02           EXIT=1
      4 silenced  ... expected >= 9 ... never executed: P-SRC-01 P-GIT-01 P-DATA-02 P-ATTR-02 EXIT=1
      both REQUIRED_SOURCE silenced, --source-only:
                  PINS ok=1 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only
                   - only 1 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
                   - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01 P-SRC-02
                  EXIT=1

  THE COUNTS AS SET, all measured on this tree on 2026-09-08 and written into the file beside the constants:
  12 pins load in every mode (MIN_PINS 10 -> 12); `bash ops/check-pins` ran 9 and `--tier mac` ran 9
  (MIN_RAN 6 -> 9); `bash ops/check-pins --source-only` ran 3 (MIN_RAN_SOURCE_ONLY 2 -> 3).

  The ratchet does work that REQUIRED_RAN alone does not — P-SAFE-05 is not in REQUIRED_RAN_SOURCE, so
  moving it out of the push gate with `anchor: source -> artifact` is caught only by the count:

      RED  $ bash ops/check-pins --source-only
      PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0
      GREEN $ bash ops/check-pins --source-only
      PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
       - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
      EXIT=1

  And MIN_PINS=12 now bites one pin short instead of three (P-ATTR-02's block deleted, 11 pins left):

      GREEN $ bash ops/check-pins
      PINS FAIL: only 11 pin(s) loaded from pins/PINS.yaml (expected >= 12).
        An empty or truncated pin list must never read as 'every load-bearing property holds'.
      EXIT=1

  ---- ROUTE 3: `assertion: "true"` ------------------------------------------------------------------------

  RED (HEAD), every non-TODO `assertion:` in pins/PINS.yaml rewritten to `"true"` (10 lines changed):

      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0

  GREEN, same edit, same commands:

      $ bash ops/check-pins
      PINS ok=0 skipped=0 pending=3 expired=0 failed=9 tier=linux
       - P-SRC-01: assertion 'true' cannot fail whatever the tree contains - a truth literal executes, and asserts nothing
       - P-SRC-02: assertion 'true' cannot fail whatever the tree contains - a truth literal executes, and asserts nothing
       - P-OPS-01: ... - P-GIT-01: ... - P-DATA-02: ... - P-TEST-01: ... - P-PROC-01: ... - P-ATTR-02: ...
       - P-SAFE-05: assertion 'true' cannot fail whatever the tree contains - a truth literal executes, and asserts nothing
       - only 0 assertion(s) actually ran for tier=linux (expected >= 9)
       - required pin(s) never executed their assertion for tier=linux: P-SRC-01 P-SRC-02 P-OPS-01 P-GIT-01 P-DATA-02 P-TEST-01 P-PROC-01 P-ATTR-02 P-SAFE-05
      EXIT=1
      $ bash ops/check-pins --source-only
      PINS ok=0 skipped=8 pending=1 expired=0 failed=3 tier=linux source-only
       - P-SRC-01: assertion 'true' cannot fail whatever the tree contains - a truth literal executes, and asserts nothing
       - P-SRC-02: ...   - P-SAFE-05: ...
       - only 0 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
       - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01 P-SRC-02
      EXIT=1

  ROUTE 3, ADJACENT — the same effect through other always-true forms, each applied to every assertion.
  All four were exit 0 at HEAD; all four are exit 1 now:

      assertion: ":"           RED  PINS ok=9 ... failed=0 EXIT=0   GREEN failed=9, "assertion ':' cannot fail ..." EXIT=1
      assertion: "exit 0"      RED  PINS ok=9 ... failed=0 EXIT=0   GREEN failed=9, "assertion 'exit 0' ..."        EXIT=1
      assertion: "true ; true" RED  PINS ok=9 ... failed=0 EXIT=0   GREEN failed=9, "assertion 'true ; true' ..."   EXIT=1
      assertion: "test 1 = 1"  RED  PINS ok=9 ... failed=0 EXIT=0   GREEN failed=9, "assertion 'test 1 = 1' ..."    EXIT=1

  A CORRECTION, recorded because the first attempt was invalid. `/bin/true` appeared to be caught at HEAD,
  but git-bash MSYS had rewritten the literal in argv to `C:/Program Files/Git/usr/bin/true`, which fails on
  the space — so that run tested nothing. Re-done with MSYS_NO_PATHCONV=1 so the real literal reaches the file:

      $ grep -n 'assertion: "/bin/true"' pins/PINS.yaml | head -1
      13:  assertion: "/bin/true"
      RED  $ bash ops/check-pins    PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux   EXIT=0
      GREEN $ bash ops/check-pins
      PINS ok=0 skipped=0 pending=3 expired=0 failed=9 tier=linux
       - P-SRC-01: assertion '/bin/true' cannot fail whatever the tree contains - a truth literal executes, and asserts nothing
      EXIT=1

  `vacuous()` was also table-tested in both directions, because a refusal that also refuses real assertions
  would be worse than the hole. 25 vacuous forms (`true`, `TRUE`, `:`, `exit 0`, `/bin/true`, `true && true`,
  `true || true`, `(true)`, `true | true`, `test 1 = 1`, `[ 1 = 1 ]`, `[[ x == x ]]`, `test 0 -eq 0`,
  `[ -n x ]`, `[ 1 ]`, `true # grep -q foo Package.swift`, empty, comment-only, ...) against 18 real ones
  (all 9 live assertions in pins/PINS.yaml plus other real shapes):

      $ python .artifacts/T-0072/vacuous_table.py
      vacuous(): 25 refused-cases, 18 kept-cases, 0 wrong
      EXIT=0

  ITS LIMIT, stated rather than implied: `vacuous()` refuses a truth literal or a tautological `test`/`[ ]`.
  It cannot refuse an assertion that is real but weak — `grep -q '' Package.swift`, or P-SRC-01 rewritten to
  grep a directory that does not exist. Closing that needs mutation testing (flip the tree, require the
  assertion to go red), which is a bigger change than this task and is filed as a finding below.

  ---- ROUTE 4: `PYTHON=` chooses the interpreter -----------------------------------------------------------

  DECIDED, not left to omission, and the decision is written in `ops/check-pins` itself: the override is
  KEPT. A venv, a pyenv shim or an explicit python3.12 is a real local need; it is not a security boundary,
  because anyone who can set the environment already owns the box; and CI never sets it — the two jobs in
  .github/workflows/linux-core.yml install python3 and run `bash ops/check-pins` with no PYTHON in scope, so
  pinning the interpreter there would pin something nothing varies. What is NOT a convenience, and is now
  closed, is the silent form: a run that printed nothing and exited 0, which no caller can distinguish from
  a pass. The shim probes the interpreter and refuses a non-Python value with exit 2.

  RED (HEAD), no file edit at all:

      $ PYTHON=true bash ops/check-pins
      EXIT=0                             <- and no output whatsoever
      $ PYTHON=echo bash ops/check-pins
      C:/Users/phineasf/Documents/GitHub/wt/T-0066/ops/lib/pins.py
      EXIT=0
      $ PYTHON=cat bash ops/check-pins
      (the entire source of ops/lib/pins.py)
      EXIT=0
      $ PYTHON=true bash ops/check-pins --source-only
      EXIT=0

  GREEN, same four commands:

      $ PYTHON=true bash ops/check-pins
      PINS FAIL: PYTHON=true does not resolve to a working python3 (tried: true).
        Refusing to exit 0 without loading a single pin, let alone running an assertion.
      EXIT=2
      $ PYTHON=echo bash ops/check-pins        (same two lines, "tried: echo")     EXIT=2
      $ PYTHON=cat bash ops/check-pins         (same two lines, "tried: cat")      EXIT=2
      $ PYTHON=true bash ops/check-pins --source-only                              EXIT=2

  The convenience still works, and a typo'd path now refuses instead of half-running:

      $ PYTHON=python bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ PYTHON=$(command -v python) bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0
      $ PYTHON=/no/such/python bash ops/check-pins
      PINS FAIL: PYTHON=/no/such/python does not resolve to a working python3 (tried: /no/such/python).
        Refusing to exit 0 without loading a single pin, let alone running an assertion.
      EXIT=2

  ---- T-0066's own guards, re-run so this change is not a regression ---------------------------------------

      $ (a) every pin deleted, header comments kept -> bash ops/check-pins   and   --source-only
      PINS FAIL: only 0 pin(s) loaded from pins/PINS.yaml (expected >= 12).   EXIT=1  (both)
      $ (b) sed -i 's/^  anchor: source$/  anchor: sources/' pins/PINS.yaml -> bash ops/check-pins --source-only
      PINS FAIL: pin(s) the --source-only push gate exists for are not anchor: source: P-SRC-01 (anchor: 'sources') P-SRC-02 (anchor: 'sources').
      EXIT=1
      $ (c) bash ops/check-pins --tier bogus   EXIT=2 ; --tier  EXIT=2 ; --sourceonly  EXIT=2   (messages unchanged)
      $ bash ops/check-pins --verbose  ->  "  ok      P-SRC-01" ... EXIT=0

  ---- GATES in wt/T-0066 ------------------------------------------------------------------------------------

      $ bash ops/queue-check              QUEUE OK (69 tasks)                                            EXIT=0
      $ bash ops/check-pins               PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux    EXIT=0
      $ bash ops/check-pins --source-only PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only  EXIT=0
      $ bash ops/sane                     SANE OK                                                        EXIT=0
      $ bash ops/agent-preflight          PREFLIGHT OK                                                   EXIT=0
      $ bash ops/test                     FAIL: services/api exists but vitest produced no report        EXIT=1

  `ops/test` is the same PRE-EXISTING failure T-0066 recorded, and this change cannot reach it: `grep -n
  pins ops/test` returns only the two `pins/floor_*.txt` reads, so ops/test never invokes ops/check-pins or
  ops/lib/pins.py. `services/api/node_modules` is absent in this worktree; CI installs it in the `core` job.
  The Swift half passed on the same run: `Test run with 16 tests in 3 suites passed`.

  ---- NOTES AND NEW FINDINGS --------------------------------------------------------------------------------

  * `touches:` was widened on this task and on [[T-0066]] from one entry to `[ops/lib/pins.py, ops/check-pins]`.
    The pre-commit hook resolves the touches list from the BRANCH name, so on task/T-0066 it reads T-0066's
    file whatever task is actually being worked; both were updated so the two staged paths are allowed and
    the record is honest. This task's own `touches:` had named only `ops/check-pins`, which is not where the
    T-0066 fix lives.
  * FINDING (new, not fixed here — outside `touches:`). The re-ratcheted floors are module constants, and
    `.githooks/commit-msg` guards only `pins/floor_linux.txt` and `pins/floor_ios.txt`. `MIN_RAN = 9 -> 6` is
    a one-line edit with no `floor-lower:` justification required and nothing red — the same shape applies to
    `MIN_FILES` in `ops/lib/check-exec-bits` and `ops/lib/check-line-cap`. A ratchet whose notch can be moved
    silently is a suggestion again, one commit later.
  * FINDING (new, not fixed here). `vacuous()` refuses assertions that cannot fail; nothing refuses an
    assertion that is real but no longer points at the property (P-SRC-01 rewritten to grep `Sources2/`
    passes and enforces nothing). The honest closure is mutation testing: for each REQUIRED_RAN pin, inject
    the violation it names and require the assertion to go red. That is a task, not a line.
  * The `PYTHON=` shape closed here in `ops/check-pins` is still open in `ops/queue-check`, `ops/new-task`,
    `ops/claim`, `ops/sane` and every other `ops/*` wrapper. One line each; not in this task's `touches:`.
  * Scripts used are in `.artifacts/T-0072/` (gitignored, never committed): `route1.sh`, `route1b.sh`,
    `route234.sh`, `route3_bintrue.sh`, `adjacent2.sh`, `regress.sh`, `vacuous_table.py`, plus the helpers
    `silence.py`, `vacuous.py`, `drop_pin.py`, `decoy.py`, `coord_inject.swift`. Every edit to
    `pins/PINS.yaml` and `Sources/ScenicKit/Model/Coordinate.swift` was reverted with `git checkout --`;
    `git status --short` after the last run shows only `ops/check-pins` and `ops/lib/pins.py` modified.

- 2026-09-08 round-two adversarial verification, by an agent that did not write the fix.
  **holds = false.**

  **CORRECTION TO THIS TASK FILE.** The entry above records all four routes as closed. Two are not, and this
  line is here because a task file claiming a closed route is worse than one that never claimed it:

    ROUTE 3 is OPEN. The verbatim round-one evasion (`assertion: "true"` on every pin) now goes red. Two more
    characters do not: `assertion: "true || false"` is accepted by `vacuous()`, executes, exits 0, and
    reproduces the round-one green byte for byte with a banned `import CoreLocation` sitting in
    `Sources/ScenicKit/Model/Coordinate.swift`. 28 of 32 cannot-fail shapes tested are accepted. Deleting one
    alternative from P-SRC-01's real regex - still a genuine grep that can fail - is green too.

    ROUTE 4 is HALF OPEN, and the half that is missing was not mentioned. `PYTHON=true` now exits 2, but a
    four-line script that answers the probe token and then does nothing still passes. Worse, and separately:
    `ops/check-pins` locates the module with `git rev-parse --show-toplevel`, so running THIS repo's
    check-pins from inside any other git repo executes THAT repo's `ops/lib/pins.py`. The verifier got
    `PINS ok=99 ... failed=0`, exit 0, from a synthetic repo, with nothing in this one modified. Pre-existing
    - `git show dac14c3:ops/check-pins` has the same line - and not introduced here, but it defeats every
    guard in the file at once and the task file does not say so.

  What IS closed, and it is real: routes 1 and 2, plus all four round-one survivors re-run verbatim. Today's
  headroom is exactly zero (ran=9 against MIN_RAN=9). The floors are hard literals, not derived from
  PINS.yaml. `ROOT` now comes from `__file__`, so all four entry points keep their guards.

  Every evasion below was EXECUTED. Full report verbatim, so the next person inherits the limits
  along with the code.

  # Round-two adversarial verification of T-0072 — holds = False
  
  ## Round-one routes still open
  
  - ROUTE 3 (`assertion` that cannot fail) — the VERBATIM round-one evasion (`assertion: "true"` on every pin) now goes RED, but the route itself is wide open: appending two characters, `assertion: "true || false"`, is accepted by vacuous(), executes, exits 0, and reproduces the round-one green byte-for-byte with a banned `import CoreLocation` in Sources/. 28 of 32 cannot-fail shapes I table-tested are accepted. The task file records this route as closed=true; it is not.
  
  - ROUTE 4 (`PYTHON=` bypass) — the VERBATIM round-one evasion (`PYTHON=true`) now goes RED with exit 2, but the route is only half closed and the fixer says so in the file: `PYTHON=<binary that echoes the probe token> bash ops/check-pins` still prints nothing and exits 0. Additionally the same shim line resolves the module via `git rev-parse --show-toplevel`, so `bash <this-repo>/ops/check-pins` run from any OTHER git repo executes THAT repo's ops/lib/pins.py — I got `PINS ok=99 ... failed=0 / EXIT=0` from a synthetic repo. The task file records this route as closed=true (with the hostile-PYTHON caveat); the module-path half is not mentioned.
  
  
  ## Verdict
  
  HOLDS = FALSE. Round two is a genuine improvement and its own transcript reproduces exactly — but the task file now records all four routes as closed=true, and two of them are not.
  
  WHAT IS REAL. All four round-one survivors, re-run verbatim, now go red: `runs_on: []` on P-SRC-01 (exit 1 in all three modes, naming P-SRC-01 in the new "never executed" line), the three-pin headroom bisect (exit 1), `assertion: "true"` on every pin (failed=9, exit 1), and `PYTHON=true` (exit 2 with a reason). round1RoutesStillOpen as literally defined — round-one commands that still pass — is EMPTY. REQUIRED_RAN/REQUIRED_RAN_SOURCE work: they caught `runs_on: []`, a single-pin `runs_on` key typo, and `pending: <live task>`, each printing the pin id. The floors are hard literals, not derived from PINS.yaml, and today's headroom is exactly zero (ran=9 vs MIN_RAN=9; source-only ran=3 vs floor 3). Nine argv shapes round one never tried were all refused or behaved. Four entry points (subdirectory, outside the repo, module direct, module direct from outside) all keep every guard, because ROOT comes from `__file__`. `anchor: [source]` (type change) is refused. Process claims check out: 297 lines, both files 100755, commit 3fb8968 touches only the two ops files and the two queue files, pins/PINS.yaml is not in the commit, queue-check/sane/agent-preflight green, tree clean.
  
  THE FINDINGS — seven fresh evasions passed, six of them reaching the exact scenario the task exists to prevent: a banned `import CoreLocation` sitting in Sources/ with `bash ops/check-pins`, `--source-only` and `--tier mac` all printing the healthy baseline and exiting 0.
  
  1. ROUTE 3 IS OPEN, one line wide. `assertion: "true || false"` — two characters more than the round-one evasion the fix names — is accepted by `vacuous()` because it refuses only when EVERY fragment split on `;|&`/`&&`/`||` is a truth literal. One line of pins/PINS.yaml turns the import ban off and the run stays byte-identical to green. Table-tested 32 cannot-fail shapes: 28 are accepted, including `bash -c true`, `{ true; }` (while `(true)` is refused), `echo ok`, `test -d .`, `cd .`, `eval true`, `exit $((0))`.
  
  2. A DUPLICATE `assertion:` KEY IN THE SAME BLOCK SHADOWS THE REAL ONE, silently. `load()` keeps the last value for a repeated key; a second `assertion: "test -d ."` three lines below the real one leaves the correct assertion visible on line 13 to any reviewer, marks P-SRC-01 EXECUTED, satisfies every floor, and prints the healthy baseline with the banned import present. This is the sharpest evasion I found and it defeats REQUIRED_RAN's core promise — "the pin executed its assertion" is true, of the wrong assertion.
  
  3. THE RATCHET IS SATISFIABLE BY ADDING A CHEAP PIN. The fixer's ROUTE 2 claim (`anchor: source -> artifact` on P-SAFE-05 is caught) is true alone — I reproduced exit 1 — but one appended filler pin with `anchor: source` restores ran=3 and both modes go green with the USNO solar oracle no longer on the push gate.
  
  4. THE FLOOR IS A SNAPSHOT, NOT A RATCHET. Any pin added after 2026-09-08 arrives with one pin of fresh headroom and no REQUIRED_RAN entry, so it can be silenced with `runs_on: []` in one line and both modes stay green (measured: ok=10 -> ok=9, EXIT=0 both times). REQUIRED_RAN is a hand-maintained literal that nothing forces anyone to update.
  
  5. ROUTE 4 IS HALF OPEN, AS DISCLOSED, PLUS A HALF THAT IS NOT DISCLOSED. `PYTHON=<script that echoes pins-probe-ok>` prints nothing and exits 0 — confirmed, and the file says so. Not said: `ops/check-pins:18` locates the module with `git rev-parse --show-toplevel`, i.e. from the CALLER's CWD rather than from the script's own directory, so `bash <this-repo>/ops/check-pins` executed inside any other git repo runs THAT repo's ops/lib/pins.py. From a synthetic repo I got `PINS ok=99 ... failed=0 / EXIT=0`. Pre-existing (identical at dac14c3), but it is in the file this fix edited and reasoned about, and it is the same failure class the probe was added to close.
  
  6. Minor, structural: `executed` is keyed on the id string alone, so the decoy-duplicate-pin evasion was stopped only by the pre-existing duplicate-id check — note the absence of any "never executed" line in that transcript. And `ops/lib/pins.py` at 297 lines is under a cap nothing enforces: `ops/lib/check-line-cap` reads `git ls-files 'Sources/**/*.swift' 'Tests/**/*.swift'` only (T-0058 already filed).
  
  RECOMMENDATION. Keep the fix — it closes all four recorded round-one evasions and that is real. Do not mark routes 3 and 4 closed. Route 3 needs the assertion CONTENT pinned, not its shape: the cheapest honest version is a hash or a required-substring per REQUIRED_RAN id (e.g. P-SRC-01's assertion must contain `CoreLocation` and `Sources/`), since no vacuity heuristic will ever refuse `true || false` and `echo ok` and still accept real assertions. `load()` should refuse a duplicate key inside a block outright — that is a five-line fix and it kills finding 2. The shim should use `$(dirname "$(readlink -f "$0")")` instead of `git rev-parse --show-toplevel`.
  
  WORKTREE STATE. Every edit reverted with `git checkout -- .` after each attempt. Nothing created under queue/ or services/ (`git status --porcelain -uall queue services` -> no output). Helper scripts lived in the gitignored `.artifacts/verify-T-0072/` and were deleted; the synthetic repo lived in the session scratchpad, outside the repo, and was deleted. No commit, no push, main never touched. HEAD is still 3fb8968 and the baseline re-runs still print `ok=9 ... EXIT=0` and `ok=3 ... EXIT=0`. Final command: `git status --short` -> no output (clean).
  
  ## Evasions executed
  
  ### 1. CAUGHT — none — STEP 1 reproduction of the fixer's own gates on an unmodified tree at HEAD 3fb8968
  
  ```
  $ bash ops/queue-check ; bash ops/check-pins ; bash ops/check-pins --source-only ; bash ops/check-pins --tier mac ; bash ops/sane ; bash ops/agent-preflight
  QUEUE OK (69 tasks) / EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac / EXIT=0
  SANE OK / EXIT=0
  PREFLIGHT OK / EXIT=0
  Also verified: ops/lib/pins.py = 297 lines, ops/check-pins = 18 lines; git ls-files -s -> both 100755; commit 3fb8968 touches ops/check-pins, ops/lib/pins.py and the two queue files only (pins/PINS.yaml NOT in the commit).
  ```
  
  ### 2. CAUGHT — ROUND-ONE EVASION 9 re-run verbatim: pins/PINS.yaml P-SRC-01 `runs_on: [linux, mac]` -> `runs_on: []`, plus the banned import injected into Sources/ScenicKit/Model/Coordinate.swift under `#if canImport(CoreLocation)`. Setup proved: `bash -o pipefail -c "! grep -rEn '^\s*(@testable\s+)?import\s+(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)' Sources/"` -> Sources/ScenicKit/Model/Coordinate.swift:3:import CoreLocation, EXIT=1
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins ; bash ops/check-pins --tier mac
  PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
   - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
   - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01
  EXIT=1
  PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
   - only 8 assertion(s) actually ran for tier=linux (expected >= 9)
   - required pin(s) never executed their assertion for tier=linux: P-SRC-01
  EXIT=1
  PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=mac
   - only 8 assertion(s) actually ran for tier=mac (expected >= 9)
   - required pin(s) never executed their assertion for tier=mac: P-SRC-01
  EXIT=1
  (was EXIT=0 in all three modes in round one)
  ```
  
  ### 3. CAUGHT — ROUND-ONE EVASION 10 re-run verbatim: silence three REQUIRED pins by emptying runs_on — P-SRC-01, P-GIT-01, P-DATA-02 (round one measured exactly 3 pins of headroom here and stayed green)
  
  ```
  $ bash ops/check-pins
  PINS ok=6 skipped=3 pending=3 expired=0 failed=0 tier=linux
   - only 6 assertion(s) actually ran for tier=linux (expected >= 9)
   - required pin(s) never executed their assertion for tier=linux: P-SRC-01 P-GIT-01 P-DATA-02
  EXIT=1
  (was EXIT=0 in round one)
  ```
  
  ### 4. CAUGHT — ROUND-ONE EVASION 11 re-run verbatim: rewrite every `assertion:` value in pins/PINS.yaml to "true" (12 lines)
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only
  PINS ok=0 skipped=0 pending=3 expired=0 failed=9 tier=linux
   - P-SRC-01: assertion 'true' cannot fail whatever the tree contains - a truth literal executes, and asserts nothing
     ... (same line for P-SRC-02, P-OPS-01, P-GIT-01, P-DATA-02, P-TEST-01, P-PROC-01, P-ATTR-02, P-SAFE-05)
   - only 0 assertion(s) actually ran for tier=linux (expected >= 9)
   - required pin(s) never executed their assertion for tier=linux: P-SRC-01 P-SRC-02 P-OPS-01 P-GIT-01 P-DATA-02 P-TEST-01 P-PROC-01 P-ATTR-02 P-SAFE-05
  EXIT=1
  PINS ok=0 skipped=8 pending=1 expired=0 failed=3 tier=linux source-only ... EXIT=1
  (was byte-identical to the healthy baseline, EXIT=0, in round one)
  ```
  
  ### 5. CAUGHT — ROUND-ONE EVASION 12 re-run verbatim: no file edit, environment only
  
  ```
  $ PYTHON=true bash ops/check-pins ; PYTHON=true bash ops/check-pins --source-only
  PINS FAIL: PYTHON=true does not resolve to a working python3 (tried: true).
    Refusing to exit 0 without loading a single pin, let alone running an assertion.
  EXIT=2
  (identical for --source-only, EXIT=2. Was silent EXIT=0 in round one.)
  ```
  
  ### 6. *** UNCAUGHT *** — FRESH 1 — route 3, adjacent form. Every `assertion:` in pins/PINS.yaml rewritten to "true || false" (two characters more than the round-one evasion the fix names), banned `import CoreLocation` present in Sources/ScenicKit/Model/Coordinate.swift. Setup proof: the real P-SRC-01 assertion run by hand -> Sources/ScenicKit/Model/Coordinate.swift:3:import CoreLocation, EXIT=1
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only ; bash ops/check-pins --tier mac
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT=0
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
  EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac
  EXIT=0
  Byte-identical to the healthy baseline. vacuous() splits on || and && and refuses only when EVERY fragment is a truth literal, so one non-literal fragment disarms it.
  ```
  
  ### 7. *** UNCAUGHT *** — FRESH 2 — the minimal form of FRESH 1. ONE line of pins/PINS.yaml: `-  assertion: "! grep -rEn ...(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)' Sources/"` / `+  assertion: "true || false"` on P-SRC-01. id, anchor: source and runs_on all untouched; banned import still in Sources/.
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins ; bash ops/check-pins --tier mac
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
  EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac
  EXIT=0
  This is the T-0066/T-0072 acceptance scenario exactly — the Apple-import ban off, the push gate green — reached by a one-line data edit through a neighbouring field.
  ```
  
  ### 8. *** UNCAUGHT *** — FRESH 3 — route 3, the fixer's disclosed limit, executed. One token deleted from P-SRC-01's real assertion: `(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)` -> `(MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)`. Still a real grep that can fail; banned `import CoreLocation` present.
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins ; bash ops/check-pins --tier mac
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac / EXIT=0
  Disclosed in ops/lib/pins.py:126-127 ('Bounded: it cannot refuse a grep for something always present') — confirmed open, not a broken claim.
  ```
  
  ### 9. *** UNCAUGHT *** — FRESH 3b — table test of vacuous() vs. reality: 32 candidate assertions, each asked (a) does vacuous() refuse it, (b) what does `bash -o pipefail -c` actually return. Run through the module itself via importlib on ops/lib/pins.py.
  
  ```
  $ python .artifacts/verify-T-0072/vac_table.py
  ACCEPTED BY vacuous() YET CANNOT FAIL: 28
    - true || false / false || true / echo ok / echo ok >/dev/null / printf '' / cd . / pwd >/dev/null / test -d . / [ -d . ] / test -e . / command true / env true / bash -c true / bash -c 'exit 0' / { true; } / if true; then true; fi / while false; do :; done / for i in 1; do :; done / test 1 -lt 2 / test -z '' / grep -q id pins/PINS.yaml / ls >/dev/null / exit $((0)) / true 2>/dev/null / eval true / set -e / unset NOPE / shift 0 || true
  Refused (4): 'true; true', '(true)', 'true # real check disabled', ': || :'. Note `(true)` is refused but `{ true; }` is not.
  ```
  
  ### 10. CAUGHT — FRESH 4 — decoy duplicate id. P-SRC-01 `runs_on: []`, plus an appended second block with `id: P-SRC-01`, `anchor: source`, `runs_on: [linux, mac]`, `assertion: "test -d ."` so the decoy lands in the `executed` set on the real pin's behalf. Banned import present.
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins
  PINS ok=3 skipped=9 pending=1 expired=0 failed=1 tier=linux source-only
   - P-SRC-01: duplicate id
  EXIT=1
  PINS ok=9 skipped=1 pending=3 expired=0 failed=1 tier=linux
   - P-SRC-01: duplicate id
  EXIT=1
  Caught — but ONLY by the pre-existing duplicate-id check: note there is no 'never executed' line, i.e. the decoy DID satisfy REQUIRED_RAN. `executed` is keyed on the id string alone, so the new guard is load-bearing on the old one.
  ```
  
  ### 11. CAUGHT — FRESH 5a — the fixer's own ROUTE 2 claim, tested. P-SAFE-05 `anchor: source` -> `anchor: artifact`, nothing else.
  
  ```
  $ bash ops/check-pins --source-only
  PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
   - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
  EXIT=1
  Claim confirmed as stated.
  ```
  
  ### 12. *** UNCAUGHT *** — FRESH 5b — same edit, plus one appended filler pin (`id: P-FILL-01`, `anchor: source`, `runs_on: [linux, mac]`, `assertion: "test -f README.md"`) to put the source-only ran count back to 3. Satisfy the floor while removing the thing that mattered.
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins ; bash ops/check-pins --source-only --verbose
  PINS ok=3 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
  EXIT=0
  PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT=0
  --verbose shows what now runs on the push gate:
    ok      P-SRC-01
    ok      P-SRC-02
    ok      P-FILL-01
  P-SAFE-05 (the USNO solar oracle) is gone from the push gate and both modes are green. The ratchet is satisfiable by adding a cheap pin.
  ```
  
  ### 13. *** UNCAUGHT *** — FRESH 6 — is the floor a ratchet or a snapshot? Append one genuinely load-bearing-looking pin (P-FILL-01, anchor: source, runs_on [linux, mac], real assertion) — it is NOT in REQUIRED_RAN, because REQUIRED_RAN is a hand-maintained literal — then silence it with `runs_on: []` in one line.
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only   # with the new pin live, then again after silencing it
  with the new pin live:
    PINS ok=10 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
    PINS ok=4 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  after `runs_on: []` on that pin:
    PINS ok=9 skipped=1 pending=3 expired=0 failed=0 tier=linux / EXIT=0
    PINS ok=3 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  Every pin added after 2026-09-08 arrives with exactly one pin of fresh headroom and no REQUIRED_RAN entry. 'the first silencing is now red' is true only for the exact 12-pin tree the constants were measured against.
  ```
  
  ### 14. CAUGHT — FRESH 7 — `pending: T-0066` (a task live in queue/claimed/) added to P-SRC-01, banned import present
  
  ```
  $ bash ops/check-pins --source-only
  PINS ok=2 skipped=8 pending=2 expired=0 failed=0 tier=linux source-only
   - only 2 assertion(s) actually ran for tier=linux --source-only (expected >= 3)
   - required pin(s) never executed their assertion for tier=linux --source-only: P-SRC-01
  EXIT=1
  ```
  
  ### 15. CAUGHT — FRESH 8 — typo ONE pin's field name only (round one renamed all of them): P-SRC-01's `  runs_on: [linux, mac]` -> `  runs_on_: [linux, mac]`, a valid identifier the parser accepts silently
  
  ```
  $ bash ops/check-pins
  PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
   - only 8 assertion(s) actually ran for tier=linux (expected >= 9)
   - required pin(s) never executed their assertion for tier=linux: P-SRC-01
  EXIT=1
  ```
  
  ### 16. CAUGHT — FRESH 9 — change the TYPE of the operand the push-gate check compares: P-SRC-01 `anchor: source` -> `anchor: [source]` (a one-element flow list, still reads as 'source' to a human)
  
  ```
  $ bash ops/check-pins --source-only
  PINS FAIL: pin(s) the --source-only push gate exists for are not anchor: source: P-SRC-01 (anchor: ['source']).
    The import ban and the 300-line cap would stop running on every push with nothing red.
  EXIT=1
  ```
  
  ### 17. CAUGHT — FRESH 10 — nine argv shapes round one did not try (case variants, trailing whitespace, repeats, combinations, bare --)
  
  ```
  $ for a in '--tier Linux' '--tier LINUX' '--tier mac --source-only' '--verbose --verbose' '--source-only --source-only' '--tier linux --tier mac' '--' '--tier=mac --source-only'; do bash ops/check-pins $a; done ; bash ops/check-pins --tier "linux "
  --tier Linux              -> PINS FAIL: unknown --tier 'Linux'  EXIT=2
  --tier LINUX              -> PINS FAIL: unknown --tier 'LINUX'  EXIT=2
  --tier "linux "           -> PINS FAIL: unknown --tier 'linux ' EXIT=2
  --                        -> PINS FAIL: unrecognised argument '--' EXIT=2
  --tier=mac --source-only  -> PINS FAIL: unrecognised argument '--tier=mac' EXIT=2
  --tier mac --source-only  -> PINS ok=3 skipped=8 pending=1 ... tier=mac source-only EXIT=0 (legitimate)
  --verbose --verbose       -> full verbose run, EXIT=0 (legitimate)
  --source-only --source-only -> ok=3 ... EXIT=0 (legitimate)
  --tier linux --tier mac   -> ok=9 ... tier=mac EXIT=0 (last wins; still a real tier, still ran 9)
  No argv shape reached a zero-assertion exit 0.
  ```
  
  ### 18. *** UNCAUGHT *** — FRESH 11 — route 4, the half the fixer says is NOT closed. A 4-line /bin/sh script that answers the probe with `pins-probe-ok` and then does nothing, pointed at by PYTHON. No file edit inside the repo.
  
  ```
  $ PYTHON=$PWD/.artifacts/verify-T-0072/fakepy bash ops/check-pins ; PYTHON=... bash ops/check-pins --source-only
  (no output at all)
  EXIT=0
  (no output at all)
  EXIT=0
  Confirmed exactly as the fixer disclosed in ops/check-pins:1-10. A run that prints nothing still exits 0, so no caller can tell it from a pass.
  ```
  
  ### 19. CAUGHT — FRESH 12 — alternate entry points, no file edit: (a) from a subdirectory, (b) from outside any git repo, (c) the module invoked directly, bypassing the shim, (d) the module invoked directly from outside the repo
  
  ```
  $ (cd services && bash ../ops/check-pins) ; (cd /tmp && bash <wt>/ops/check-pins) ; python ops/lib/pins.py --source-only ; (cd /tmp && python <wt>/ops/lib/pins.py)
  a) PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
  b) fatal: not a git repository ... python: can't open file 'C:\Program Files\Git\ops\lib\pins.py' / EXIT=2
  c) PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  d) PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
  ROOT comes from __file__, so the module is CWD-independent and every guard survives all four. No hole here.
  ```
  
  ### 20. *** UNCAUGHT *** — FRESH 13 — the other half of the shim line. `ops/check-pins:18` is `exec "$py" "$(git rev-parse --show-toplevel)/ops/lib/pins.py" "$@"` — the module is located from the CALLER's git toplevel, not from the script's own directory. Created a throwaway git repo in the session scratchpad containing `ops/lib/pins.py` that just prints a green summary line, then ran the real repo's check-pins from inside it. Nothing inside the repo under test was modified. (Pre-existing: `git show dac14c3:ops/check-pins` has the same line.)
  
  ```
  $ cd <unrelated git repo> && bash /c/Users/phineasf/Documents/GitHub/wt/T-0066/ops/check-pins
  PINS ok=99 skipped=0 pending=0 expired=0 failed=0 tier=linux
  EXIT=0
  The interpreter probe added by this fix does not protect the module path. Same class the probe was written to close ('no caller can tell it apart from a pass'), one argument to the left.
  ```
  
  ### 21. *** UNCAUGHT *** — FRESH 14 — the stealthiest one. `load()` keeps the LAST value for a repeated key inside a block. Inserted a second `  assertion: "test -d ."` three lines below P-SRC-01's real assertion (after `added:`). The correct assertion is still there on line 13 for any reviewer to read. Banned `import CoreLocation` present in Sources/.
  
  ```
  $ python -c "...m.load(m.PINS)... print P-SRC-01 assertion" ; bash ops/check-pins --source-only ; bash ops/check-pins ; bash ops/check-pins --tier mac
  the visible assertion is still the real one; the parser keeps the last:
  test -d .
  
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac / EXIT=0
  P-SRC-01 is counted as EXECUTED, every floor is satisfied, vacuous() is bypassed, the summary is byte-identical to the healthy baseline, and the Apple import is in Sources/. A duplicate key in a pin block produces no warning of any kind.
  ```
