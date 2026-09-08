---
id: T-0066
title: ops/check-pins reports failed=0 and exits 0 when it ran no assertion at all
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-08T01:19:36Z
lease_expires_at: 2026-09-08T05:19:36Z
worktree: wt/T-0066
branch: task/T-0066
exclusive: []
touches: [ops/lib/pins.py]
pins_affected: []
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

**`ops/check-pins` can report success having executed nothing, and three separate one-word edits reach that
state.** Found by the self-referential-check sweep, every case executed rather than reasoned about:

    (a) delete every pin from pins/PINS.yaml, keeping the header comments
        -> PINS ok=0 skipped=0 pending=0 expired=0 failed=0 tier=linux   exit 0
        -> identical under --source-only

    (b) change `anchor: source` to `anchor: sources` - one typo, five lines
        -> the CI job `pins-source-only` prints ok=0 skipped=12 ... failed=0, exit 0
        -> the import ban and the 300-line cap stop running on every push, with nothing red

    (c) no file edit at all: `ops/check-pins --tier bogus`
        -> ok=0 skipped=9 pending=3 expired=0 failed=0 tier=bogus        exit 0
        control: the same tree with --tier linux gives ok=1 ... failed=8, so the harness does execute
        assertions when it is not being fooled

**Why it is hollow.** The exit code derives only from `failed` and `expired`, both counted while iterating
the very list the run is supposed to prove non-empty. `load()` on a PINS.yaml with no `- id:` items returns
`[]` with no error. So the population being checked and the evidence that checking happened come from the
same file.

**This is the third instance of one bug.** agent/reviewer-5 fixed exactly this in `ops/lib/check-exec-bits`
(MIN_FILES + a REQUIRED list). agent/reviewer-10 fixed it in `ops/lib/check-line-cap`. **The runner that
executes both of those fixed checks never got the guard itself.** Case (b) is the one that matters most:
`pins-source-only` is the per-push gate, so a typo in a data file silently disables the import ban for
everybody, and nothing anywhere goes red.

- Assert the run actually executed assertions: a floor on the number of pins loaded, and a floor on the
  number that were RUN rather than skipped for the current tier.
- Refuse an unrecognised `--tier`. Case (c) needs no file edit at all, which makes it the easiest to hit by
  accident and the hardest to notice.
- Consider a REQUIRED list of pin ids that must exist, the way `check-exec-bits` has one for paths - a pin
  that silently disappears from PINS.yaml is the same failure as one that never ran.
- Demonstrate red for all three cases above, and green after. Case (b) must be demonstrated against
  `--source-only` specifically, because that is the mode the push gate uses.
- Do NOT weaken the skip logic to make this quieter. `runs_on` skipping is correct behaviour; the defect is
  that a run which skipped EVERYTHING reports success.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from a repo-wide sweep for checks whose expected value comes from
  the thing they check. Eight surfaces, two adversarial verifiers per finding, each required to execute its
  falsification.
