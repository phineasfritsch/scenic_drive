---
id: T-0271
title: Entitlements target - the paywall (SubscriptionStoreView with Terms of Use + Privacy links, Restore) and a Settings screen (subscription, Restore, Manage subscription, Terms, Privacy, Legal/Attribution) reachable from home; P-STORE-01 source half
state: ready
owner: null
owner_session: null
claimed_at: null
lease_expires_at: null
worktree: null
branch: null
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Sources/Entitlements/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/, .github/workflows/ios-screenshot.yml, ops/lib/, pins/PINS.yaml]
pins_affected: [P-STORE-01, P-ATTR-02]
reviewer: null
depends_on: []
verify: [ops/test, ops/check-pins]
acceptance:
  - "a new Apple-package target Entitlements (StoreKit + SwiftUI + DesignSystem only; NOT a feature target that a feature imports) added to the FeatureScenicHome LIBRARY PRODUCT's targets list so the app links it with NO project.pbxproj edit (the xcodeproj lock is held elsewhere); the app shell composes it: home exposes a settings action (a callback, so FeatureScenicHome never imports Entitlements) and the shell presents Settings, which opens the Paywall"
  - "Paywall = SubscriptionStoreView for one ruled subscription group id (a typed constant; the plan's $29.99/yr, 7-day trial live in App Store Connect, not in code) with .subscriptionStoreControlStyle and .storeButton(.visible, for: .restorePurchases) and BOTH a Terms of Use and a Privacy Policy link (URLs as typed constants pointing at the docs/store pages' planned hosting - rule them; mark PLANNED); Settings lists subscription status, Restore (AppStore.sync()), Manage subscription (showManageSubscriptions), Terms, Privacy and Legal/Attribution (the ODbL notice text from NOTICE/LICENSE-DATA, P-ATTR-02); every control has an accessibility identifier"
  - "P-STORE-01's source half registered in pins/PINS.yaml as a fail-closed whole-line WHITELIST check under ops/lib (identifiers + SubscriptionStoreView + restorePurchases + both links present in exactly the approved files), seen RED by named mutants (link removed, restore hidden, paywall without SubscriptionStoreView) then green; ios-screenshot gains -screen settings|paywall launch-argument shots (DEBUG-only) and its pinned guard moves with it; ios-compile and ios-screenshot dispatched on the branch GREEN with the new PNGs downloaded and looked at (quote what they show)"
---
## Brief

Plan M6 'StoreKit 2 ... Restore row (AppStore.sync()) ... paywall = SubscriptionStoreView with Terms of Use + Privacy
links' and pin P-STORE-01 (Terms + Privacy in Settings AND paywall; SubscriptionStoreView used; Restore row present).
Screens: Settings (vehicle later, subscription + Restore + management deep link, Terms, Privacy, Legal/Attribution).
No App Store Connect setup, no purchases: the paywall renders its own empty/loading state on CI without products,
which is fine - the shot proves the links and Restore are on screen. The XCUITest half of P-STORE-01 waits for the
xcodeproj lock (T-0180).

## Log
- 2026-10-06T00:40:41Z filed by agent/claude-opus-5 (orchestrator) from the milestone gap map (M6 paywall/settings).
