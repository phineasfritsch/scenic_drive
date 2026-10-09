---
id: T-0338
title: A dull loop's 422 nothing_pretty carries the Worker's own "try a longer loop" offer, and the app acts on it
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T21:38:36Z
lease_expires_at: 2026-10-10T03:38:36Z
worktree: .worktrees/T-0338
branch: task/T-0338
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/check-safety-disclaimer-linked-digests.txt]
pins_affected: []
reviewer: null
depends_on: [T-0337]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 MEASUREMENT, NO OFFER (R1-R3): loopHonest's dull rows driven through handleLoop (the handler ROUTES[\"/loop\"] calls) at minutes 45 and minutes 85 (45 + 40) answer the SAME verdict row for row - [2, 2, 2], [unscored x3], [5, 5, 5] and [retraced, 2, retraced] each answer 422 {error: nothing_pretty, minutes} after 3 requests at both, the [6] control answers 200 attempts 1 at both; the only request field minutes moves is round_trip.distance (30000 -> 56667). Quoted in the Log 2026-10-09T21:45:53Z. A longer loop from the same start and seed is not shown likelier to clear 0.45, so /loop gains no more_time_minutes and the app no 'Try a longer loop'."
  - "A2 NO CODE: git diff --name-only origin/main...HEAD lists exactly queue/claimed/T-0338-loop-nothing-pretty-offer.md - no services/, Sources/, Tests/, apps/ios/ or ops/ file, so no digest row, pin, mutant population or iOS CI run is owed."
  - "A3 GATES on the merged head: ops/queue-check, python ops/lib/check-pins-yaml.py, ops/lib/check-line-cap and python ops/lib/check-mutate-population.py exit 0; loopHonest.test.ts passes unedited."
---
## Brief

T-0337 R2 ruled that the app offers no "try a longer loop" on /loop's 422 {error: nothing_pretty, minutes}: the body
carries only the request's minutes, and an offer of minutes + 40 computed on the device would be a server field
invented on the client. /plan's offer is the Worker's (honestFailure.ts more_time_minutes = budget + 40, nil past 180;
the app acts on it since T-0334). If the owner wants the same for loops, the Worker answers it: loop.ts's
nothing_pretty gains `more_time_minutes` (minutes + 40 when <= MAX_LOOP_MINUTES 180, else null), the client's
LoopNothingPretty reads it fail-closed (present, null or exactly minutes + 40 within 180), and the loop screen offers
"Try a longer loop" that re-plans with those minutes through LoopSheet's gate.

MEASURE FIRST: whether a longer loop from the same start and the same (user, UTC day) seed is any likelier to clear
RouteScore's 0.45 - run the loopHonest harness's dull rows at minutes and minutes + 40 and quote both. If it is not,
the offer is a promise the planner cannot keep, and this task closes with that measurement instead.

## Log
- 2026-10-09T07:34:39Z filed by agent/claude-opus-5 (T-0337 owner) from T-0337 R2.
- 2026-10-09T21:38:36Z claimed by agent/claude-opus-5; lease until 2026-10-10T03:38:36Z
- 2026-10-09T21:45:53Z MEASURE FIRST, before any ruling or code. A throwaway vitest file (services/api/test/t0338Measure.test.ts,
  never staged, moved to the ignored .artifacts/t0338/ after the run) drove loopHonest's dull rows through handleLoop with
  loopHarness/loopPath/squareLoop/outAndBack unedited, once at minutes 45 and once at minutes 85, and scored every
  answer the router sent with routeScoreOf. `npx vitest run test/t0338Measure.test.ts --reporter=verbose` (1 passed):
      [2, 2, 2] minutes 45: 422 {"error":"nothing_pretty","minutes":45} requests 3 distances [30000,30000,30000] scores ["0.020000","0.020000","0.020000"]
      [2, 2, 2] minutes 85: 422 {"error":"nothing_pretty","minutes":85} requests 3 distances [56667,56667,56667] scores ["0.020000","0.020000","0.020000"]
      [unscored x3] minutes 45: 422 {"error":"nothing_pretty","minutes":45} requests 3 distances [30000,30000,30000] scores ["null","null","null"]
      [unscored x3] minutes 85: 422 {"error":"nothing_pretty","minutes":85} requests 3 distances [56667,56667,56667] scores ["null","null","null"]
      [5, 5, 5] minutes 45: 422 {"error":"nothing_pretty","minutes":45} requests 3 distances [30000,30000,30000] scores ["0.425000","0.425000","0.425000"]
      [5, 5, 5] minutes 85: 422 {"error":"nothing_pretty","minutes":85} requests 3 distances [56667,56667,56667] scores ["0.425000","0.425000","0.425000"]
      [retraced, 2, retraced] minutes 45: 422 {"error":"nothing_pretty","minutes":45} requests 3 distances [30000,30000,30000] scores ["0.713333","0.020000","0.713333"]
      [retraced, 2, retraced] minutes 85: 422 {"error":"nothing_pretty","minutes":85} requests 3 distances [56667,56667,56667] scores ["0.713333","0.020000","0.713333"]
      [6] (control, pretty) minutes 45: 200 {"attempts":1,"minutes":45} requests 1 distances [30000] scores ["0.510000"]
      [6] (control, pretty) minutes 85: 200 {"attempts":1,"minutes":85} requests 1 distances [56667] scores ["0.510000"]
  Every dull row is the same 422 at both lengths; the pretty control is the same 200 at both. Not likelier.