- 2026-09-08T01:19:36Z claimed by agent/claude-opus-5; lease until 2026-09-08T05:19:36Z
- 2026-09-08 agent/claude-opus-5 fixed in `ops/lib/pins.py` (269 lines, under the cap). Guards follow the
  shape of `ops/lib/check-exec-bits` (MIN_FILES + REQUIRED) and `ops/lib/check-line-cap` (MIN_FILES): module
  constants `TIERS`, `MIN_PINS=10`, `MIN_RAN=6`, `MIN_RAN_SOURCE_ONLY=2`, `REQUIRED` (12 ids), `REQUIRED_SOURCE`
  (P-SRC-01, P-SRC-02 must carry `anchor: source`); strict `parse_args` refuses an unknown argument or tier
  with exit 2; `ran` counts only pins whose assertion was executed. The `runs_on` skip logic is untouched.

  BASELINE (unchanged before and after the fix):

      $ bash ops/check-pins
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --source-only
      PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
      EXIT=0

  RED (a) every pin deleted from pins/PINS.yaml, header comments kept:

      $ bash ops/check-pins
      PINS ok=0 skipped=0 pending=0 expired=0 failed=0 tier=linux
      EXIT=0
      $ bash ops/check-pins --source-only
      PINS ok=0 skipped=0 pending=0 expired=0 failed=0 tier=linux source-only
      EXIT=0

  GREEN (a) same edit, same two commands:

      $ bash ops/check-pins
      PINS FAIL: only 0 pin(s) loaded from pins/PINS.yaml (expected >= 10).
        An empty or truncated pin list must never read as 'every load-bearing property holds'.
      EXIT=1
      $ bash ops/check-pins --source-only
      PINS FAIL: only 0 pin(s) loaded from pins/PINS.yaml (expected >= 10).
        An empty or truncated pin list must never read as 'every load-bearing property holds'.
      EXIT=1

  RED (b) `sed -i 's/^  anchor: source$/  anchor: sources/' pins/PINS.yaml` (4 lines changed), demonstrated
  against `--source-only` because that is what the `pins-source-only` push gate runs. `import SwiftUI` was
  prepended to Sources/ScenicKit/Geo/Geo.swift for the same run, so the gate had a real violation to catch:

      $ bash ops/check-pins --source-only
      PINS ok=0 skipped=12 pending=0 expired=0 failed=0 tier=linux source-only
      EXIT=0

  GREEN (b) same one-word typo:

      $ bash ops/check-pins --source-only
      PINS FAIL: pin(s) the --source-only push gate exists for are not anchor: source: P-SRC-01 (anchor: 'sources') P-SRC-02 (anchor: 'sources').
        The import ban and the 300-line cap would stop running on every push with nothing red.
      EXIT=1

  RED (c) no file edit at all:

      $ bash ops/check-pins --tier bogus
      PINS ok=0 skipped=9 pending=3 expired=0 failed=0 tier=bogus
      EXIT=0

  GREEN (c):

      $ bash ops/check-pins --tier bogus
      PINS FAIL: unknown --tier 'bogus'; accepted: --tier <linux|mac>, --source-only, --verbose. An unknown tier matches no runs_on, so every pin would skip and the run would report failed=0
      EXIT=2
      $ bash ops/check-pins --tier
      PINS FAIL: --tier needs a value; accepted: --tier <linux|mac>, --source-only, --verbose
      EXIT=2
      $ bash ops/check-pins --sourceonly
      PINS FAIL: unrecognised argument '--sourceonly'; accepted: --tier <linux|mac>, --source-only, --verbose
      EXIT=2
      $ bash ops/check-pins --tier mac
      PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac
      EXIT=0

  The other two guards, each seen red (a check nobody has seen fail is not a check). P-GIT-01's block deleted:

      $ bash ops/check-pins
      PINS FAIL: required pin id(s) absent from pins/PINS.yaml: P-GIT-01.
        A pin that silently disappears is the same failure as one that never ran.
      EXIT=1

  and the run-floor alone, with P-SRC-01/P-SRC-02 `runs_on` narrowed to `[mac]` (no expiry attaches to mac, so
  nothing else fires) — note `failed=0` on the summary line and exit 1 anyway, which is the whole point:

      $ bash ops/check-pins --source-only
      PINS ok=1 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only
       - only 1 assertion(s) actually ran for tier=linux --source-only (expected >= 2)
            Skipping is correct; reporting success after skipping everything is not.
      EXIT=1

  GATES in wt/T-0066: `bash ops/queue-check` -> `QUEUE OK (66 tasks)` exit 0; `bash ops/sane` -> `SANE OK`
  exit 0; `bash ops/agent-preflight` -> `PREFLIGHT OK` exit 0; `bash ops/check-pins` and
  `bash ops/check-pins --source-only` as in BASELINE above, both exit 0. `bash ops/test` exits 1 with
  `FAIL: services/api exists but vitest produced no report` — PRE-EXISTING and not from this change: the
  identical command on the unmodified tree (`git checkout -- ops/lib/pins.py`, then re-run) prints the same
  line and the same exit 1. `services/api/node_modules` is absent in this worktree; `npm ci` has never run
  here, and CI installs it in the `core` job.

