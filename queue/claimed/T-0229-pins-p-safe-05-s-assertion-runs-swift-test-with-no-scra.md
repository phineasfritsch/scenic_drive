---
id: T-0229
title: pins - P-SAFE-05's assertion runs `swift test --filter SolarFixtureTests` with NO --scratch-path: racy against any other swift build on the box (seen failing OPEN once on 2026-09-19); every pin that builds Swift takes its own scratch path
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T15:39:28Z
lease_expires_at: 2026-10-17T15:39:28Z
worktree: .worktrees/T-0229
branch: task/T-0229
exclusive: []
touches: [pins/PINS.yaml, ops/lib/]
pins_affected: [P-SAFE-05]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "P-SAFE-05's assertion (pins/PINS.yaml:150) and every other pin assertion that invokes swift build/test carry `--scratch-path .build/pins-<id>` (grep 'swift (build|test)' over PINS.yaml enumerates the population; quote it); a structural check under ops/lib refuses a pin assertion that runs swift without --scratch-path, RED first on the current PINS.yaml (P-SAFE-05 named), then green; CLAUDE.md's 'every swift build/test on a shared box uses its own --scratch-path' is what it enforces"
  - "the race demonstrated once on the record: two `swift test` invocations against the root package in parallel with and without the scratch path, the failing-open output quoted (T-0182's Log has the first sighting); bash ops/check-pins --source-only, check-exec-bits, queue-check bare"
---
## Brief

T-0182's author ran `bash ops/check-pins --source-only` and `swift test --scratch-path .build/T0182` as two parallel
calls and P-SAFE-05 failed OPEN once - the pin's own `swift test` shares the default .build with whoever else is
building. A P-SAFE-* pin failing open is the class CLAUDE.md says buys a round every time; here the cause is the
pin's assertion, not the branch. Harness, two rounds.

