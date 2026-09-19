---
id: T-0229
title: pins - P-SAFE-05's assertion runs `swift test --filter SolarFixtureTests` with NO --scratch-path: racy against any other swift build on the box (seen failing OPEN once on 2026-09-19); every pin that builds Swift takes its own scratch path
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
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
