---
id: T-0080
title: whether an assertion can fail is not decidable by reading it; only mutation can answer it
state: review
owner: agent/pins-mutation
owner_session: d217767a
claimed_at: 2026-09-08T07:12:16Z
lease_expires_at: 2026-09-08T11:12:16Z
worktree: null
branch: task/T-0080
exclusive: []
touches: [ops/lib/pins.py, ops/lib/pins_mutation.py, ops/lib/pins_mutation_cases.py, ops/pins-mutation]
pins_affected: []
reviewer: agent/reviewer-14
depends_on: []
verify: [ops/test, ops/check-pins, ops/pins-mutation]
acceptance:
  - "ops/pins-mutation -> PINS-MUTATION mutable=9 covered=9 cases=29 killed=27 survived=0 gaps=2 errors=0, exit 0"
  - "RED: delete CoreLocation from P-SRC-01's regex in a demo worktree -> ops/check-pins still exits 0, ops/pins-mutation reports SURVIVED and exits 1"
  - "RED: assertion: \"true || false\" on P-GIT-01 -> ops/check-pins still exits 0, ops/pins-mutation reports 2 SURVIVED and exits 1"
  - "RED: the vacuity floor - a cases list of 0 injections must FAIL, not report every pin healthy"
  - "the demo worktree is removed and git status is clean in both the caller's tree and the demo tree"
---
## Brief

[[T-0072]] added `vacuous()` to `ops/lib/pins.py` to refuse an assertion that cannot fail. It refuses
`assertion: "true"`. It accepts `assertion: "true || false"` - two more characters - which executes, exits 0,
and reproduces the round-one green byte for byte with a banned `import CoreLocation` sitting in
`Sources/ScenicKit/Model/Coordinate.swift`. The round-two verifier table-tested 32 cannot-fail shapes through
the real module: **28 were accepted.**

And a syntactic check cannot win this, because the next case is not even vacuous. Deleting one alternative
from P-SRC-01's real regex -

    (CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)  ->  (MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)

- leaves a genuine grep that can absolutely fail, still runs, still counts toward `MIN_RAN`, and no longer
catches the import it was written for. There is no property of the assertion's TEXT that separates that from
the correct one.

**So stop reading assertions and start mutating.** For each pin in `REQUIRED_RAN`, the pin's own
`statement` already names the violation it exists to catch. Inject that violation and require the assertion to
go RED. A pin whose assertion stays green against the thing it names is a dead pin, whatever its text says.

This is the honest closure and it is a task, not a line - which is why the T-0072 fixer filed it rather than
half-attempting it, and that judgement was right.

- Start with the pins where the violation is cheap and reversible to inject: P-SRC-01 (add a banned import),
  P-OPS-01 (chmod a required script), P-SRC-02 (append 301 lines to a tracked file), P-GIT-01, P-PROC-01
  (a task in done/ with owner == reviewer).
- The injection must be reverted whether the check passes or fails. Do it in a scratch worktree, never in the
  caller's tree - and prove the tree is clean afterwards, as the verifiers here are required to.
- Not every pin can be mutation-tested cheaply. Say which and why, in the file, rather than quietly covering a
  subset and reporting a number.
- This is slow. It probably belongs in `ops/check-pins --mutate` run in CI and not on every developer
  invocation - but decide that explicitly, because a check nobody runs is the thing this queue keeps finding.
- `vacuous()` should stay. It is cheap and it catches the careless case; it just must not be described as
  closing this route. [[T-0072]]'s log has been corrected accordingly.

## Log
- 2026-09-08 filed by agent/claude-opus-5 from the round-two adversarial verification of T-0072, which
  executed all 32 shapes through the module rather than reasoning about them.