## Log
- 2026-09-19T21:20:32Z filed by agent/claude-fable-5-1 (orchestrator, from T-0182's Log: P-SAFE-05 seen failing OPEN under a parallel swift test). Not started; cheap; after the LA chain.
- 2026-10-16T15:39:28Z claimed by agent/claude-opus-5; lease until 2026-10-17T15:39:28Z
- 2026-10-16T15:45:59Z MEASUREMENT, before any code, by agent/claude-opus-5 (worktree .worktrees/T-0229, base 55c4b140).
  * Population, direct: `yaml.safe_load(pins/PINS.yaml)` is a list of 51 pins; every pin has `assertion`. Assertions
    whose text holds a bare-word `swift` command: ONE - P-SAFE-05
    (`... && swift test --filter SolarFixtureTests 2>&1 | grep -E 'Test run with ...' >/dev/null`). The only other
    assertion containing the letters `swift` is P-DATA-02, and there only as the file name `Package.swift`.
  * Population, transitive (scripts an assertion names, grepped for a swift build/test call): ops/lib/run-named-tests.py
    is the ONE builder. Its `swift_results` runs `swift test --scratch-path $SCENIC_SWIFT_SCRATCH (default .build)`,
    i.e. the shared default unless an operator overrides it. 11 pins reach it through a `swift` entry in
    ops/lib/named-tests.json: P-SAFE-04 P-PRIV-04 P-PRIV-05 P-PROD-02 P-PROD-05 P-STORE-02 P-SAFE-08 P-NAV-01 P-SAFE-09
    P-SAFE-07 P-PROD-01 (two of them, P-NAV-01 and P-SAFE-09, anchor source, so they run in the --source-only gate).
    The other regex hits are not builders: check-failure-naming, check-pipe-consumers, check-secret-scan.py,
    check-schema-version.py and check-named-table.py mention swift in prose or mutate a JSON table; check-mutate-only.py
    (P-PROC-06) launches ops/mutate drivers, and every `swift build`/`swift test` in ops/mutate/*.py passes
    `--scratch-path SCRATCH` (grep quoted 13 drivers, 26 calls, none without). ops/check-pins itself is
    `exec python ops/lib/pins.py`, which runs assertions under `bash -o pipefail -c` and builds nothing.
    ops/test:23 runs `swift test --parallel` on the default .build - outside this task's touches (ops/lib/, PINS.yaml)
    and the one-command test runner, not a pin; recorded, not changed.
  RULINGS
  * R1 (Brief vs T-0182's Log): the Brief calls the sighting "failing OPEN"; T-0182:317-326 shows the pin went RED (the
    gate failed, then passed serially) - a false red, i.e. it failed closed. The fail-open direction is still real by
    construction: a pin whose `swift test` shares .build with another build can run a test binary someone else built
    (a hand-made mutant, a different checkout state). Fixed either way; the race demo below records what happens.
  * R2 (Brief vs T-0182's Log): T-0182's other build used `--scratch-path .build/T0182`, NOT the default .build, so
    "shares the default .build" is not what the Brief's own evidence shows; T-0182 says "SwiftPM cannot have two builds
    in one package at once". Whether a separate scratch path cures that is measured below (two parallel runs sharing
    .build, then two on their own scratch paths), not assumed.
  * R3 (acceptance `.build/pins-<id>` vs run-named-tests): P-SAFE-05 takes `--scratch-path .build/pins-p-safe-05`
    (its own id, lowercased). run-named-tests.py serves 11 pins one after another inside one check-pins run; one cold
    root-package build per pin would add 10 cold builds to CI's core job for no isolation gain (pins run serially),
    so its default becomes ONE runner-owned path `.build/pins-named-tests`, never the shared .build.
    SCENIC_SWIFT_SCRATCH stays (queue/done logs of T-0261..T-0377 use it) but a value that resolves to the shared
    .build is REFUSED by name before swift starts.
  * R4 (where the guard runs): new pin P-OPS-10 (free on main and on T-0230/T-0241/T-0376's PINS.yaml, measured),
    anchor source, runs_on [linux, mac], assertion `python ops/lib/check-swift-scratch.py`. Whitelist shape: every
    word starting `swift` (case-insensitive, not preceded by a letter, digit, `_`, `.`, `/` or `-`, so `Package.swift`
    and `Tests/X.swift` are file names, but `swift-build`, `swiftc`, `SWIFT` are not excused) in any assertion read
    by ops/lib/pins.py's own `load` must sit at a command position and read exactly
    `swift (test|build) --scratch-path .build/pins-<own id lowercased>`. Everything else is refused, by pin id.
    The runner half binds to the shipping symbol: the guard imports run-named-tests.py, replaces only its subprocess
    and `which`, calls `swift_results` and holds the argv it would run.
  * R5 (ops/mutate drivers): already all on their own SCRATCH (measured above); not a pin assertion; no change.
  ACCEPTANCE (this task's, written before code)
  A1 `grep -nE '(^|[^A-Za-z0-9_./-])[Ss][Ww][Ii][Ff][Tt]' ` over the assertions (via the guard's --list) enumerates
     the population: P-SAFE-05 only, carrying `--scratch-path .build/pins-p-safe-05`.
  A2 `python ops/lib/check-swift-scratch.py` on the base tree is RED naming P-SAFE-05 and run-named-tests' `.build`;
     on the branch GREEN.
  A3 `python ops/lib/check-swift-scratch.py --prove-red` - every row RED by name: missing flag; flag in an echo; flag
     in a comment; flag on a different command in the same assertion; a second swift call missing it; another pin's
     scratch; `.build` spelled out; `swift run`; echo of a flagged command; `swift-build`; `SWIFT test`; quoted
     `bash -c "swift ..."`; runner mutants (flag pair dropped, default reverted to .build, env override `.build`
     accepted); control rows (flagged single call, two flagged calls, `Package.swift` file name) GREEN.
  A4 `SCENIC_SWIFT_SCRATCH=.build python ops/lib/run-named-tests.py P-NAV-01` refuses by name before swift runs;
     `python ops/lib/run-named-tests.py P-NAV-01` and the P-SAFE-05 assertion pass on their own scratch paths.
  A5 the race demo (two parallel `swift test --filter SolarFixtureTests`, shared .build, then own scratch paths) quoted.
  A6 bare: bash ops/check-pins --source-only; check-pins-yaml.py; check-exec-bits; check-line-cap; check-mutate-population.py;
     check-mutate-only.py; check-safety-disclaimer; queue-check.
- 2026-10-16T15:58:52Z RED FIRST, then green, by agent/claude-opus-5 (commit 55ad7045).
  * R6 (amends R4, found by the first RED run): the case-insensitive `swift` prefix also caught `SwiftUI` inside
    P-SRC-01's grep alternation (`...|SwiftUI|MapLibre|...` - the `|` reads as a pipe). The word is now `swift` NOT
    followed by a letter, digit or `_`: `SwiftUI` is a name, `swift-build`/`swift-test` (SwiftPM's executables) and
    `SWIFT` are still words. P-SRC-01's shape is a control row (GREEN); `swift-test after a pipe` is a RED row.
  * A2 RED on the base tree (`git stash push ops/lib/run-named-tests.py`; PINS.yaml still as on main):
      RED P-SAFE-05: `swift test --filter SolarFixtureTests 2>&1 | grep -E 'Test run with [1` - not `swift test|build --scratch-path .build/pins-p-safe-05`
      RED run-named-tests.py: scratch path `.build` is the shared .build or outside it
      RED run-named-tests.py: SCENIC_SWIFT_SCRATCH=.build was not refused before swift ran (1 call(s))
      RED run-named-tests.py: SCENIC_SWIFT_SCRATCH=./.build/ was not refused before swift ran (1 call(s))
      SWIFT-SCRATCH pins=51 swift_words=1 refused=4   exit=1
    GREEN on the branch: `PINS-YAML ok pins=52 fields=418`; `SWIFT-SCRATCH pins=52 swift_words=1 refused=0` exit=0.
  * A1 `--list` on the branch: one line, `P-SAFE-05: swift test --scratch-path .build/pins-p-safe-05 --filter ...`.
  * A3 `--prove-red`: `SWIFT-SCRATCH prove-red rows=30 wrong=0` exit=0 - 20 assertion rows RED (each by its own
    reason line), 5 assertion controls GREEN, 4 runner mutants RED (flag pair dropped -> `not swift test
    --scratch-path <dir>`; default back to .build -> `made 0 swift calls`; env .build accepted -> `SCENIC_SWIFT_SCRATCH=.build
    was not refused`; scratch outside .build -> `is the shared .build or outside it`), shipped runner GREEN.
  * A4 `SCENIC_SWIFT_SCRATCH=.build python ops/lib/run-named-tests.py P-NAV-01` ->
    `NAMED P-NAV-01 REFUSED: SCENIC_SWIFT_SCRATCH=.build is the shared default .build - ...` exit=1; `./.build/` on
    P-SAFE-09 refused the same way, exit=1.
  * A5 the race, .build/t0229/race.sh (two `swift test --filter SolarFixtureTests` started together, this worktree):
      shared default .build: run1 exit=1 verdict=FAIL
        error: invalid access to ...\.build\x86_64-unknown-windows-msvc\debug\Telemetry.build\include\module.modulemap
      shared default .build: run2 exit=0 verdict=PASS (√ Test run with 6 tests in 1 suite passed)
      own scratch paths (.build/pins-race-a, .build/pins-race-b): run1 exit=0 PASS, run2 exit=0 PASS (6 tests each)
    So R2 is settled on this box: two builds on one scratch path collide; on two scratch paths of one package they do not.
    The failure is RED (fails closed), as R1 ruled; the open direction stays the by-construction argument of R1.
