---
id: T-0337
title: The app reads /trip's and /loop's 422 nothing_pretty as its own failure with calm copy, not as unexpectedResponse(422)
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T07:30:27Z
lease_expires_at: 2026-10-09T17:30:27Z
worktree: .worktrees/T-0337
branch: task/T-0337
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml, ops/mutate/tripsheet_mutations.py, ops/mutate/tripsheet_run.py, ops/mutate/tripsheet.py, ops/mutate/loopsheet_mutations.py, ops/mutate/loopsheet_run.py, ops/mutate/loopsheet.py, queue/backlog/T-0338-loop-nothing-pretty-offer.md]
pins_affected: [P-SAFE-04]
reviewer: null
depends_on: [T-0335]
verify: [ops/test, ops/check-pins]
acceptance:
  - "A1 TRIP READER through the shipping entry point TripClient.trip (TripWire.trip over a CountingPlanTransport), Swift Testing suite TripNothingPrettyTests: a 422 {error: nothing_pretty, days, extra_budget_pct} over the CROSS PRODUCT of day variants {1, 3, 5 accepted; 0, 6, (1.0).nextDown, (5.0).nextUp, 2.5, \"3\", true, null, missing, 1e999 refused} x percent variants {0, 25, 40 accepted; -1, 41, (0.0).nextDown, (40.0).nextUp, 12.5, \"40\", false, null, missing refused}; each row's expected is a function of its two variants - .failure(.nothingPretty(TripNothingPretty(days:, extraBudgetPercent:))) when both are accepted, else .failure(.unexpectedResponse(status: 422)) - compared WHOLE, from exactly 1 request; a meta-row holds the table at 13 x 12 rows. The same accepted body at 400, 404 and 429 is unexpectedResponse(status) and at 500 routingOffline."
  - "A2 LOOP READER through LoopClient.loop (LoopWire.loop), suite LoopNothingPrettyTests: 422 {error: nothing_pretty, minutes} over minute variants {10, 45, 180 accepted; 9, 181, (10.0).nextDown, (180.0).nextUp, 44.5, \"45\", true, null, missing, 1e999 refused}, expected = f(variant) as A1, whole, 1 request each, meta-row 13 rows; the accepted body at 400, 404, 429 is unexpectedResponse(status), at 500 routingOffline."
  - "A3 SHEET AND COPY: TripError.nothingPretty(_).failure == TripFailure.nothingPretty and LoopError.nothingPretty(_).failure == LoopFailure.nothingPretty in the existing failure-mapping tables; a 422 {nothing_pretty, days 5, extra_budget_pct 40} through ClientTripPlanner leaves TripSheet .failed(ticket, .nothingPretty) and {nothing_pretty, minutes 45} through ClientLoopPlanner leaves LoopSheet .failed(ticket, .nothingPretty); TripFailure.nothingPretty.line and LoopFailure.nothingPretty.line equal R6's two rows WHOLE; the existing every-failure-has-its-own-calm-line tests stay green over allCases (12 -> 13, 9 -> 10)."
  - "A4 RED FIRST: on the commit carrying the tests, the two value types and the enum cases but NOT the two reader arms, A1/A2's row tests and A3's sheet rows are quoted RED by name; then green on the arms."
  - "A5 MUTANTS: tripsheet and loopsheet populations gain TripNothingPretty.swift / LoopNothingPretty.swift as subjects and the new suites as test files, with entries: the reader arm dropped; each bound moved outward by one (days 0 and 6, percent -1 and 41, minutes 9 and 181); the whole-number check dropped; nothingPretty shown as unexpectedResponse; each run with --only and CAUGHT by its named killers, quoted; MIN_MUTATIONS raised to the new counts."
  - "A6 GATES: every changed or new Sources/ file re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt; check-line-cap, check-mutate-population, check-pins-yaml, queue-check and check-pins --source-only green on the head merged with origin/main; ios-compile and ios-screenshot success on the branch."
---
## Brief

