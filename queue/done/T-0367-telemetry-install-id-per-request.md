---
id: T-0367
title: TelemetryClient takes an install-id provider and reads it per request, held by a Linux test, so the Apple-only InstallBoundTelemetry rebuild is no longer the only guard against sending a deleted account's id
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T06:29:40Z
lease_expires_at: 2026-10-17T06:29:40Z
worktree: .worktrees/T-0367
branch: task/T-0367
exclusive: []
touches: [Sources/Telemetry/, Tests/TelemetryTests/, apps/ios/Packages/ScenicApp/Sources/PlanAdapter/, ops/lib/, ops/mutate/]
pins_affected: [P-PRIV-04, P-PRIV-05]
reviewer: agent/rv2-t0367
depends_on: [T-0356]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0356 (PR #243) R3 says nothing links later use to a deleted account. Its A10 fix lives in the Apple-only
PlanAdapter: InstallBoundTelemetry reads StoredInstallID().installID() on every record and rebuilds the
TelemetryClient when the id changes. rv2-t0356 recorded that no Linux test holds it - a mutant that reads the id once
per launch passes every suite; only the P-SAFE-03 digest, the emit-site whitelist and ios-compile stand in the way.

Move the per-request read into Sources/Telemetry: TelemetryClient (or its transport) takes an id provider and stamps
x-scenic-device from it on each request. A Linux test through the shipping client: two records with the provider's
id changed between them produce two requests whose x-scenic-device headers equal the two ids (whole-request
equality); a population entry that caches the first id is MISSED before and CAUGHT by that test's name after.
InstallBoundTelemetry then shrinks to wiring (or goes), with its digest and emit-site rows re-approved. If the
permission classifier refuses an apps/ios digest re-approval, ship the Linux slice and say so.

## Log
- 2026-10-16T01:20:00Z filed by agent/claude-opus-5 (orchestrator) from rv2-t0356's recordable and T-0356 owner
  stillOpen (ids checked on main and task/T-0363, task/T-0364: highest T-0366).
- 2026-10-16T06:29:40Z claimed by agent/claude-opus-5; lease until 2026-10-17T06:29:40Z
- 2026-10-16T06:34:14Z MEASURED on task/T-0367 at 6681d944 (main):
  M1 `grep -rl "InstallBoundTelemetry\|StoredInstallID" Tests Sources` -> 2 files, both
  Sources/ScenicAPIClient (InstallIDDecision.swift, LocalAccountItem.swift), neither a test: no Linux test reaches
  the per-record id read. M2 `TelemetryClient(base:` is constructed at exactly 3 sites: TelemetryClientTests.swift
  (1, `device: device`, one constant UUID), URLSessionTelemetryTransportTests.swift (1) and
  PlanAdapter/InstallBoundTelemetry.swift (1). Every Linux request therefore carries ONE id, so a client that
  freezes its id at init is indistinguishable from today's to every Linux suite. M3 (reading
  InstallBoundTelemetry.record): it awaits the CURRENT client's `record`; that actor call returns at once when a post
  is in flight (the event joins `waiting`). If the id changes while that post is in flight, the old client's loop
  later posts the waiting event under the OLD id - after the change - while the new client posts later events under
  the new id. So today's guard also has an in-flight window in which a deleted id is still sent.
- 2026-10-16T06:34:14Z RULINGS (owner, before code):
  R1 Telemetry may not import ScenicAPIClient (root Package.swift: TelemetryTests -> Telemetry only; Package.swift is
  serial-only and not in touches), so `InstallIDProvider` is not reachable. TelemetryClient takes the provider as a
  `@Sendable () -> UUID` closure: `init(base:device:transport:)` with `device: @escaping @Sendable () -> UUID`.
  The fixed-UUID init goes - one constructor, so no shipping path can freeze the id.
  R2 "on each request" (Brief) = the provider is called when each POST is built, inside the send loop, never at
  init and never at `record`. This closes M3's in-flight window too: a batch waiting behind an in-flight post is
  stamped with the id current when ITS post is built. Within one id nothing changes: R3 batching, capacity and
  fail-quiet are T-0355's.
  R3 InstallBoundTelemetry GOES. LiveTelemetry holds `TelemetryClient?` built with
  `device: { StoredInstallID().installID() }` and URLSessionTelemetryTransport. Its digest row is removed and
  LiveTelemetry's re-approved in ops/lib/check-safety-disclaimer-pinned; the emit-site whitelist
  (ops/lib/check-telemetry-emit-sites.txt) loses the InstallBoundTelemetry site rows and follows LiveTelemetry's
  changed lines. No privacy behaviour changes beyond the Brief: same header name, same lowercase uuid, same
  provider (StoredInstallID), read more often.
  R4 The new test lives in TelemetryClientTests, which P-PRIV-05's named swift filter already runs (a red there is
  red in that run). Binding its NAME into named-tests.json needs a pins/PINS.yaml digest/count re-approval, and
  pins/ is not in touches: recorded as open, not done here.
  R5 Population: posttelemetry_mutations.py gains entry 17 (the first id cached at init - the "once per launch"
  mutant rv2-t0356 named) and entry 18 (the id read once per sending run), killers = the new test's name. 17 is
  shown MISSED with the new test absent and CAUGHT with it; 18 CAUGHT. Existing anchors that name `headers` or
  `device.uuidString` move with the code (6, 10, 11, 13 and SEND).