- 2026-09-08 adversarial verification by a second agent that did not write the fix. **holds = false.**
  The fix is real and its own transcript reproduces; it does not survive contact. Reproduced first,
  then every evasion below was EXECUTED, not argued. Full report follows verbatim so the next person
  inherits the limits along with the code.

  # Adversarial verification of T-0066 — holds = False
  
  ## Verdict
  
  HOLDS = FALSE. The fix is real and its own transcript reproduces byte-for-byte, but it does not survive adversarial contact.
  
  WHAT IS GENUINELY GOOD. Eight distinct evasions went red, including all three cases the fix names and five shapes it does not claim. The `ran` counter is truly independent of the summary line (evasion 3 prints `failed=0` while exiting 1). The floors are hard module literals in ops/lib/pins.py, NOT derived from pins/PINS.yaml — the repo's signature recurring bug is absent in that form, and I checked. parse_args refused all ten argv shapes I threw at it, including `--tier human` and `--tier device` (real runs_on values) and `--tier --source-only` (fails safe). Process claims all check out: 269 lines, two files in the commit, PINS.yaml untouched, mode 100755, ops/sane green, branch pushed.
  
  THE FINDING (evasions 9 and 10). The run-floor's deliberate headroom is a hole big enough to walk a load-bearing pin through. A one-line, data-only edit — P-SRC-01's `runs_on: [linux, mac]` -> `runs_on: []`, id present, `anchor: source` intact, so check_population is fully satisfied — stops the Apple-import ban from ever executing, and BOTH `bash ops/check-pins` and `bash ops/check-pins --source-only` exit 0 with failed=0. I did not stop at "this would fail": I injected `import CoreLocation` into Sources/ScenicKit/Model/Coordinate.swift under `#if canImport(CoreLocation)` (so the tree still compiles and no other pin goes red — exactly the "compiles and tests pass on the Mac" case P-SRC-01's own why_no_test_catches_it describes), confirmed P-SRC-01's assertion exits 1 by hand, and watched the push gate print `ok=2 ... failed=0 / EXIT=0`. The control — same broken tree, PINS.yaml restored — goes red with failed=1. Bisected: 3 pins can be silenced on the full run and 1 on the --source-only gate before the floor bites.
  
  ROOT CAUSE. The header comment at ops/lib/pins.py:45 says "Floors sit below the current counts so a deliberate removal has headroom; REQUIRED carries the precision." That is the overclaim. REQUIRED carries precision on EXISTENCE only (`pid not in by_id`); nothing anywhere asserts that a named pin actually RAN. The guard counts how many assertions executed but never checks WHICH, so identity is enforced for presence and only cardinality for execution. Suggested shape, matching the fix's own idiom: a REQUIRED_RAN set checked after the loop — every id in it must have been executed, or be legitimately pending, or be skipped with unexpired human/device evidence. That closes the gap without touching the runs_on skip logic.
  
  TWO LESSER FINDINGS. (11) Rewriting every `assertion:` to `"true"` yields output byte-identical to the healthy baseline — the TODO check catches an empty assertion but nothing catches a vacuous one. (12) `PYTHON=true bash ops/check-pins` prints nothing at all and exits 0; this is pre-existing in the ops/check-pins shim (verified byte-identical at b340c60^), untouched by this fix, but it means the hardened module can be bypassed with no file edit.
  
  RECOMMENDATION. Do not merge as done. The fix is a real improvement and should be kept — but the case-(b) scenario it was written to prevent (the import ban silently off on every push) is still reachable through a different field, in one line, so the task's acceptance criterion is not met. Send back for REQUIRED_RAN; findings 11 and 12 are worth separate queue entries rather than scope creep here.
  
  WORKTREE STATE. All edits reverted with `git checkout --` after each attempt; helper scripts were written to the session scratchpad, never into the repo. Final `git status --short` printed no output (clean), HEAD still b340c60, and the baseline re-runs still print `ok=9 ... EXIT=0` and `ok=3 ... EXIT=0`.
  
  FILES: C:\Users\phineasf\Documents\GitHub\wt\T-0066\ops\lib\pins.py (lines 45, 52-56 REQUIRED/REQUIRED_SOURCE, 226 the `tier in runs_on` gate, 258-265 the floor); C:\Users\phineasf\Documents\GitHub\wt\T-0066\ops\check-pins (the PYTHON override); C:\Users\phineasf\Documents\GitHub\wt\T-0066\pins\PINS.yaml; C:\Users\phineasf\Documents\GitHub\wt\T-0066\Sources\ScenicKit\Model\Coordinate.swift (injection target, restored).
  
  ## Evasions executed
  
  ### 1. CAUGHT — REPRODUCTION FIRST (not an evasion): ran the fixer's entire claimed transcript verbatim on an unmodified tree.
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only ; bash ops/check-pins --tier bogus ; bash ops/check-pins --tier ; bash ops/check-pins --sourceonly ; bash ops/check-pins --tier mac
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux / EXIT=0
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only / EXIT=0
  PINS FAIL: unknown --tier 'bogus'; accepted: --tier <linux|mac>, --source-only, --verbose. An unknown tier matches no runs_on, so every pin would skip and the run would report failed=0 / EXIT=2
  PINS FAIL: --tier needs a value; ... / EXIT=2
  PINS FAIL: unrecognised argument '--sourceonly'; ... / EXIT=2
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=mac / EXIT=0
  
  Every line matches the fixer's report byte-for-byte. Also verified: ops/lib/pins.py is 269 lines (under the 300 cap), commit b340c60 touches exactly ops/lib/pins.py + the queue task file, pins/PINS.yaml is unchanged in the commit (git diff --name-only b340c60^ b340c60 -- pins/PINS.yaml => 0 files), both files are mode 100755, branch is pushed to origin, and `bash ops/sane` prints SANE OK / EXIT=0.
  ```
  
  ### 2. CAUGHT — EVASION 1 - empty the population the guard iterates. Deleted every pin from pins/PINS.yaml, keeping only the header comments.
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only
  PINS FAIL: only 0 pin(s) loaded from pins/PINS.yaml (expected >= 10).
    An empty or truncated pin list must never read as 'every load-bearing property holds'.
  EXIT=1
  (identical for --source-only, EXIT=1)
  ```
  
  ### 3. CAUGHT — EVASION 2 - stay ABOVE the MIN_PINS floor while deleting load-bearing pins. Removed the P-GIT-01 and P-ATTR-02 blocks, leaving exactly 10 pins so len(pins) >= MIN_PINS=10 is satisfied.
  
  ```
  $ bash ops/check-pins
  PINS FAIL: required pin id(s) absent from pins/PINS.yaml: P-GIT-01 P-ATTR-02.
    A pin that silently disappears is the same failure as one that never ran.
  EXIT=1
  ```
  
  ### 4. CAUGHT — EVASION 3 - typo one field name so the population silently becomes empty rather than wrong. Renamed every `runs_on:` key to `runs_onx:` (a valid identifier, so the parser accepts it silently).
  
  ```
  $ bash ops/check-pins
  PINS ok=0 skipped=9 pending=3 expired=0 failed=0 tier=linux
   - only 0 assertion(s) actually ran for tier=linux (expected >= 6)
        Skipping is correct; reporting success after skipping everything is not.
  EXIT=1
  
  This is the sharpest of the red demos: the summary line still says failed=0, but the run exits 1. The ran counter is genuinely independent of the summary line, as claimed.
  ```
  
  ### 5. CAUGHT — EVASION 4 - null out one operand of the `tier in runs_on` equality. Rewrote every `runs_on:` value to the empty list `[]`.
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only
  PINS ok=0 skipped=9 pending=3 expired=0 failed=0 tier=linux
   - only 0 assertion(s) actually ran for tier=linux (expected >= 6)
  EXIT=1
  
  PINS ok=0 skipped=11 pending=1 expired=0 failed=0 tier=linux source-only
   - only 0 assertion(s) actually ran for tier=linux --source-only (expected >= 2)
  EXIT=1
  ```
  
  ### 6. CAUGHT — EVASION 5 - make the equality vacuously false by case. Rewrote `runs_on: [linux, mac]` to `[Linux, Mac]` and `[linux]` to `[Linux]`, so `tier in runs_on` never matches while the file still reads correct to a human.
  
  ```
  $ bash ops/check-pins
  PINS ok=0 skipped=9 pending=3 expired=0 failed=0 tier=linux
   - only 0 assertion(s) actually ran for tier=linux (expected >= 6)
        Skipping is correct; reporting success after skipping everything is not.
  EXIT=1
  ```
  
  ### 7. CAUGHT — EVASION 6 - the anchor typo the source-only push gate exists to prevent (the fixer's case (b)). Changed `anchor: source` to `anchor: sources` on P-SRC-01 and P-SRC-02 only (a 2-line diff).
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins
  PINS FAIL: pin(s) the --source-only push gate exists for are not anchor: source: P-SRC-01 (anchor: 'sources') P-SRC-02 (anchor: 'sources').
    The import ban and the 300-line cap would stop running on every push with nothing red.
  EXIT=1
  (identical for the plain invocation, EXIT=1 - the anchor guard runs in both modes)
  ```
  
  ### 8. CAUGHT — EVASION 7 - abuse the one non-failing path. `pending:` is documented as reported-but-not-failing, so I made EVERY pin pending on T-0066 (a task live in queue/claimed/, so the pending-debt check is satisfied). failed=0 with zero assertions executed.
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only
  PINS ok=0 skipped=0 pending=12 expired=0 failed=0 tier=linux
   - only 0 assertion(s) actually ran for tier=linux (expected >= 6)
  EXIT=1
  
  PINS ok=0 skipped=8 pending=4 expired=0 failed=0 tier=linux source-only
   - only 0 assertion(s) actually ran for tier=linux --source-only (expected >= 2)
  EXIT=1
  ```
  
  ### 9. CAUGHT — EVASION 8 - argv fuzzing beyond the three shapes the fixer tried: equals-form, real-but-non-tier runs_on values, empty string, case variants, single-dash, trailing positional, and --tier swallowing the next flag.
  
  ```
  $ bash ops/check-pins --tier=linux ; --tier human ; --tier device ; --tier "" ; --TIER linux ; --source-only=1 ; --tier linux --tier bogus ; -source-only ; --source-only extra ; --tier --source-only
  All ten refused, all EXIT=2. Notably:
  --tier=linux  -> PINS FAIL: unrecognised argument '--tier=linux'
  --tier human  -> PINS FAIL: unknown --tier 'human'    (a real runs_on value, still refused)
  --tier device -> PINS FAIL: unknown --tier 'device'
  --tier ""     -> PINS FAIL: unknown --tier ''
  --tier --source-only -> PINS FAIL: unknown --tier '--source-only'  (fails safe rather than silently dropping the flag)
  No argv shape reached a zero-assertion exit 0.
  ```
  
  ### 10. *** UNCAUGHT *** — EVASION 9 (PASSED - THE FINDING) - keep every REQUIRED id present and every REQUIRED_SOURCE anchor intact; just stop ONE load-bearing pin from ever running. One-line, data-only edit to pins/PINS.yaml: P-SRC-01's `runs_on: [linux, mac]` -> `runs_on: []`. Then injected the exact violation P-SRC-01 exists to catch into Sources/ScenicKit/Model/Coordinate.swift, wrapped in `#if canImport(CoreLocation)` so the tree still compiles and every other pin stays green - i.e. precisely the 'code compiles and tests pass on the Mac' scenario P-SRC-01's own why_no_test_catches_it describes.
  
  ```
  $ bash ops/check-pins --source-only ; bash ops/check-pins ; bash ops/check-pins --tier mac   # with the banned import present in Sources/
  First, proof the guarded property is genuinely violated - P-SRC-01's own assertion, run by hand:
    $ bash -o pipefail -c "! grep -rEn '^\s*(@testable\s+)?import\s+(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)' Sources/"
    Sources/ScenicKit/Model/Coordinate.swift:3:import CoreLocation
    P-SRC-01 assertion EXIT=1
  
  Now the guard on that same tree:
    $ bash ops/check-pins --source-only   # the push gate
    PINS ok=2 skipped=9 pending=1 expired=0 failed=0 tier=linux source-only
    EXIT=0
    $ bash ops/check-pins
    PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=linux
    EXIT=0
    $ bash ops/check-pins --tier mac
    PINS ok=8 skipped=1 pending=3 expired=0 failed=0 tier=mac
    EXIT=0
  
  CONTROL (proves the runs_on edit is what defeats it, not the import being undetectable): restored pins/PINS.yaml, left the banned import in place, same command:
    PINS ok=2 skipped=8 pending=1 expired=0 failed=1 tier=linux source-only
     - P-SRC-01: Root-package targets import Foundation only - never CoreLocation, MapKit, UIKit, SwiftUI, MapLibre, Ferrostar
          output: Sources/ScenicKit/Model/Coordinate.swift:3:import CoreLocation
    EXIT=1
  
  So a one-line data edit converts a red run into a green one, with a banned Apple import sitting in Sources/.
  ```
  
  ### 11. *** UNCAUGHT *** — EVASION 10 (PASSED) - quantify how wide the headroom in evasion 9 is. Silenced N REQUIRED pins by emptying runs_on, ids and anchors untouched, and bisected the floor.
  
  ```
  $ silence P-SRC-01 P-GIT-01 P-DATA-02 -> bash ops/check-pins ; then add P-ATTR-02 ; then silence P-SRC-01 P-SRC-02 -> bash ops/check-pins --source-only
  3 REQUIRED pins silenced (tier=linux):
    PINS ok=6 skipped=3 pending=3 expired=0 failed=0 tier=linux
    EXIT=0                                <-- still green
  4 REQUIRED pins silenced:
    PINS ok=5 skipped=4 pending=3 expired=0 failed=0 tier=linux
     - only 5 assertion(s) actually ran for tier=linux (expected >= 6)
    EXIT=1
  Both REQUIRED_SOURCE pins silenced, --source-only:
    PINS ok=1 skipped=10 pending=1 expired=0 failed=0 tier=linux source-only
     - only 1 assertion(s) actually ran for tier=linux --source-only (expected >= 2)
    EXIT=1
  
  The hole is exactly 3 pins wide on the full run (MIN_RAN=6 vs 9 today) and exactly 1 pin wide on the --source-only push gate (MIN_RAN_SOURCE_ONLY=2 vs 3 today).
  ```
  
  ### 12. *** UNCAUGHT *** — EVASION 11 (PASSED) - keep the ran count high but make every assertion vacuous. Rewrote every `assertion:` value in pins/PINS.yaml to `"true"`.
  
  ```
  $ bash ops/check-pins ; bash ops/check-pins --source-only
  PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
  EXIT=0
  PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
  EXIT=0
  
  Byte-identical to the healthy baseline. Every load-bearing property in the repo is unenforced and the output is indistinguishable from green. The existing TODO check covers `assertion: TODO` but nothing covers a semantically vacuous assertion. Weaker than evasion 9 (it needs a 12-line diff, and `ran` is honest that 9 processes were spawned), but recorded because the output carries zero signal.
  ```
  
  ### 13. *** UNCAUGHT *** — EVASION 12 (PASSED, pre-existing, not introduced by this fix) - bypass the hardened module entirely via the entrypoint's env override. ops/check-pins is `exec "${PYTHON:-$(command -v python3 || command -v python)}" .../pins.py "$@"`, so PYTHON selects the interpreter. No file edit at all.
  
  ```
  $ PYTHON=true bash ops/check-pins ; PYTHON=true bash ops/check-pins --source-only
  (no output at all)
  EXIT=0
  (no output at all)
  EXIT=0
  
  Verified pre-existing: `git show b340c60^:ops/check-pins` is byte-identical to the current file, so the fix neither introduced nor closed this. A run that prints nothing whatsoever still exits 0, so no caller can distinguish it from a pass.
  ```