T-0335 (R2, R3, R5) made the Worker refuse a dull road trip - 422 {error: nothing_pretty, days, extra_budget_pct} - and
answer a loop whose every clean attempt was dull with 422 {error: nothing_pretty, minutes}. On T-0335's head
Sources/ScenicAPIClient TripReplyReader and LoopReplyReader map both to their `default` arm,
`.unexpectedResponse(status: 422)`, so the driver sees a generic error where the Worker said "nothing pretty within
reach". MEASURE FIRST: the trip and loop error enums and every switch over them (Sources/ and apps/ios), the copy
rows they reach, and whether a loop's refusal should offer "try a longer loop" (minutes + 40 within
MAX_LOOP_MINUTES 180, as /plan's more_time offer) or a re-roll tomorrow (the seed is per user per UTC day). Then the
acceptance: each reader maps (422, nothing_pretty) to its own case over a table with every field at its bounds and
each field missing / mistyped refused, whole-copy equality for the new rows, the digests re-approved.

## Log
- 2026-10-09T05:23:51Z filed by agent/claude-opus-5 (T-0335 owner) from T-0335 R5.
- 2026-10-09T07:30:27Z claimed by agent/claude-opus-5; lease until 2026-10-09T17:30:27Z
- 2026-10-09T07:34:39Z MEASURED on eb585655 (owner agent/claude-opus-5), before any code:
  - The enums: TripError 12 cases -> TripFailure 12 (Sources/ScenicAPIClient/TripError.swift `failure`); LoopError 9
    -> LoopFailure 9 (LoopError.swift `failure`). Every switch over them: those two `failure` switches, and
    TripFailure.line / LoopFailure.line (Sources/ScenicKit/TripSheet, LoopSheet). apps/ios switches over NONE:
    FeaturePlanSheet/RoadTripScreen.swift:32-36 and LoopScreen.swift:32-36 show `Text(failure.line)` under
    accessibility ids `trip.failure` / `loop.failure` for every case; `grep noCleanLoop|tooFewDays|ceilingBreached
    apps/ios` is empty. So a new case needs no app edit, and its copy row is the only thing the driver sees.
  - The readers: TripReplyReader / LoopReplyReader have no (422, "nothing_pretty") arm; both reach `default ->
    .unexpectedResponse(status: 422)`, shown as "The planner answered in a way we did not expect. Try again."
  - The Worker bodies: services/api/src/trip.ts:60 `json({ error: "nothing_pretty", days, extra_budget_pct:
    extraBudgetPct }, 422)` - both are the request's own whitelisted values (tripRequest.ts:81 wholeIn(days, 1, 5);
    :85-89 extraBudgetPct = 40 unless the body carries a whole percent in [0, 40]). loop.ts:53 `json({ error:
    "nothing_pretty", minutes }, 422)` - the request's minutes (loopRequest.ts:61 finite in [10, 180], not required
    whole); the app's LoopRequestBody sends `minutes: Int` in 10...180, so every echo this client can receive is whole.
  - The re-roll: loop.ts:82 `loopSeed(who.userId, dayKey(now))`, loopPlanner.ts:81 "the same user on the same day gets
    the same loop", and the Worker already re-rolls S, S+1, S+2 within LOOP_UPSTREAM_COST = 3 (loopPlanner.ts:29)
    before it answers nothing_pretty. A retry today with the same start and minutes repeats those three seeds.