- 2026-10-09T21:45:53Z RULINGS (author rule, before any code):
  - R1 Brief vs reality - the harness is minutes-blind. loopHarness answers the n-th request with answers[n] whatever
    it asked for, so its rows cannot come out likelier at any length; the measurement above is the Brief's measurement
    and it says "not likelier", but on its own it would say that about any offer. What it does show is the request
    side: minutes moves exactly one field the router sees, round_trip.distance = roundTripDistance(minutes) (30000 ->
    56667). The seed (loopSeed(user, UTC day)), the seed ladder (S, S+1, S+2), the custom model
    (buildCustomModel(LOOP_LAMBDA 2, the same feed)) and the start are identical at 45 and 85. Ruled: the decision
    turns on whether the PLANNER has any mechanism that makes a longer loop prettier, read from src, not from the fake.
  - R2 the planner has none. planLoop holds lambda at LOOP_LAMBDA and asks for a longer round trip on the same seed;
    nothing in it steers toward scenery as minutes grow. RouteScore (routeScore.ts) is metre-weighted: mean, p90 and
    dud fraction are intensive (a longer loop over the same mix of roads scores the same - the [5, 5, 5] row's 0.425
    is length-free), and only the episode term grows with length, capped at EPISODE_WEIGHT 0.10 once 3 episodes of
    >= 800 m above 0.6 exist. Whether 40 more minutes reaches different scenery is a property of the graph around
    the start that the Worker does not know when it refuses. Contrast /plan's offer (honestFailure.ts
    MORE_TIME_MINUTES): there the budget is the ceiling the lambda sweep is held to, so +40 admits more scenic
    candidates - a mechanism the planner can keep. /loop has no ceiling to relax.
  - R3 so the Brief's own branch applies: "If it is not, the offer is a promise the planner cannot keep, and this
    task closes with that measurement instead." /loop's nothing_pretty keeps its body {error, minutes}; the client's
    LoopNothingPretty and the loop screen are unchanged (T-0337 R2 stands). An offer that re-plans costs the user a
    second LOOP allowance on the same seed for no shown gain. No code; acceptance A1-A3 above.
  - R4 what would reopen it: a measurement over a real graph, not the fake - GraphHopper round_trip from a set of LA
    starts whose 45-minute loop at the day seed scores < 0.45, re-asked at 85, counting how many clear 0.45. That is a
    container run over the LA graph (services/routing/work/graph-cache holds only the Vermont slice) and, per
    CLAUDE.md, a measurement task, not an acceptance; left to the owner to file if the offer is still wanted.
- 2026-10-09T22:10:31Z FINAL ACCEPTANCE on head 0f7af7f9 (git fetch origin + merge origin/main: "Already up to date"), PR #235:
  - A1 the measurement quoted at 21:45:53Z above; no offer field, no app button.
  - A2 `git diff --name-only origin/main...HEAD` -> `queue/claimed/T-0338-loop-nothing-pretty-offer.md` (only line).
  - A3 `ops/queue-check` -> "QUEUE OK (340 tasks)" exit 0; `python ops/lib/check-pins-yaml.py` -> "PINS-YAML ok pins=50
    fields=403" exit 0; `ops/lib/check-line-cap` -> "P-SRC-02: 553 Swift files tracked (Sources=269, Tests=197,
    apps/ios=87), none over 300 lines" exit 0; `python ops/lib/check-mutate-population.py` -> "P-PROC-06: 320 modules, 181
    covered by 38 populations, 118 allowlisted, 0 added by this branch ... the floor of 147 holds" exit 0;
    `npx vitest run test/loopHonest.test.ts` -> "Test Files 1 passed (1) Tests 14 passed (14)". PR #235 checks: core
    pass, pins-source-only pass.
- 2026-10-09T23:01:32Z agent/claude-opus-5 (owner): rv1-t0338 FAIL was ancestry-only (main gained PR #232 T-0343 and PR #236 T-0351). Merged origin/main (bec82d9d) last as 170245db. A2 re-quoted: `git diff --name-only origin/main...HEAD` lists only queue/claimed/T-0338-loop-nothing-pretty-offer.md. A3 re-run on the merged head: queue-check "QUEUE OK (342 tasks)" exit 0; check-pins-yaml "PINS-YAML ok pins=50 fields=403" exit 0; check-mutate-population "every added module is covered or allowlisted; the floor of 147 holds" exit 0; loopHonest.test.ts "Tests 14 passed (14)".
