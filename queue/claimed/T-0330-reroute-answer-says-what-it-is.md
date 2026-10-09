---
id: T-0330
title: A reroute answer says whether it continued the drive - /plan marks an answer built from a recalled plan_token apart from the fresh plan it falls back to, and the app rules on a fresh one; the drive screen's ETA line follows the line it draws
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-09T06:51:11Z
lease_expires_at: 2026-10-09T16:51:11Z
worktree: .worktrees/T-0330
branch: task/T-0330
exclusive: []
touches: [services/api/src/, services/api/test/, Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-NAV-01]
reviewer: null
depends_on: [T-0328]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: how often a reroute token is unusable in practice (12 h TTL, device / place mismatch, PLANS unbound), what field marks a continued answer (a boolean on the 200 or the echoed first_pin) without a second coordinate or more than 2 dp, and whether the app takes a fresh answer or rejoins"
  - "The Worker's marker and the app's ruling on it are full-equality tested on both sides (recalled / expired / mismatched device / mismatched place / first_pin past the pins); the drive screen's ETA line is the taken answer's, Linux-tested through DriveDisplay or its successor"
  - "R2/R3/R4 below are the rulings the tests bind: `continued` is one of exactly 14 keys on every /plan 200 (planRecorded's ruled list), a fresh answer mid-drive is TAKEN with DriveDisplay.freshNote on the full surface only, and the session's ETA is the preview's (seeded through ScenicKit's DriveSession(preview:online:), which NavAdapter calls) until a taken answer's replaces it"
  - "Every new test is seen RED by name before its code lands, then bound by name in named-tests.json P-NAV-01; ops/mutate/drive.py and services/api/test/mutate/planMutants.mjs gain entries for the marker, the ruling and the ETA hand-off, each CAUGHT, with the floors raised"
  - "Digests re-approved in ops/lib/check-safety-disclaimer-linked-digests.txt; check-drive-display.py's whitelist carries the screen's new lines; ios-compile and ios-screenshot succeed on the branch and the drive shots are looked at and described in the Log"
---
## Brief

T-0328 R5 (PR for T-0328): with a token present the device cannot tell a reroute answer from the fresh plan /plan
falls back to when it no longer remembers the token (plan.ts recalls, reroutePlanner.ts recomputes decision points,
both answers have one shape), so the app takes either. T-0328 R6: the drive screen's ETA line stays the preview's
after a reroute is taken.