- 2026-10-09T07:34:39Z RULINGS (owner):
  - R1 Each reader maps (422, "nothing_pretty") to its own case carrying the body's fields, read FAIL-CLOSED as
    NothingPrettyOffer is (T-0332): new value types TripNothingPretty(days, extraBudgetPercent) and
    LoopNothingPretty(minutes), each Decodable, every key present, a JSON number that is finite, whole and inside the
    Worker's own bounds (days 1...5, percent 0...40, minutes 10...180); anything else is unexpectedResponse(status:
    422), never a guess. Loop minutes must be whole although loopRequest.ts accepts a fraction: a fractional echo
    answers no request this client made (it sends Int). The bounds are the types' own constants, not
    TripRequestBody/LoopRequestBody's ranges, so a mutant of the request bound is not also a mutant of the reader.
    Read through PlanFailureBody beside `nothingPretty`, each with `try?`, so a malformed one never costs the body.
  - R2 NO LONGER-LOOP OFFER, NO RE-ROLL BUTTON. The loop body carries only `minutes`; an offer of minutes + 40 would
    be a server field invented on the client (the /plan offer's more_time_minutes is the Worker's, honestFailure.ts),
    and a re-roll today repeats the Worker's three seeds (measured above). The copy says "today" and names the two
    choices the driver already holds on the form (another start, another length) - no action, no number. If the
    owner wants a "try a longer loop" button, the Worker must carry it: filed as T-0338 (backlog; loop.ts answers
    more_time_minutes = minutes + 40 when <= MAX_LOOP_MINUTES, and the app acts on it as T-0334 did for /plan).
    The trip gets no offer either: the destination is the driver's (T-0335 R2) and 40 percent is the Worker's cap.
  - R3 TripFailure.nothingPretty / LoopFailure.nothingPretty, payload-free like every other case; TripError /
    LoopError carry the read value for fidelity (as quotaExhausted carries resetsAt).
  - R4 pins_affected names P-SAFE-04; nothing here touches the ceiling (a refusal carries no route) and no test bound
    by name in named-tests.json is renamed - ruled NOT affected. The digest rows of every changed or new Sources/
    file are re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt (memory sources-digest-pin).
  - R5 touches widened to the tripsheet / loopsheet mutation populations (CLAUDE.md: a new numeric module ships its
    population; the two value types join the existing populations) and the follow-up's backlog file.
  - R6 THE COPY (whole, the two new rows; owner-route-intent: calm, unhurried, never alarm, no "!"):
    TripFailure.nothingPretty: "Nothing on the way there was pretty enough to show. Try another place to head for."
    LoopFailure.nothingPretty: "No loop from here was pretty enough to show today. Try another start or another length."
- 2026-10-09T08:11:44Z A4 RED FIRST on c74c4e21 (value types, cases, copy and tests; no reader arms), `swift test
  --filter TripNothingPrettyTests|LoopNothingPrettyTests|TripSheetGateTests|LoopSheetGateTests|...` exit=1:
  `Test "a dull trip's 422 nothing_pretty is read whole at every bound, refused otherwise" with 156 test cases failed
  ... with 9 issues.` (exactly the 9 accepted rows: the refused rows already answered unexpectedResponse(422));
  `Test "a dull loop's 422 nothing_pretty is read whole at every bound, refused otherwise" with 13 test cases failed
  ... with 3 issues.`; `Test "a dull trip reaches the sheet as nothingPretty from one request" failed ... with 1 issue.`;
  `Test "a dull loop reaches the sheet as nothingPretty from one request" failed ... with 1 issue.`; `Test run with 38
  tests in 8 suites failed ... with 14 issues.` GREEN on 8a40d41e (the two arms): `Test run with 41 tests in 9 suites
  passed` (+ NothingPrettyReaderTests 4 XCTests, 0 failures), exit=0.
- 2026-10-09T08:11:44Z A5 MUTANTS on 8a40d41e: `python ops/mutate/tripsheet.py --only 44,...,53` -> `caught by the test
  that names it: 10 of 10 (wrong killer 0, trapped 0, compile-only 0, MISSED 0, skipped 0)`, `MUTATE OK caught=10/10
  (--only: 10 of 53 entries)`; `python ops/mutate/loopsheet.py --only 60,...,65` -> `6 of 6 (wrong killer 0, ...
  MISSED 0)`, `MUTATE OK caught=6/6 (--only: 6 of 65 entries)`. Each entry's killers as named in the populations
  (rows table for 44-51 / 60-63, sheet row for 44/60, mapping + copy + sheet for 52/64, copy for 53/65).
- 2026-10-09T08:11:44Z A6 iOS CI on 8a40d41e: ios-compile 37901075343 success (3m15s); ios-screenshot 37901079042
  success (11m46s). Bare gates on 8a40d41e: `P-SRC-02: 525 Swift files tracked ... none over 300 lines`; `PINS-YAML ok
  pins=49 fields=395`; `QUEUE OK (329 tasks)`.