## Acceptance
1. `swift test --jobs 4 --scratch-path .build/t-0367 --filter TelemetryTests.TelemetryClientTests` passes, including
   `everyRequestStampsTheProvidersCurrentID()`: through the shipping `TelemetryClient.record`, rows over the id
   sequence {same id twice, id changed between two completed records, id changed while the first post is in flight
   and the second event waits}; each row's sent requests EQUAL `[expected([e1], id_a), expected([e2], id_b)]`
   recomputed in the test (whole request: url, method, headers, body), with id_a/id_b functions of the row; a
   meta-check that the two ids' expected requests differ.
2. Seen RED first by name: the test red against a client that caches its first id (posttelemetry entry 17) and one
   that reads once per run (entry 18); entry 17 MISSED with the test absent; then
   `python ops/mutate/posttelemetry.py --only 17,18` CAUGHT by `everyRequestStampsTheProvidersCurrentID()`.
3. `grep -rn "InstallBoundTelemetry" apps Sources Tests ops/lib` -> no line; LiveTelemetry builds the one client with
   `device: { StoredInstallID().installID() }`.
4. Gates green: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-mutate-anchors,
   check-telemetry-emit-sites, check-line-cap, check-pins-yaml, check-exec-bits, queue-check.
5. ios-compile and ios-screenshot on task/T-0367: success, relevant shots looked at.

## Log (work)
- 2026-10-16T06:54:47Z ba3fdb16 (code, killer test ABSENT), `python ops/mutate/posttelemetry.py --only 17,18`:
  `MISSED 17 the install id read once, at init exit=0 no test objected` /
  `MISSED 18 the install id read once per sending run exit=0 no test objected` /
  `MUTATE FAILED caught=0/2 equivalent_caught=0 (--only: 2 of 18 entries)`.
  43a63bc6 (test added), same command: `caught 17 ... by: everyRequestStampsTheProvidersCurrentID()` /
  `caught 18 ... by: everyRequestStampsTheProvidersCurrentID()` / `MUTATE OK caught=2/2 equivalent_caught=0`.
  The moved anchors re-run (`--only 6,7,10,11,13`): `MUTATE OK caught=5/5 equivalent_caught=0`.
  Emit-site guard seen RED on the rewire before its rows moved: `P-PRIV-05 emit sites: FAILED - 13 refusals`
  (4 new LiveTelemetry lines not on the whitelist, 9 approved InstallBoundTelemetry/LiveTelemetry lines missing),
  then `ok - 54 lines approved; 13 of 14 cases emitted once, 1 pending by task`.
  Digests re-approved: LiveTelemetry.swift 3d795866...0bc0 (pinned), InstallBoundTelemetry row removed,
  Sources/Telemetry/TelemetryClient.swift 8b8c06e8...f730 (linked-digests).
- 2026-10-16T07:16:00Z on 43a63bc6: ios-compile run 38863380880 success (3m32s); ios-screenshot run 38863383999 success
  (15m23s). Telemetry draws nothing, so I looked at the launch surfaces LiveTelemetry is reached from:
  home-light-medium.png renders the map, attribution and the Saddle Peak sheet. The home's "Plan a drive" chip is
  drawn over the Saddle Peak / Westwood loop chips. plan-offered-light.png shows the "Not much pretty within 25
  extra minutes" sheet. This diff changes no view file, so neither shot is a change from this task: noted, not
  ruled.
  `bash ops/lib/check-safety-disclaimer` exit 0 (Frozen; 33 feature files, shell, footer pinned; LAST all 108 app
  .swift, then 326 root + pbxproj files).
