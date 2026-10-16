---
id: T-0367
title: TelemetryClient takes an install-id provider and reads it per request, held by a Linux test, so the Apple-only InstallBoundTelemetry rebuild is no longer the only guard against sending a deleted account's id
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T06:29:40Z
lease_expires_at: 2026-10-17T06:29:40Z
worktree: .worktrees/T-0367
branch: task/T-0367
exclusive: []
touches: [Sources/Telemetry/, Tests/TelemetryTests/, apps/ios/Packages/ScenicApp/Sources/PlanAdapter/, ops/lib/, ops/mutate/]
pins_affected: [P-PRIV-04, P-PRIV-05]
reviewer: null
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
