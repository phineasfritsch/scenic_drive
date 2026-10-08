---
id: T-0328
title: The app reroutes through the plan token - it keeps /plan's plan_token with the preview, and when DriveSession asks for a reroute online NavAdapter sends PlanClient.reroute (one 2-dp origin + token + first remaining pin), lands the answer through DriveController's ticket, and redraws the drive line
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-08T17:24:51Z
lease_expires_at: 2026-10-09T03:24:51Z
worktree: .worktrees/T-0328
branch: task/T-0328
exclusive: []
touches: [Sources/ScenicKit/, Sources/ScenicAPIClient/, Tests/, apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/, ops/lib/, ops/mutate/, ops/lib/check-safety-disclaimer-linked-digests.txt, pins/PINS.yaml]
pins_affected: [P-NAV-01, P-PRIV-05, P-ATTR-01]
reviewer: null
depends_on: [T-0319, T-0321, T-0324]
verify: [ops/test, ops/check-pins]
acceptance:
  - "MEASURE then RULE FIRST in a dated Log entry: where plan_token lives on the device after a plan (PlanPreview / PlanResponse, never persisted past the drive, never logged), how NavAdapter's RerouteUnavailable is replaced by a sender built on PlanClient.reroute, how the reroute answer becomes a new DriveLine + pins for DriveController.rerouteArrived, and how DriveScreen draws the rerouted line (rv1-t0324 recordable 4: the screen always draws the preview's line); what happens with a null token (PLANS unbound until the owner binds it): the Worker answers a fresh plan - rule whether the app uses it or rejoins"
  - "The mapping RerouteRequest -> PlanClient.reroute request and reroute answer -> rerouteArrived inputs is pure Linux-tested code with full-equality tables (token present / null, first pin 0 / last / past last, offline edge mid-flight -> the late answer dropped by ticket); no request while offline; P-NAV-01 binds the new tests by name"
  - "ios-compile + ios-screenshot pass; the drive map shows the rerouted line (a DEBUG rehearsal row if ruled feasible); attribution unchanged (P-ATTR-01 green); digests re-approved; population entries MISSED before and CAUGHT by name after"
---
## Brief

