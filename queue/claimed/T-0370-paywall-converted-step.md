---
id: T-0370
title: The paywall's converted step - paywall(.converted) on a verified purchase from the store view
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T09:42:28Z
lease_expires_at: 2026-10-17T09:42:28Z
worktree: .worktrees/T-0370
branch: task/T-0370
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/]
pins_affected: [P-PRIV-05, P-STORE-01]
reviewer: null
depends_on: [T-0361]
verify: [ops/test, ops/check-pins]
acceptance: []
---
## Brief

T-0361 (R7) wired `paywall(.shown)` (PaywallScreen's appearance, Entitlements' `paywallShown` key) and left
`.converted` unwired: StoreKit's `onInAppPurchaseCompletion` on SubscriptionStoreView replaces the view's default
completion handling, a purchase-flow change no Linux test or screenshot sees. MEASURE how the app finishes
transactions today (Transaction.updates? none?) and rule where a verified purchase is observed - the store view's
completion with the default behaviour kept, or a transaction listener in PlanAdapter - before code. The emit line
`record(TelemetryEvent.paywall(step))` in LiveTelemetry stays the case's one emit row.

## Log
- 2026-10-16T02:32:24Z filed by agent/claude-opus-5 (T-0361 owner) from T-0361 R7.
- 2026-10-16T09:42:28Z claimed by agent/claude-opus-5; lease until 2026-10-17T09:42:28Z