## Log
- 2026-10-08T18:25:31Z filed by agent/claude-opus-5 from T-0328 R5 and R6.
- 2026-10-09T06:51:11Z claimed by agent/claude-opus-5; lease until 2026-10-09T16:51:11Z
- 2026-10-09T06:54:54Z MEASURE then RULE (owner, before any code; tree at 564e6626).
  R1 MEASURED. services/api/src/plan.ts has ONE 200 site and two bodies reach it, both ScenicPlanResult +
  closures_hazard + plan_token with the same 13 keys (planRecorded.test.ts "the response carries exactly the ruled
  fields"): planReroute's (reroutePlanner.ts) exactly when the token recalls AND recalled.device == the caller AND
  recalled.place == the request's place AND first_pin <= the stored pin count AND the continuation fits fastest-from-
  here + budget; planScenic's fresh plan on everything else - no reroute; deps.plans null (PLANS unbound); recall
  null (unknown, expired past PLAN_TOKEN_TTL_SECONDS = 43200, KV read throws, unparseable or out-of-range record);
  another device (structurally its own key, planKeyPrefix(caller)); another place; first_pin past the pins; and
  planReroute null over the ceiling. HOW OFTEN IN PRACTICE: services/api/wrangler.jsonc binds no PLANS (its bindings
  are QUOTA, TELEMETRY and DB; no kv_namespaces), so in production today every 200 carries plan_token null, the app
  sends NO reroute (T-0328 R5) and the fresh fallback is reached zero times. Once bound: 12 h outlasts any one drive
  (fastest hours + a 180-minute budget), so expiry needs a drive left open past 12 h; another device and another
  place cannot come from the app (PlanRerouter sends the continuation's place; the key is the caller's device);
  first_pin past the pins cannot (DriveSession sends passed <= waypoints.count, the pins the Worker stored). What is
  left is KV's eventual consistency (a reroute read at another edge shortly after the put may miss - Cloudflare
  documents up to 60 s) and the over-ceiling null (the rest of the pins no longer fits from where the driver is).
  Neither can be counted with nothing bound, so the ruling must be right at any frequency. THE APP:
  PlanRerouter.reply(of:) maps route, waypoints and plan_token only; DriveController/DriveSession take either body
  alike. THE ETA LINE: DriveScreen renders `Text(preview.etaLine)` - the PlanPreview the drive started from, for the
  whole drive; DriveDisplay has no ETA, and a taken answer's eta_s / fastest_eta_s are dropped at reply(of:).
  R2 THE MARKER: every /plan 200 gains `continued` (a JSON boolean): true exactly when the body is planReroute's,
  false on every fresh plan, a plain plan included. It carries no coordinate and no precision, and the request is
  unchanged (still one 2-dp origin, P-PRIV-05). Rejected: echoing first_pin - a number the device already holds,
  meaningless on a fresh plan whose pins restart, and a present-or-absent shape the key whitelist would have to
  allow two ways. The ruled key list becomes 14.
  R3 A FRESH ANSWER MID-DRIVE IS TAKEN, WITH A NOTE. The fresh answer is a scenic plan from where the driver is to
  the same place under the same budget ceiling re-measured from here, its pins on its line: something to follow
  now. Refusing it is rejoin mode while ONLINE, with no retry (DriveSession asks again only on the offline-to-online
  edge) and a full-surface status that says "offline" (false), guiding back toward a line the Worker forgot or
  could not finish inside the budget. Calm is a line to follow; honest is saying it is new. DriveDisplay gains
  `note`: DriveDisplay.freshNote = "A new route from here - not the rest of your plan." on the FULL surface while the
  current line is a fresh answer, nil on the minimal surface (P-SAFE-09: moving adds nothing) and nil once a
  continued answer is taken. DriveVoice is unchanged ("Here is a new way." is true of both). A decoded 200 without
  `continued` reads false (the note shows: fail toward saying more); a non-boolean refuses the decode (the reroute
  fails: rejoin). T-0328 R5 is unchanged: no token, no request.
  R4 THE ETA LINE IS THE CURRENT LINE'S. DriveSession carries etaSeconds / fastestEtaSeconds: the preview's at the
  start through a new ScenicKit DriveSession(preview:online:) that NavAdapter calls (token, line, pins, lambda and
  ETA seeded on Linux; T-0328's device-only seeding E5 becomes testable), then each taken answer's eta_s /
  fastest_eta_s. DriveDisplay gains `etaLine`, built by PlanPreview.etaLine(etaSeconds:fastestEtaSeconds:) - the one
  formatter, which PlanPreview.etaLine also calls - and DriveScreen renders display.etaLine. After a reroute it is the
  answer's minutes from the reroute point; nothing counts it down live (Ferrostar step durations are 0, unchanged).
  The estimate badge rule is unchanged: preview.showsEstimateBadge, which the server's always-true eta_is_estimate
  keeps on (CLAUDE.md's 5-sample rule; the device has no learned samples yet).
  R5 TAKEN TOGETHER OR NONE: line, pins, token, ETA and continued are taken by DriveSession.rerouteArrived together;
  a refused or late answer changes none of them (DriveController's ticket, unchanged).
  R6 TESTS: services/api/test/planContinued.test.ts through handlePlan - recalled rows (first_pin 0, 1, 3) EQUAL an
  independent planReroute recomputation plus continued true; unusable rows (unknown or expired, unbound, read throws,
  another device, another place, first_pin 4, over the ceiling) EQUAL the plain fresh plan with continued false; a
  meta-test that every row's answer differs from its opposite. Swift: PlanResponse decode table (true / false /
  absent / non-boolean); ScenicKit DriveContinuedTests through DriveController and DriveDisplay(session:) over
  continued x surface vs literals, and the preview seeding; ScenicAPIClient DriveContinuedReplanTests through
  PlanRerouter and a recording transport. All bound by name in P-NAV-01.
- 2026-10-09T07:47:57Z BUILT (owner). RED FIRST BY NAME: services/api at b6fdc928 + the tests only, `npx vitest run
  test/planContinued.test.ts test/planRecorded.test.ts`: 4 failed | 2 passed - FAILED by name "a recalled token's
  answer is planReroute's body, whole, with continued true", "every unusable token's answer is the fresh plan's body,
  whole, with continued false", "meta: no fresh row ignores its variant - each opposite continues, and the marker is
  the only difference in kind", "the response carries exactly the ruled fields (R8)"; with plan.ts's marker 17/17 green
  (planReroute.test.ts included, unchanged: its fresh-equals-fresh rows hold with continued false on both sides).
  Swift with the API present but unwired (DriveSession(preview:) seeding 0, DriveController/PlanRerouter/
  DriveDisplay(session:) not passing ETA or marker): 20 tests, 6 FAILED by name - continuedBySurface, previewSeedsTheDrive,
  etaBounds, refusedAnswerTakesNothing (DriveContinuedTests), continuedThroughTheRerouter, replyCarriesTheMarkerAndEta
  (DriveContinuedReplanTests); the two meta-tests range over expectations only and were green. Wired: the whole root
  suite 740 tests passed. Two T-0328 expectations moved with the ruling (R4): DriveDisplayTests' drawing() now carries
  the default session's "0 min · about as quick as the fastest way", and DriveReplanTests.answerBecomesTheDrawnLine
  expects the reply's ETA (900/800) and continued false (the body has no marker) - both literals.
  MUTANTS: planMutants.mjs --only reroute-token-dropped,continued-always,continued-on-recall,continued-never-sent:
  RESULT caught=4 missed=0 trap=0 of 4 (population 68, floor 62 -> 68). drive.py --only 61,67,72,76,81,107-129:
  26 of 28 caught by name; WRONG KILLER 113 (zero refused in the shared isEta made every default-ETA session nil and
  crashed the run before etaBounds reported - a trap, re-aimed per entry point: 113 an answer's zero, new 130 a
  preview's zero) and 124 (never a note: K_WIRE's expected is built through the same public init, so it is not a
  killer; named K_SURF only). --only 113,124,130: caught 3 of 3. Anchors 61/67/72/76/81 moved with the code (a trailing
  argument now follows them) and are caught; E5 now mutates DriveNavigator's DriveSession(preview:online:) call (still
  device-only; its seeding is CAUGHT through entries 120-122). Floor 106 -> 130, MIN_TEST_FILES 9 -> 11, FILTER adds
  DriveContinuedTests|DriveContinuedReplanTests.
  GUARDS: check-drive-display.py whitelists the screen's two new lines ("if let note = display.note {",
  "Text(display.etaLine)"): 21 approved lines, --prove-red 6/6. Digests re-approved: 7 Sources rows in
  check-safety-disclaimer-linked-digests.txt, DriveRehearsal/DriveScreen/DriveHost/DriveNavigator in
  check-safety-disclaimer-pinned. DriveHost's guard now calls DriveSession(preview:online:) - the navigator's own
  check, so a preview with an ETA outside 0...86400 s is refused there instead of crashing on the navigator's '!'.
  P-NAV-01 binds 45 names (34 + 8 Swift + 3 vitest).
  iOS CI at f0404eb3: ios-compile success (run 37898274367), ios-screenshot success (run 37898277672). LOOKED AT
  drive-light and drive-dark: the KINKED road line (the rehearsal's reroute, taken through DriveController with its
  ETA 1380/1200 and continued true, drawn from DriveDisplay.line), no caption (guiding), the footer "© MapLibre ·
  Natural Earth · Route data © OpenStreetMap contributors" above the one large End drive action. The shots are the
  MINIMAL surface (15 m/s fixes), so neither the ETA line nor the note is on them, as ruled (P-SAFE-09: moving adds
  nothing); the full surface's two new Text lines are compiled (ios-compile) and whitelisted, not photographed.