T-0319 owner stillOpen 2 (PR #209): the Worker remembers pins + lambda under plan_token and /plan accepts
`reroute: {token, first_pin}`, and ScenicAPIClient has PlanClient.reroute - but the app neither keeps the token nor
calls it; NavAdapter's sender is RerouteUnavailable (T-0321 R3), so every online off-route goes to rejoin mode.
rv1-t0324 recordable 4: DriveScreen always draws the preview's planned line.

## Log
- 2026-10-08T17:21:59Z filed by agent/claude-opus-5 (orchestrator) from T-0319 stillOpen 2 and rv1-t0324 recordable 4.
- 2026-10-08T17:24:51Z claimed by agent/claude-opus-5; lease until 2026-10-09T03:24:51Z
- 2026-10-08T17:32:02Z MEASURE then RULE (agent/claude-opus-5, owner). MEASURED at f98572c5: (m1) PlanResponse decodes
  `plan_token` (T-0319 R6) but ClientPlanner.preview(of:) copies route, ETAs, hazards, waypoints and lambda only - the
  token is dropped on the device; PlanTicket (place, budgetMinutes) never reaches the preview. (m2) DriveNavigator's
  `sender` defaults to RerouteUnavailable and DriveHost/the shell pass none, so every online off-route throws at once
  and rejoins. (m3) PlanAdapter/LivePlanner.swift is the only ScenicAPIClient importer under apps/ios; NavAdapter
  imports ScenicKit + Ferrostar only, and Package.swift is serial (not in touches) - NavAdapter cannot import
  PlanAdapter. (m4) services/api/src/plan.ts:108-111 recalls the token from PLANS and uses it only when device, place
  and first_pin <= pins.length agree; anything else is the fresh plan below it, and EVERY 200 carries a new
  plan_token (line 121). reroutePlanner.ts returns `waypoints = decisionPoints(chosen)` - fresh decision points on the
  new line, not the remembered pins - so a reroute answer and a fresh answer have the same shape. (m5)
  services/api/wrangler.jsonc binds no PLANS (grep: 0 lines), so in prod today plan_token is absent (null on the
  device). (m6) DriveScreen draws DriveMapLine.route(for: preview) - the preview's line forever (rv1-t0324 rec. 4).
  (m7) ios-screenshot.yml: SETTLE=15 s; the drive shot starts `simctl location` at 15 m/s along DriveRehearsal.line's
  four points before launch. (m8) SavedDraft.of(preview) reads route, waypoints and lambda only; PlanPreview is not
  Codable; no print/os_log names a token under Sources/ or apps/ios.
  RULINGS. R1 WHERE THE TOKEN LIVES: a new ScenicKit value PlanContinuation {token, place, budgetMinutes};
  PlanPreview.continuation is non-nil exactly when the Worker sent a plan_token, built by
  ClientPlanner.preview(of:place:budgetMinutes:) from the response and the ticket. It is held in memory only: never
  Codable, never in SavedDraft (a Linux test holds SavedDraft.of equal with and without it), never printed. The drive's
  CURRENT token lives in DriveSession.planToken (seeded from the preview), rides each RerouteRequest, and is replaced by
  the answer's token only when DriveSession takes that answer; it dies with the drive. R2 THE SENDER: ScenicAPIClient
  PlanRerouter (RerouteSending; client, place, budgetMinutes): a request with no token throws RerouteUnavailable with
  ZERO requests; otherwise ONE PlanClient.reroute(request, token:, place:, budgetMinutes:) (the origin rounded to 2 dp
  there, T-0319 R9) and the 200 mapped by PlanRerouter.reply(of:) to RerouteReply(line: route, waypoints, planToken).
  PlanAdapter's LivePlanner.rerouter(for: preview) builds it (still the only ScenicAPIClient importer) and answers
  RerouteUnavailable without an https base or a continuation; the shell hands it to DriveHost(preview:sender:content:),
  which hands it to DriveNavigator. RerouteUnavailable stays as that fallback. R3 THE ANSWER: RerouteReply gains
  planToken; DriveController.rerouteArrived passes line, waypoints and token to DriveSession.rerouteArrived - all three
  taken together or none; a late answer is dropped by ticket before the session sees it, so its token is never taken.
  R4 THE DRAWN LINE: DriveDisplay gains `line` (DriveDisplay(session:) = session.line.coordinates; the surface x mode
  table rows carry []); DriveScreen draws DriveMapLine.route(for: display.line) and redraws on change of display.line,
  so a taken reroute is the line on the map. The credit is unchanged: the MapRoute still carries
  PlanPreview.attribution and the footer composes it with the basemap's (P-ATTR-01). R5 NULL TOKEN (PLANS unbound):
  the app makes NO request and rejoins, exactly as offline - a reroute without a token cannot name the drive it
  continues, and a fresh origin-to-place plan is not the rest of THIS drive (P-NAV-01). A token the Worker no longer
  remembers (12 h TTL, evicted, PLANS unbound after the plan) gets a fresh plan the device cannot tell from a reroute
  (m4); the app TAKES it - same 2-dp origin, same place, same budget ceiling, its pins on its line - and the
  Worker-side flag that would let the app rule otherwise is recorded as a follow-up (services/ is not in touches).
  R6 BUDGET: each reroute sends the ticket's budgetMinutes unchanged; the Worker re-measures the fastest route from the
  new origin, so the ceiling holds per answer. The drive screen's ETA line stays the preview's (recorded, not ruled
  here). R7 PRIVACY: a reroute is sent only on DriveController's `.send`, never offline; one 2-dp coordinate per send
  (Linux tests through the controller, PlanRerouter and a recording transport). R8 DEBUG REHEARSAL ROW: FEASIBLE inside
  m7's 15 s. DriveRehearsal's planned line becomes the simulated path shifted 0.003 deg north (~333 m > 50 m), so the
  15 m/s fixes are off-route after the 5 s dwell; DriveRehearsal.rerouter (DEBUG with `-screen drive`, else nil)
  answers at once with the simulated path itself, so the drive shot shows the rerouted line under the puck and no
  caption. The shell line becomes `sender: DriveRehearsal.rerouter ?? LivePlanner.rerouter(for: drive)`. R9 TESTS AND
  POPULATION: new ScenicAPIClientTests suite DriveReplanTests - the cross product token {present, null} x first pin
  {0, last, past last} through DriveController + PlanRerouter + a recording transport, each request and each taken
  answer compared WHOLE to a recomputation, with a meta-test that no row ignores its variant; the offline edge
  mid-flight (late answer dropped by ticket, token kept); zero requests while offline. Named in P-NAV-01's
  named-tests entry. ops/mutate/drive.py gains PlanRerouter.swift, PlanContinuation.swift and ClientPlanner.swift as
  subjects with entries MISSED at f98572c5's tests and CAUGHT by the new names. R10 GUARDS RE-APPROVED IN THE SAME
  DIFF: check-drive-display.py's whitelist (screen, host, shell lines), check-safety-disclaimer-frozen's
  FROZEN_APP_SHELL shell line, the -linked digest rows and -pinned's digests of the touched app files.
- 2026-10-08T18:36:03Z RED then GREEN (owner). RED by name with the API in place and its wiring stubbed (token not carried, answer's
  token not taken, PlanRerouter throwing at once, continuation nil, DriveDisplay(session:) drawing []): swift test
  --filter DriveReplanTests|DriveDisplayTests|SavedDraftTests|Drive*Tests - FAILED tokenByFirstPin (3 issues, the
  three token-present rows), answerBecomesTheDrawnLine (4), lateAnswerDroppedByTicket (2), previewKeepsTheToken (1),
  sessionDisplayFollowsTheSession (6); noRowIgnoresItsVariant and offlineSendsNothing green (they hold today's
  behaviour). GREEN after wiring: ScenicKitTests + ScenicAPIClientTests 475/475; NAMED P-NAV-01 passed=34/34.
  ios-compile success (run 37820194624 at 258eb378; 37823842530 at 8ee0775d); ios-screenshot success (run
  37820201191): the drive shot showed one kinked line and no caption - consistent with a taken reroute, but the
  planned line was the road shifted north, the same shape, so the shot could not tell them apart. R8 AMENDED: the
  rehearsal's planned line is ONE straight segment (first to last point, shifted 0.003 deg north), so a kinked
  three-segment line in the shot is the reroute's. POPULATION: drive.py --only 16,55,56,58-74 at c96fde9f: 17/20
  caught, entry 62 WRONG KILLER (the drawn-line test cannot see a reply token both sides drop; killers corrected to
  token x first pin + late answer), 71 and 73 MISSED (previewKeepsTheToken compared against a want built by the
  same inits - a mutant in PlanContinuation.init or PlanPreview.init moved both sides); the test now also reads the
  continuation back field by field against literals; --only 62,71,73 at 8ee0775d: MUTATE OK caught=3/3.
  --prove-vacuity --only 58-74: VACUITY PROOF OK, MISSED=17 of 17 with the 7 test files emptied. Anchors 16/55/56
  moved with the code (old text gained a trailing argument) and are still caught. RerouteReply.swift left the
  P-PROC-06 allowlist (it is a drive.py subject now); check-mutate-population: floor of 138 holds. Follow-up T-0330
  filed (R5's fresh-vs-continued marker; R6's ETA line).