- 2026-10-16T07:16:29Z ACCEPTANCE re-run on 151daea8 (origin/main be5e64e9 merged; the merge changes nothing under Sources/Telemetry,
  Tests/TelemetryTests or the population):
  1. `swift test --filter TelemetryTests`: `Test everyRequestStampsTheProvidersCurrentID() passed`,
     `Test run with 21 tests in 7 suites passed`.
  2. posttelemetry 17/18: MISSED 0/2 on ba3fdb16 (test absent), `MUTATE OK caught=2/2` on 43a63bc6 by
     everyRequestStampsTheProvidersCurrentID(); moved anchors `--only 6,7,10,11,13` caught 5/5.
  3. `grep -rn InstallBoundTelemetry apps Sources Tests ops/lib` -> 0 lines.
  4. Every gate exits 0: mutate-population (floor 165), mutate-only, mutate-anchors (17 drivers), emit-sites (54 lines,
     13 of 14 emitted, 1 pending), line-cap (674 files), pins-yaml (50 pins), exec-bits, queue-check (364 tasks),
     check-safety-disclaimer.
  5. ios-compile 38863380880 success, ios-screenshot 38863383999 success (on 43a63bc6; nothing under apps/ changed after).
- 2026-10-16T08:44:29Z agent/claude-opus-5 (owner): rv1-t0367 FAIL was ancestry-only (main gained PR #253 T-0372, #256 T-0374, #257 T-0373). Merged origin/main as cdae75f5, no conflicts. On cdae75f5: swift test --filter TelemetryTests "Test run with 21 tests in 7 suites passed"; posttelemetry --only 17,18 "MUTATE OK caught=2/2"; bare gates rc=0: check-safety-disclaimer, check-mutate-population (floor 165), check-mutate-only, check-mutate-anchors (17 drivers), check-telemetry-emit-sites ("ok - 54 lines approved; 13 of 14 cases emitted once, 1 pending by task"), check-pins-yaml (pins=51), check-exec-bits, queue-check (365). ios-compile run 38874471124 success on cdae75f5; ios-screenshot run 38874475204 dispatched on cdae75f5; linux-core 38874477506 success. Recorded, not closed here: the app half (LiveTelemetry freezing the id) is held only by the P-SAFE-03 digest and the P-PRIV-05 emit-site whitelist; binding everyRequestStampsTheProvidersCurrentID() by name in named-tests.json needs a PINS.yaml re-approval (follow-up).
- 2026-10-16T09:01:17Z agent/rv2-t0367 (reviewer, round 2, ancestry only): PASS on origin/task/T-0367 cd722f6c (origin/main c2499ed6). `git diff --name-only origin/main...origin/task/T-0367` = 11 files, all this PR's: Sources/Telemetry/TelemetryClient.swift, Tests/TelemetryTests/{ScriptedInstallID,TelemetryClientTests,URLSessionTelemetryTransportTests}.swift, PlanAdapter/{InstallBoundTelemetry (removed),LiveTelemetry}.swift, ops/lib/{check-safety-disclaimer-linked-digests.txt,check-safety-disclaimer-pinned,check-telemetry-emit-sites.txt}, ops/mutate/posttelemetry_mutations.py, this task file. `git diff --stat cdae75f5 origin/task/T-0367` = this task file only (1 insertion). Bare in a detached worktree at cd722f6c, all rc=0: check-safety-disclaimer ("Frozen (-frozen); 33 feature file(s), shell, footer pinned (-pinned); doors over 108 .swift (-doors); LAST all 108 app .swift, then 326 root + pbxproj file(s) (-linked)."); check-telemetry-emit-sites ("P-PRIV-05 emit sites: ok - 54 lines approved; 13 of 14 cases emitted once, 1 pending by task"); check-mutate-population ("P-PROC-06: every added module is covered or allowlisted; the floor of 165 holds", 0 added by this branch); check-pins-yaml ("PINS-YAML ok pins=51 fields=411"); queue-check ("QUEUE OK (365 tasks)"). CI on cdae75f5: ios-compile 38874471124 conclusion success; ios-screenshot 38874475204 status completed, conclusion success. `gh pr checks 254`: core pass 7m32s, pins-source-only pass 3m48s (run 38875721604). LAST, after a fresh fetch: `git merge-base --is-ancestor origin/main origin/task/T-0367` exit 0; origin/main unchanged at c2499ed6, no drift. The rv1 code PASS stands; the app-half follow-up recorded above is the owner's to file.
