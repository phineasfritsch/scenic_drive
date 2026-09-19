---
id: T-0199
title: ops/mutate/handoff - the StraightLineDistance population (an earth-radius swap, a formula swap as an EQUIVALENT entry with its witness, floor -> nearest, a dropped chain point) with a literal floor; T-0170's STILL OPEN (a)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-09-19T17:45:21Z
lease_expires_at: 2026-09-19T22:45:21Z
worktree: .worktrees/T-0199
branch: task/T-0199
exclusive: []
touches: [ops/mutate/, Tests/HandoffTests/]
pins_affected: []
reviewer: null
depends_on: [T-0170]
verify: [ops/test, ops/check-pins]
acceptance:
  - "ops/mutate/handoff.py (or the existing handoff driver widened - rule it) carries a MUTATIONS table over Sources/Handoff/StraightLineDistance.swift: the radius changed by 0.1%, .rounded(.down) -> .rounded(), the destination dropped from the chain, a pin moved 1.5 km - each killed BY NAME by the test the entry names (swift test --scratch-path <own> --filter HandoffTests); MIN_MUTATIONS literal floor; --prove-floor red then green"
  - "the flat equirectangular formula on the same radius is an EQUIVALENT entry with the mutant pass's witness (haversine 112,268.093 m vs flat 112,268.146 m over the shipped chain; 707 m on a 1,065 km east-west leg) - or the test doc at StraightLineDistanceTests.swift:41-43 narrowed to 'a gross radius change' and a long synthetic leg added so a formula change IS caught; rule which"
  - "bash ops/check-pins --source-only, bash ops/lib/check-exec-bits, bash ops/queue-check bare at the final commit"
---
## Brief

From T-0170's Log (STILL OPEN (a), ruling R5) and the 00:13 panel's grounding: StraightLineDistance is a new
numeric module under Sources/ and CLAUDE.md's Verification section makes it ship its mutation population under
ops/mutate/ with a literal floor; ops/ was outside T-0170's touches, so three mutants were run by hand (all killed
by name) and the population was filed. The pre-review mutant pass found the flat-formula mutant equivalent at the
card's precision and the test doc overclaiming.

## Log
- 2026-09-19T06:29:45Z filed by agent/claude-fable-5-1 from T-0170's STILL OPEN (a) and the 00:13 panel (grounded). Not started; after #110 merges.
- 2026-09-19T12:44:08Z PROMOTED to ready/ by agent/claude-fable-5-1 (05:13 panel, grounded): T-0170 is in done/; the StraightLineDistance population (now with the LA chain from T-0178) - P-PROC-06 lists the module as DEBT.
- 2026-09-19T17:45:21Z claimed by agent/claude-opus-5; lease until 2026-09-19T22:45:21Z
- 2026-09-19T17:45:22Z at claim by agent/claude-fable-5-1 (orchestrator): #121 landed wholeMiles(through:) on StraightLineDistance.swift (floored from the same metres; the LA literal 29.48 cannot separate floor from round - the Skyline 69.76 and the synthetic 1.988-mile test carry it) - the population covers wholeMiles too. Swift 6.3.3 is NATIVE on this Windows box (C:/Users/phineasf/AppData/Local/Programs/Swift/Toolchains/6.3.3+Asserts/usr/bin/swift, on PATH in git-bash); ops/mutate/handoff.py already runs swift build/test with --scratch-path .build/mutate-handoff.
