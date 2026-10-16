---
id: T-0370
title: The paywall's converted step - paywall(.converted) on a verified purchase from the store view
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-16T09:42:28Z
lease_expires_at: 2026-10-17T09:42:28Z
worktree: .worktrees/T-0370
branch: task/T-0370
exclusive: []
touches: [apps/ios/Packages/ScenicApp/Sources/, apps/ios/ScenicDrive/ScenicDriveApp.swift, ops/lib/]
pins_affected: [P-PRIV-05, P-STORE-01]
reviewer: agent/rv2-t0370
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
- 2026-10-16T10:05:00Z RED FIRST (code written, guards not yet moved): `python ops/lib/check-store-links.py` ->
  `P-STORE-01 (ops/lib/check-store-links.py): 3 refusal(s)` - `import : an unapproved line in
  .../Entitlements/PaywallConvertedKey.swift: \`import SwiftUI\``, `the frozen Entitlements source:
  .../PaywallConvertedKey.swift is not an approved file`, `... PaywallScreen.swift's non-blank kept lines hash
  385f9793..., approved 03d478bf...`. `python ops/lib/check-telemetry-emit-sites.py` -> `REFUSED  site not on the
  whitelist: .../PlanAdapter/LiveMoments.swift:         LiveTelemetry.paywall(.converted)` / `FAILED - 1 refusals`.
  Every new --prove-red row RED by name (A1/A2 below), e.g. `RED    converted reported before the finish  <- the
  paywall's purchase completion: the run ... occurs 0 time(s)`, `RED    a second finish site (a listener in
  PlanAdapter)  <- finish(): an unapproved line in .../PlanAdapter/Probe.swift`, `PROVE-RED  the paywall's converted
  moment sends .shown (T-0370) exit 1 (want 1) red`.
- 2026-10-16T10:05:00Z GREEN (head 8d6b013e): FROZEN re-approved (PaywallScreen 385f9793..., PaywallConvertedKey
  c047ccf9...); P-SAFE-03 -pinned rows + PINNED_SHELL_DIGEST d377f58b..., PaywallScreen 73504214..., LiveMoments
  03ed73bf..., new PaywallConvertedKey row 0ed5bb9e...; -frozen gains the shell's
  `.environment(\.paywallConverted, { LiveMoments.paywallConverted() })`.
  A1 `P-STORE-01 source half: ... ok`; `check-store-links --prove-red: 40/40 rows as required (36 mutants refused by
     name, 4 legitimate edits green)` (7 new rows).
  A2 `P-PRIV-05 emit sites: ok - 55 lines approved; 13 of 14 cases emitted once, 1 pending by task`;
     `PROVE-RED  ok - 18 rows`.
  A3 grep: `LiveMoments.swift:34 LiveTelemetry.paywall(.shown)`, `LiveMoments.swift:40 LiveTelemetry.paywall(.converted)`,
     `LiveTelemetry.swift:81 record(TelemetryEvent.paywall(step))` - nothing else.
  A4 `swift test --jobs 4 --filter TelemetryTests` -> `Test run with 21 tests in 7 suites passed`.
  A5 check-safety-disclaimer exit 0; check-mutate-population `the floor of 165 holds`; check-mutate-only `NAME-PAIRS
     OK`; check-map-attribution ok; check-line-cap `none over 300 lines`; check-pins-yaml `PINS-YAML ok pins=51`;
     queue-check `QUEUE OK (367 tasks)`.
  A6 ios-compile run 38883116368 `completed success` (17m8s); ios-screenshot run 38883119438 `completed success`
     (17m43s), both on head 8d6b013e. Shots looked at: paywall-light.png and paywall-dark.png (the run produces no AX5
     paywall shot) - navigation title "Scenic Drive Pro", back chevron, StoreKit's "Subscription Unavailable / The
     subscription is unavailable in the current storefront." (the group id is still PLANNED-asc-group-id, so no
     product loads on CI and no purchase can be driven), and the "Terms of Use" / "Privacy Policy" band at the
     bottom. The completion handler draws nothing, as R7 expected. Observed, not changed here: in the unavailable
     state the store's ground (white in light, #1C1C1E-ish in dark) differs from the links band's `bg`.
- 2026-10-16T10:22:46Z merged origin/main (e8637659, PR #259 T-0375: named-tests.json, PINS.yaml, queue only; no conflict, no digest rows touched). ACCEPTANCE re-run on merged head abac0833: A1 `40/40 rows as required (36 mutants refused by name, 4 legitimate edits green)`; A2 `13 of 14 cases emitted once, 1 pending by task`, `PROVE-RED  ok - 18 rows`; A3 unchanged (no Swift came from main); A4 `Test run with 21 tests in 7 suites passed`; A5 every bare gate exit 0 (disclaimer, mutate-population, mutate-only, map-attribution, line-cap, pins-yaml, `QUEUE OK (367 tasks)`); A6 ios runs above (main brought no apps/ios change).
- 2026-10-16T12:33:07Z agent/claude-opus-5 (orchestrator): rv1 FAIL was ancestry only (origin/main had T-0318's Worker code). Merged origin/main (no conflict); bare gates on the merged head all exit 0: check-safety-disclaimer, check-mutate-population, check-mutate-only, check-telemetry-emit-sites, check-store-links, check-line-cap, check-pins-yaml, check-exec-bits, queue-check. No apps/ios file changed by the merge.
- 2026-10-16T12:44:10Z agent/rv2-t0370 (reviewer, round 2): PASS. git fetch origin; origin/main fbeb99b8, head 7b5ff05e. Merge brought only main changes: git diff 697a21d8..origin/task/T-0370 -- apps/ios is empty, and every file in 697a21d8..head except this task file is one main changed since merge-base e8637659. Bare gates in a detached worktree on 7b5ff05e all exit 0: check-safety-disclaimer, check-mutate-population (floor of 165 holds), check-mutate-only, check-line-cap (678 Swift files, none over 300), check-pins-yaml (pins=51), check-exec-bits, queue-check (QUEUE OK (368 tasks)), check-store-links, check-telemetry-emit-sites (13 of 14 cases emitted once, 1 pending by task), check-ios-compile-guardrails, ios_screenshot_pinned, check-map-attribution. gh pr checks 260 on 7b5ff05e: core pass, pins-source-only pass. git merge-base --is-ancestor origin/main origin/task/T-0370 run last: exit 0. rv1 acceptance results stand; signed off.
