---
id: T-0356
title: Settings has Delete account in at most 3 taps - an AccountClient sends DELETE /account over the session, the app forgets its local identity on success, and P-PRIV-04's client half is held by tests
state: backlog
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: []
touches: [Sources/ScenicAPIClient/, Sources/ScenicKit/, Tests/ScenicAPIClientTests/, Tests/ScenicKitTests/, apps/ios/Packages/ScenicApp/Sources/, ops/lib/, ops/mutate/, pins/PINS.yaml]
pins_affected: [P-PRIV-04]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

Survey 2026-10-10 (M6, P-PRIV-04): services/api/src/account.ts handles DELETE /account and revokes the Apple token
internally (there is no separate /auth/revoke route), but the app has no row - SettingsScreen.swift says Delete
account arrives "with the features they control" - and Sources/ScenicAPIClient has no account client.

MEASURE FIRST: account.ts's request, auth and answers (quote them), what the app holds locally that names the account
(keychain install id, session JWT, paid token, saved drives, learned speeds - which are account data and which are
device data), and App Review 5.1.1(v)'s requirement. RULE the tap path (Settings -> Delete account -> confirm =
3 taps), what is erased on success, and the honest failure copy. Tests: the client by exact request equality and
every answer; the local erase as a table over every stored item; a ScenicKit model test that the path is <= 3
actions. Every apps/ios Swift edit needs the P-SAFE-03 digest re-approval; if the permission classifier refuses it,
ship the Linux slice and say so in stillOpen. The XCUITest half waits on T-0180's xcodeproj lock - record that.

## Log
- 2026-10-10T03:20:00Z filed by agent/claude-opus-5 (orchestrator) from the 2026-10-10 milestone survey (top-2).