- 2026-09-08T07:12:16Z claimed by agent/pins-mutation; lease until 2026-09-08T11:12:16Z
- 2026-09-08 agent/pins-mutation. **Delivered:** `ops/pins-mutation` + `ops/lib/pins_mutation.py` (the runner)
  + `ops/lib/pins_mutation_cases.py` (the injections). `ops/lib/pins.py` gains exactly one thing:
  `run(assertion, cwd=None)`, so the mutation runner executes assertions through the same code path
  `check-pins` uses. A second `bash -c` of its own would have proved something about the harness rather than
  about the pin.

  **How it answers the brief.** For each pin, the injections are derived from the pin's own `statement`, applied
  in a throwaway worktree, and the assertion must go RED. 29 injections across the 9 pins that run on this
  tier: 27 must-kill, 2 filed gaps. `covered=9` is not asserted by hand - a pin that runs here with no
  injection FAILS the run (demonstrated red below), so a new pin cannot land quietly uncovered.

  **`touches:` widened** from `[ops/lib/pins.py]` to add the three new paths, deliberately and before the first
  commit. The runner cannot live inside `pins.py`: that file is at its 300-line ceiling with three open PRs
  against it, and more importantly `check-pins` runs on every push and in every preflight and must never write
  to the tree it is checking.

  **`ops/check-pins --mutate` was considered and rejected** (the brief asked for an explicit decision).
  A mutation run creates a worktree and takes ~1m40 here because P-SAFE-05 runs `swift test` four times. Wiring
  it behind a flag on the cheap read-only gate puts an injecting mode one typo away from a developer's own
  checkout. `ops/etl-mutation` (T-0081) already established the separate-entry-point shape for exactly this
  reason, and this follows it: stdlib only, explicit enumerated mutations, clean-tree guard, O_EXCL lock. No
  mutmut, no cosmic-ray - unpinned dependencies are refused here.
  CI: it belongs in `.github/workflows/linux-core.yml` as its own job, not in the per-push `pins-source-only`
  step. That file is outside this task's `touches:` and T-0075 owns what CI actually runs, so the wiring is
  NOT claimed here. Until it is wired, this is a command a human or a reviewer runs; saying otherwise would be
  the "check nobody runs" the brief warns about.

  **`vacuous()` stays.** It is not on this branch at all - T-0072 is still in `queue/claimed/`, so `main` (and
  therefore this worktree) has neither `vacuous()` nor `REQUIRED_RAN`; on this branch even a bare
  `assertion: "true"` is accepted by check-pins. Nothing here removes or weakens it, and when T-0072 merges the
  two are complementary: `vacuous()` is a cheap syntactic floor on every push, this is the empirical gate.
  A note in `pins.py`'s rules block says so at the place a future agent will read it. The runner does not
  import `REQUIRED_RAN` - it derives coverage from `runs_on`/`pending`/`assertion` in PINS.yaml itself, so the
  two lists cannot drift apart into a lie about coverage; when T-0072 lands, `REQUIRED_RAN` and
  `covered=9` are the same nine pins by construction.

  **Covered (9 pins, 27 must-kill injections).** P-SRC-01 (6: one per banned framework - this is what kills the
  brief's regex-alternative deletion), P-SRC-02 (3: over-cap file under Sources/, under Tests/, and the file
  set falling below MIN_FILES), P-OPS-01 (3: a script demoted to 100644, a data file promoted to 100755, a
  required script dropped from the index), P-GIT-01 (2), P-DATA-02 (2), P-TEST-01 (3), P-PROC-01 (2: a done/
  task graded by its own owner, and one with no reviewer), P-ATTR-02 (3), P-SAFE-05 (3: USNO provenance
  replaced by our own output, fixtures cut to 10, the solar math shifted by a 2-degree zenith).

  **NOT covered, and why - no silent skips.** The runner prints these on every run:
  - `P-PROD-01` - `pending: T-0012`. Its assertion is `TODO`; there is nothing to make red. check-pins already
    fails a TODO that outlives its task.
  - `P-COST-02` - `pending: T-0014`. Same.
  - `P-HUMAN-01` - `pending: T-0013` **and** `runs_on: [human]`. A worktree cannot drive five commutes. This is
    the one class mutation genuinely cannot answer; pins.py's expiry ratchet is what covers it.
  There are no `device` pins in PINS.yaml today. When one is added it lands in this same list with its reason,
  and if it is machine-runnable and unmodelled the run fails until someone writes the injection.

  **Two known gaps, exempted but still executed.** `expect="gap"` cases run like any other; they are expected
  to survive, and the run FAILS the day one of them is killed and the exemption stops being true. Each must
  name a task that exists in `queue/` and is not yet `done/`:
  - P-SRC-01 greps `Sources/` only, so `import UIKit` in a root-package TEST target is invisible - filed as
    **T-0099** (`queue/ready/`), which also carries the promotion instruction.
  - check-line-cap globs `Sources/` and `Tests/` only, so the 300-line cap does not reach the iOS package -
    **T-0037** already owns it.
  Fixing either means editing `pins/PINS.yaml`, which is outside this task's `touches:` and wants its own
  red/green and its own reviewer. Measuring them beats writing them down.

  **RED 1 - the brief's own example.** `wt/demo-T-0080` (branch `tmp/demo-T-0080`), one committed change:
  `(CoreLocation|MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)` -> `(MapKit|UIKit|SwiftUI|MapLibre|Ferrostar)`.

        ### ops/check-pins:
        PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        check-pins exit=0

        ### ops/check-pins --source-only:
        PINS ok=3 skipped=8 pending=1 expired=0 failed=0 tier=linux source-only
        source-only exit=0

        ### ops/pins-mutation --pin P-SRC-01:
          SURVIVED  P-SRC-01  import CoreLocation in Sources/ScenicKit/Model/Coordinate.swift
          GAP       P-SRC-01  import UIKit in Tests/ScenicKitTests/GeoTests.swift (test target)  (survives; T-0099 owns it)
        PINS-MUTATION mutable=9 covered=1 cases=7 killed=5 survived=1 gaps=1 errors=0 tier=linux FILTERED
         - SURVIVED P-SRC-01 import CoreLocation in Sources/ScenicKit/Model/Coordinate.swift  (violates: Root-package targets import Foundation only)
           The assertion stayed green while the statement it makes was false.
        pins-mutation exit=1

    The first attempt at this demo also committed a real `import CoreLocation` into `Coordinate.swift` to
    reproduce the brief byte for byte. That made check-pins exit 1 - not for P-SRC-01, but because P-SAFE-05
    builds the package with `swift test` and CoreLocation does not exist on this toolchain. Recorded because it
    is a fact about the tree, not about the pin: the dead pin was caught by accident, on a host that has swift,
    by an unrelated assertion. The demo above is the honest one - nothing but the weakened regex.

  **RED 2 - an assertion that cannot fail.** `assertion: "true || false"` on P-GIT-01, committed in the same
  demo worktree:

        ### ops/check-pins:
        PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        check-pins exit=0

        ### ops/pins-mutation --pin P-GIT-01:
          SURVIVED  P-GIT-01  the eol=lf line deleted from .gitattributes
          SURVIVED  P-GIT-01  eol=lf weakened to text=auto
        PINS-MUTATION mutable=9 covered=1 cases=2 killed=0 survived=2 gaps=0 errors=0 tier=linux FILTERED
         - SURVIVED P-GIT-01 the eol=lf line deleted from .gitattributes  (violates: .gitattributes normalizes every text file to LF)
         - SURVIVED P-GIT-01 eol=lf weakened to text=auto  (violates: .gitattributes normalizes every text file to LF)
        pins-mutation exit=1

  **RED 3 - the runner's own vacuity floor and coverage guard.** First `CASES = []`:

        ### ops/pins-mutation (no filter):
        MUTATION FAIL: 0 injections are defined - a run that mutates nothing is not a pass, it is a run that proved nothing
        exit=2

    That refusal used to read `no cases match --pin []`, which blames a filter that was never given; writing
    this demo is what found it (commit 60770e5). Then, with P-SRC-01's six must-kill cases deleted and
    everything else intact - the shape of a case list quietly losing a pin:

        PINS-MUTATION mutable=9 covered=8 cases=23 killed=21 survived=0 gaps=2 errors=0 tier=linux
         - P-SRC-01: runs here but has NO injection - write one in pins_mutation_cases.py
         - FLOOR: cases 23 < 29; raise this bar, never lower it to fit a lost case
         - FLOOR: kills 21 < 27; raise this bar, never lower it to fit a lost case
         - FLOOR: pins covered 8 < 9; raise this bar, never lower it to fit a lost case
        exit=1

  **RED 4 - an injection that changes nothing.** `IMPORT_HOST` pointed at a renamed file, which is how a case
  rots. Six no-ops must be errors, never quiet passes:

        PINS-MUTATION mutable=9 covered=1 cases=1 killed=0 survived=0 gaps=1 errors=6 tier=linux FILTERED
         - ERROR P-SRC-01 import CoreLocation in Sources/ScenicKit/Model/CoordinateRenamed.swift: injection did nothing - Sources/ScenicKit/Model/CoordinateRenamed.swift does not exist
         ... (six, one per banned framework)
        exit=1

    The same guard runs even when a primitive claims success: after every injection the demo tree's
    `git status --porcelain` must be non-empty, or the case is an ERROR.

  **GREEN - the gate, on this branch's HEAD, tree clean:**

        ### ops/check-pins:
        PINS ok=9 skipped=0 pending=3 expired=0 failed=0 tier=linux
        check-pins exit=0

        ### ops/pins-mutation (full, unfiltered, --verbose):
          baseline P-ATTR-02: green
          killed    P-ATTR-02  LICENSE-DATA deleted
          killed    P-ATTR-02  the OpenStreetMap credit reworded away
          killed    P-ATTR-02  every ODbL mention removed
          baseline P-DATA-02: green
          killed    P-DATA-02  the platform floor dropped to iOS 17
          killed    P-DATA-02  the floor restated as .v18 (no waypoint URLs)
          baseline P-GIT-01: green
          killed    P-GIT-01  the eol=lf line deleted from .gitattributes
          killed    P-GIT-01  eol=lf weakened to text=auto
          baseline P-OPS-01: green
          killed    P-OPS-01  ops/test committed 100644
          killed    P-OPS-01  a data file committed 100755
          killed    P-OPS-01  a required script dropped from the index
          baseline P-PROC-01: green
          killed    P-PROC-01  a done/ task graded by its own owner
          killed    P-PROC-01  a done/ task with no reviewer at all
          baseline P-SAFE-05: green
          killed    P-SAFE-05  the oracle's USNO provenance replaced by our own output
          killed    P-SAFE-05  the fixture set cut to 10 site-days
          killed    P-SAFE-05  the solar math shifted by a 2-degree zenith
          baseline P-SRC-01: green
          killed    P-SRC-01  import CoreLocation in Sources/ScenicKit/Model/Coordinate.swift
          killed    P-SRC-01  import MapKit in Sources/ScenicKit/Model/Coordinate.swift
          killed    P-SRC-01  import UIKit in Sources/ScenicKit/Model/Coordinate.swift
          killed    P-SRC-01  import SwiftUI in Sources/ScenicKit/Model/Coordinate.swift
          killed    P-SRC-01  import MapLibre in Sources/ScenicKit/Model/Coordinate.swift
          killed    P-SRC-01  import Ferrostar in Sources/ScenicKit/Model/Coordinate.swift
          GAP       P-SRC-01  import UIKit in Tests/ScenicKitTests/GeoTests.swift (test target)  (survives; T-0099 owns it)
          baseline P-SRC-02: green
          killed    P-SRC-02  a 320-line tracked Swift file under Sources/
          killed    P-SRC-02  a 320-line tracked Swift file under Tests/
          killed    P-SRC-02  the scanned Swift file set drops below MIN_FILES
          GAP       P-SRC-02  a 320-line tracked Swift file under apps/ios/Packages/  (survives; T-0037 owns it)
          baseline P-TEST-01: green
          killed    P-TEST-01  floor_linux.txt is not an integer
          killed    P-TEST-01  floor_linux.txt lowered below 3
          killed    P-TEST-01  floor_ios.txt deleted
        PINS-MUTATION mutable=9 covered=9 cases=29 killed=27 survived=0 gaps=2 errors=0 tier=linux
           not modelled: P-PROD-01: pending on T-0012, so there is no assertion to make red yet; assertion is TODO/empty
           not modelled: P-COST-02: pending on T-0014, so there is no assertion to make red yet; assertion is TODO/empty
           not modelled: P-HUMAN-01: pending on T-0013 ...; runs_on ['human'] excludes this tier - a human or a device answers it, not a worktree
        real 1m36.008s
        pins-mutation exit=0

        ### ops/test (after `cd services/api && npm ci` in this fresh worktree):
        TESTS linux=50/50 ios=skipped failed=0 skipped=0
        OK
        ops/test exit=0

  **Safety.** Every injection landed in `wt/demo-pins-mutation-<pid>` (created from HEAD, removed at the end),
  never in this checkout. Each case reverts by writing back the exact bytes it captured - no `git checkout --`,
  no `git stash`, no `git clean` - and the demo tree's `git status --porcelain` must be empty again before the
  next case runs; if it is not, the run aborts with exit 2 and KEEPS the worktree so nothing is destroyed. The
  caller's tree must be clean to start, because the demo worktree is built from HEAD and uncommitted work would
  not be what got tested (that refusal is itself visible above: it stopped a run mid-session). After the green
  run, `git worktree list` holds no `demo-pins-mutation-*` and `git status` is empty. `pins/floor_*.txt`,
  `Package.swift` and `pins/PINS.yaml` are mutated by three of these cases but only ever inside the throwaway
  worktree, so no `exclusive:` lock is owed - nothing on a shared branch is touched.

  **Cost.** ~1m40 unfiltered; ~7s for a `--pin` probe. `--pin` prints FILTERED and does not apply the floors,
  so a filtered run can never be mistaken for the gate.
