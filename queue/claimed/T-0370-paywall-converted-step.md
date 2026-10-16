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
- 2026-10-16T09:45:04Z MEASURED (main b01c58b2), before code:
  M1 how the app finishes transactions today: it does not. `grep -rn` over every *.swift under apps/ for `finish()`,
     `Transaction.updates`, `Transaction.unfinished`, `onInAppPurchase` and `.purchase(` -> 0 lines. The one
     `Transaction.` line is PlanAdapter/StoreKitAccountToken.swift:14 `for await result in Transaction.all` (reads
     every verified auto-renewable for the account token; finishes nothing). So every store-view purchase today is
     finished by SubscriptionStoreView's DEFAULT completion handling, and nothing listens for Transaction.updates.
  M2 the paywall: Entitlements/PaywallScreen.swift - `SubscriptionStoreView(groupID:)` + `.inAppPurchaseOptions`
     (a fresh appAccountToken per purchase, T-0315 R3) + `.onAppear { shown?() }` (T-0361's `.shown`). No completion
     hook. Entitlements imports DesignSystem, StoreKit, SwiftUI only (P-STORE-01's ENTITLEMENTS import rows); it
     cannot see Telemetry or ScenicKit without a Package.swift dependency.
  M3 telemetry: `PaywallStep` {shown, converted} (Sources/Telemetry/PaywallStep.swift); the case's one emit row is
     LiveTelemetry.swift `record(TelemetryEvent.paywall(step))`; the one site calling it is LiveMoments.swift
     `LiveTelemetry.paywall(.shown)`. `paywall_converted` is already on funnel.py's closed event list.
  M4 guards over the touched files: P-STORE-01 (check-store-links.py, store_links_pinned.py: APP_WIDE needles,
     SEQUENCES incl. "the paywall's modifier chain", FROZEN sha256 of every Entitlements file); P-PRIV-05
     (check-telemetry-emit-sites.txt site rows); P-SAFE-03 (-pinned digests, frozen shell lines incl.
     `.environment(\.paywallShown, { LiveMoments.paywallShown() })`, PINNED_SHELL_DIGEST).
- 2026-10-16T09:45:04Z RULINGS (author rule, before code):
  R1 WHERE a verified purchase is observed: the store view's completion, `onInAppPurchaseCompletion` on PaywallScreen,
     with the default behaviour kept. NOT a Transaction.updates listener in PlanAdapter: StoreKit hands a purchase
     made in the app to the purchase call's caller (here the store view), not to Transaction.updates, so a listener
     would never see the paywall's purchase; and what it DOES see (renewals, another device's purchase, Ask to Buy
     approvals, offer codes) is not a paywall conversion and would over-count.
  R2 the default kept: the modifier REPLACES the store view's default handling, which (M1) is today the app's only
     finisher. Apple's documented default for StoreKit views finishes a verified transaction. The handler therefore
     does exactly that and nothing more: on `.success(.success(.verified(let transaction)))` it awaits
     `transaction.finish()` and THEN calls `converted?()`; every other result (unverified, pending, userCancelled,
     failure) returns untouched - no finish, no event. The paywall stays on screen as today (no dismiss added).
  R3 the seam: a new Entitlements key `PaywallConvertedKey` (own file, mirroring PaywallShownKey) and
     `EnvironmentValues.paywallConverted`; the shell sets `{ LiveMoments.paywallConverted() }`; LiveMoments'
     `paywallConverted()` calls `LiveTelemetry.paywall(.converted)`. The emit line `record(TelemetryEvent.paywall(step))`
     stays the case's one emit row; the guard gains one site row. No Package.swift or pbxproj change.
  R4 privacy unchanged: `paywall_converted` is already a wire event (M3); the closure takes no arguments, so no product
     id, transaction id, price or account token reaches telemetry. Restore (AppStore.sync) and renewals never pass
     through the store view's purchase completion, so they never send it.
  R5 Linux reach: none. The decision is a pattern over StoreKit's `Product.PurchaseResult`/`VerificationResult`
     (Apple-only); `.converted`'s encoding is already Linux-tested (TelemetryTests). No new numeric module, so no
     mutation population. Red-first is by GUARD, each seen red before green: P-STORE-01 gains APP_WIDE whitelists
     for `onInAppPurchaseCompletion`, `finish()` and `paywallConverted`, a SEQUENCE "the paywall's purchase completion"
     (the handler's lines, exactly once, in order), FROZEN rows for the new key file, and --prove-red rows (verified
     guard dropped, finish dropped, converted before finish, shell closure emptied, a second finish site);
     P-PRIV-05 gains the `LiveTelemetry.paywall(.converted)` site row and a --prove-red row (converted sends .shown).
  R6 out of scope, recorded: the app has no Transaction.updates listener (M1), so an Ask to Buy approval or an
     interrupted purchase is never finished by the app. Pre-existing; not changed here.
  R7 screens: no visual change. ios-screenshot's paywall shots (light, dark, AX5 where produced) are looked at to
     confirm the store view still draws.
- 2026-10-16T09:45:04Z ACCEPTANCE (re-quoted at the final commit):
  A1 `python ops/lib/check-store-links.py` -> ok; `--prove-red` -> every row as required, including the new rows.
  A2 `python ops/lib/check-telemetry-emit-sites.py` -> ok, the paywall case still one emit row; `--prove-red` ok.
  A3 `record(TelemetryEvent.paywall(step))` is still the only line constructing TelemetryEvent.paywall; the only
     `LiveTelemetry.paywall(` sites are LiveMoments' `.shown` and `.converted`.
  A4 swift test --jobs 4 --filter TelemetryTests passes (`.converted` encoding unchanged).
  A5 bash check-safety-disclaimer, check-mutate-population, check-mutate-only, check-map-attribution (if present),
     check-line-cap, check-pins-yaml, queue-check -> ok.
  A6 ios-compile and ios-screenshot -> success on the pushed head; paywall shots looked at.
