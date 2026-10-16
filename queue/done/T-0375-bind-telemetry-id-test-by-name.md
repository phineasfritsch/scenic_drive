---
id: T-0375
title: P-PRIV-05 binds everyRequestStampsTheProvidersCurrentID() by name, so deleting the per-request install-id test is caught, not only weakened inside the suite filter
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T09:15:21Z
lease_expires_at: 2026-10-17T09:15:21Z
worktree: .worktrees/T-0375
branch: task/T-0375
exclusive: []
touches: [ops/lib/named-tests.json, pins/PINS.yaml, queue/]
pins_affected: [P-PRIV-05]
reviewer: agent/rv1-t0375
depends_on: [T-0367]
verify: [ops/check-pins]
acceptance: []
---
## Brief

T-0367 (PR #254) moved the per-request install-id read into Sources/Telemetry and added
TelemetryClientTests.everyRequestStampsTheProvidersCurrentID() (rows: same id, id changed after a post, id changed
while a post is in flight). It runs inside P-PRIV-05's named swift filter, but its NAME is not in
ops/lib/named-tests.json, so deleting it leaves `run-named-tests.py P-PRIV-05` green (T-0367 R4: pins/ was outside
touches). Bind it by name, re-approve whatever PINS.yaml digest or count P-PRIV-05 carries, and show the binding
red by deleting the test (run-named-tests reports it MISSING) then green.

## Log
- 2026-10-16T09:40:00Z filed by agent/claude-opus-5 (orchestrator) from T-0367 R4 / rv2-t0367 (ids checked on main
  and task/T-0318, task/T-0368: highest T-0374).
- 2026-10-16T09:15:21Z claimed by agent/claude-opus-5; lease until 2026-10-17T09:15:21Z
- 2026-10-16T09:16:43Z MEASURED on task/T-0375 at 7fb516e2 (main + queue commits):
  M1 ops/lib/named-tests.json `P-PRIV-05` has keys [vitest, swift]; vitest binds 37 names; swift `filter` already
  runs `TelemetryTests\\.(...|TelemetryClientTests)`, and `tests` binds 37 distinct names, five of them
  TelemetryClientTests (everyEventPostsExactlyItsRequest(), waitingBoundTable(waiting:), everyOutcomeDropsTheBatch(),
  capacityIsTheWorkersCap(), recordedOnlyAfterTheFirstPostReturns()). `everyRequestStampsTheProvidersCurrentID` occurs
  in no line of named-tests.json or PINS.yaml; it is declared at Tests/TelemetryTests/TelemetryClientTests.swift:110
  as `@Test func everyRequestStampsTheProvidersCurrentID() async throws`, so its xunit identifier is
  `TelemetryTests.TelemetryClientTests/everyRequestStampsTheProvidersCurrentID()`.
  M2 P-PRIV-05's `assertion` is check-telemetry-emit-sites.py && check-learned-speeds-sites.py &&
  run-named-tests.py P-PRIV-05 - no check-named-table.py, so the pin carries NO digest and no machine-checked count.
  Its only recorded count is prose in `why_no_test_catches_it`, last sentence T-0365: "the row binds 37 Swift tests".
- 2026-10-16T09:16:43Z RULINGS (author rule, before code):
  R1 Brief "re-approve whatever PINS.yaml digest or count P-PRIV-05 carries" vs M2: there is no digest to re-approve.
  The count lives only in why_no_test_catches_it, so this task appends one dated T-0375 sentence there (the row binds
  38 Swift tests; seen RED/green as below) and edits no earlier sentence.
  R2 Adding check-named-table.py to P-PRIV-05 (a digest over the entry) is NOT done here: the Brief does not ask for
  it, and T-0318 (in flight) may edit P-PRIV-05's vitest rows, which would make two branches re-approve one digest.
  It is recorded as still open: a row dropped from P-PRIV-05's table, with the test, stays green.
  R3 On this Windows box UserStorePrivacyTests is GRDB-gated and does not build, so run-named-tests reports
  `PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail()` MISSING and exits 1 everywhere here (pin
  text, T-0290). Green on this box therefore means: every name passed except that one, which is MISSING; CI's Linux
  core job is the whole green. Red means the bound test is reported MISSING BY NAME in addition.

## Acceptance
1. `ops/lib/named-tests.json` P-PRIV-05 `swift.tests` contains
   `TelemetryTests.TelemetryClientTests/everyRequestStampsTheProvidersCurrentID()` exactly once; 38 distinct swift
   names; the filter and the vitest half are unchanged (`git diff origin/main -- ops/lib/named-tests.json` is that
   one added line plus its preceding line's comma).
2. pins/PINS.yaml P-PRIV-05 `why_no_test_catches_it` ends with a dated T-0375 sentence recording the binding and
   "38 Swift tests"; no other field and no earlier sentence changes; `python ops/lib/check-pins-yaml.py` exit 0.
3. Seen RED by name: with `everyRequestStampsTheProvidersCurrentID()` deleted from TelemetryClientTests.swift (not
   committed), `SCENIC_SWIFT_SCRATCH=.build/t0375 python ops/lib/run-named-tests.py P-PRIV-05` reports that name
   MISSING (beside the R3 environment MISSING) and exits 1; under the pre-binding table the same deletion does NOT
   name it (the gap). The file is then restored and its sha256 equals the committed blob's.
4. GREEN: the same command on the restored tree reports the bound name passed; the only non-pass is R3's
   UserStorePrivacyTests MISSING.
5. Gates: `python ops/lib/check-pins-yaml.py`, `bash ops/queue-check`, `python ops/lib/check-mutate-population.py`
   exit 0 on the merged head.

## Log (work)
- 2026-10-16T09:27:13Z red/green on aa938e25 + the binding, driver `.worktrees/t0375-drive.py red` (outside the repo
  tree; deletes lines 106-141 of TelemetryClientTests.swift - the doc comment, the test and its trailing blank line -
  in memory-checked bytes, runs `run-named-tests.py P-PRIV-05` with SCENIC_SWIFT_SCRATCH=.build/t0375, restores):
  `committed blob sha256 1e10fe05e7cd0412fbc14b82343686a70b844f198b03b1ca61cff4eefdbe223d worktree sha256 1e10fe05...223d equal True`
  A pre-binding table, test DELETED: `exit=1` / `RED PlaceStoreTests.UserStorePrivacyTests/noColumnNamesAPlaceOrATrail(): MISSING - no test of this name ran` /
  `NAMED P-PRIV-05 passed=73/74` - the deletion is not named (the gap the Brief describes; same result as an intact tree).
  B bound table, test DELETED: `exit=1` / the same UserStorePrivacyTests MISSING line /
  `RED TelemetryTests.TelemetryClientTests/everyRequestStampsTheProvidersCurrentID(): MISSING - no test of this name ran` /
  `NAMED P-PRIV-05 passed=73/75`.
  `restored sha256 1e10fe05e7cd0412fbc14b82343686a70b844f198b03b1ca61cff4eefdbe223d == committed blob True`
  C bound table, test RESTORED: `exit=1` / the UserStorePrivacyTests MISSING line only / `NAMED P-PRIV-05 passed=74/75`
  (green per R3: the bound name passed; the one non-pass is the Windows GRDB environment).
- 2026-10-16T09:31:00Z ACCEPTANCE re-run at b5984ad7 after `git fetch origin` + `git merge origin/main` (`Already up
  to date.`; origin/main 7fb516e2 is an ancestor, so 3 and 4 above ran on this tree's content):
  1. P-PRIV-05 swift.tests: the bound name `count 1`, `distinct 38`, vitest 37 (unchanged); `git diff origin/main --
     ops/lib/named-tests.json` is the comma on recordedOnlyAfterTheFirstPostReturns() plus the one added line.
  2. `git diff origin/main -- pins/PINS.yaml`: one line changed (P-PRIV-05 why_no_test_catches_it, T-0375 sentence
     appended); `PINS-YAML ok pins=51 fields=411` exit 0.
  3./4. as quoted in the 09:27:13Z entry (73/74 unseen, 73/75 MISSING by name, restored sha256 equal, 74/75).
  5. `PINS-YAML ok pins=51 fields=411` rc=0; `QUEUE OK (366 tasks)` rc=0; `P-PROC-06: every added module is covered
     or allowlisted; the floor of 165 holds` rc=0.
- 2026-10-16T09:40:13Z REVIEW PASS (round 1) by agent/rv1-t0375 of PR #259 at a2f11f0e (not the owner). Acceptance
  block committed before code: aa938e25 touches only this task file; b5984ad7 carries named-tests.json + PINS.yaml.
  Binding red re-shown in a separate worktree by RENAMING the test (`everyRequestStampsTheProvidersCurrentID()` ->
  `...CurrentIDRenamed()`): `python ops/lib/run-named-tests.py P-PRIV-05` rc=1, `RED
  TelemetryTests.TelemetryClientTests/everyRequestStampsTheProvidersCurrentID(): MISSING - no test of this name ran`,
  `NAMED P-PRIV-05 passed=73/75`. Restored with `git checkout --` (status clean): rc=1, only the GRDB-gated
  UserStorePrivacyTests MISSING (Windows environment, R3), `NAMED P-PRIV-05 passed=74/75`. swift.tests 38 names, 38
  distinct. Gates run bare: `PINS-YAML ok pins=51 fields=411` rc=0; `QUEUE OK (366 tasks)` rc=0; `P-PROC-06: every
  added module is covered or allowlisted; the floor of 165 holds` rc=0. `gh pr checks 259` (once): core pass 8m16s,
  pins-source-only pass 3m22s (core is where UserStorePrivacyTests runs). `git merge-base --is-ancestor origin/main
  origin/task/T-0375` rc=1: origin/main 8cf3c3c4 is ahead by one queue-only commit (queue: file T-0376, one new task
  file), acceptable drift. Open gap carried from the owner's stillOpen 2: P-PRIV-05 has no check-named-table digest,
  so dropping a name with its test stays green; worth filing after T-0318 merges.