- 2026-09-08 reviewer set to agent/reviewer-14 (not the owner); moved to queue/review/ with PR open.

- 2026-09-08 — **`ops/lib/pins_mutation.py` and `ops/lib/pins_mutation_cases.py` set to 100644, which turns
  this PR's CI RED on purpose.** They were committed 100755. That is green against `main`'s P-OPS-01 today
  and **wrong the moment [[T-0036]] merges**, because T-0036 reclassifies `ops/lib/*.py` as data:

        ops/lib/check-exec-bits (on task/T-0036):
          $4 ~ /\.(json|txt|md|py)$/ ... { if ($1 != "100644") print $4 " (data, should be 100644, ...)" }

  Its reason: every call site invokes these as `"$PY" ops/lib/x.py`, never `./ops/lib/x.py`, so the exec bit
  asserts a mode nothing uses.

  The three other branches that add an `ops/lib/*.py` all committed 100644 and are all red today for exactly
  this reason — `task/T-0021` (`classify-checks.py`), `task/T-0049` (`merge_reason_cap_assert.py`),
  `task/T-0081` (`etl_mutation.py`, `etl_mutation_rules.py`). This branch was the outlier, and being the
  outlier is what would have hurt: `ops/merge-rehearse`'s derived rule orders every such branch **after**
  T-0036, so at 100755 it merges into the tree where that mode is wrong, and the failure arrives on `main`
  rather than on a PR.

        $ bash ops/lib/check-exec-bits
          ops/lib/pins_mutation.py (script, should be 100755, is 100644)
        ops/lib/pins_mutation_cases.py (script, should be 100755, is 100644)

  That red is the correct state to be in before T-0036, and it is the same red the other three carry. Do not
  "fix" it with `--chmod=+x`: there is no mode that is right in both merge orders, which is why the ordering
  constraint exists at all. `ops/pins-mutation` stays 100755 — it is a wrapper under `ops/`, not `ops/lib/`,
  and it IS invoked directly.
