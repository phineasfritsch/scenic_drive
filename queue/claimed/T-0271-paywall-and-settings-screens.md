---
id: T-0271
title: Entitlements target - the paywall (SubscriptionStoreView with Terms of Use + Privacy links, Restore) and a Settings screen (subscription, Restore, Manage subscription, Terms, Privacy, Legal/Attribution) reachable from home; P-STORE-01 source half
state: claimed
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T00:42:18Z
lease_expires_at: 2026-10-06T12:42:18Z
worktree: .worktrees/T-0271
branch: task/T-0271
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
- 2026-10-06T00:42:18Z claimed by agent/claude-opus-5; lease until 2026-10-06T12:42:18Z
- 2026-10-06T00:56:51Z RULINGS, before any code (author rule). agent/claude-opus-5.
  - R1 P-STORE-01 IS NOT IN pins/PINS.yaml. The Brief says "registered"; `grep -n STORE pins/PINS.yaml` prints
    nothing. Ruled: this task ADDS the P-STORE-01 entry (anchor: source, runs_on: [linux]) carrying the source half;
    its statement names the XCUITest half as T-0180's, not a `pending:` key (a pending pin's assertion is skipped by
    ops/lib/pins.py - P-ATTR-01's precedent).
  - R2 THE FROZEN RENDER BLOCKS. ops/lib/check-safety-disclaimer-frozen (sourced by P-SAFE-03 and P-ATTR-01) freezes
    ScenicHomeScreen's body, `chips`, `sheetDetails`, `conditions`, the line above the body (`public init() {}`)
    and the app shell's `struct ScenicDriveApp`, and refuses any `#` directive in those three files; -sheet's (s2)
    freezes `sheetSummary`. The acceptance REQUIRES a home settings action and a shell that presents Settings, so
    two frozen lists change deliberately, in the same commit as the code, where a reviewer reads them: the shell
    block (it gains `onSettings:` and one `.sheet` - a user-opened modal like the disclaimer's own, not an overlay
    on the sheet or the credit) and `chips` (the gear joins the drive picker inside the SAME material band, so
    chipBandBottom - the map's covered edge - is still measured on the band). The ABOVE anchor of the body moves
    from `public init() {}` to the new one-line init. sheetSummary, sheetDetails, conditions and the body are NOT
    edited. No `#if DEBUG` in the shell (the directive fence): the DEBUG-only launch argument is read inside
    Entitlements (`LaunchScreen.atLaunch`), whose files are not frozen.
  - R3 THE SUBSCRIPTION GROUP ID. App Store Connect ASSIGNS a group id (a number) when the group is created; no group
    exists (owner-only, M6 listing). Ruled: `StoreConstants.subscriptionGroupID = "PLANNED-asc-group-id"`, a typed
    constant whose value says it is a placeholder; StoreKit finds no products for it, which is exactly the CI state
    the Brief accepts (the paywall's own unavailable state). The plan's $29.99/yr and 7-day trial are App Store
    Connect data and appear nowhere in code.
  - R4 TERMS AND PRIVACY URLS. docs/store/terms.md and privacy.md say "hosted later on the owner's domain"; no domain
    exists in the tree. Ruled: the constants point at the files' GitHub pages on main of this PUBLIC repo -
    https://github.com/phineasfritsch/scenic_drive/blob/main/docs/store/terms.md and .../privacy.md - which resolve
    today, marked PLANNED in the declaration's doc comment (moves to the owner's domain before submission). Not
    Apple's standard EULA: the tree already carries its own Terms draft.
  - R5 MANAGE SUBSCRIPTION. The acceptance names `showManageSubscriptions`; `AppStore.showManageSubscriptions(in:)`
    needs a UIWindowScene, i.e. UIKit, and the target is "StoreKit + SwiftUI + DesignSystem only". Ruled: SwiftUI's
    `.manageSubscriptionsSheet(isPresented:)`, StoreKit's SwiftUI spelling of the same system sheet. Restore is
    `AppStore.sync()` verbatim.
  - R6 LINKS ON THE PAYWALL. StoreKit's own `.subscriptionStorePolicyDestination` links are drawn by the store view
    and carry no identifier we can set, and are not drawn while products are unavailable (CI). Ruled: our own
    `Link` rows for Terms of Use and Privacy Policy in a `.safeAreaInset(edge: .bottom)` of the store view, each
    with an accessibility identifier, visible whether or not products load - what the shot has to show.
  - R7 LEGAL/ATTRIBUTION TEXT. "The ODbL notice text from NOTICE/LICENSE-DATA": there is no NOTICE file; LICENSE-DATA
    is the source. The in-app notice is LICENSE-DATA's `## OpenStreetMap — ODbL 1.0` section, line for line, and
    the guard compares the two (so an edit to either is refused until both move). The Protomaps line is NOT copied:
    it contains the plan's credit string, which P-ATTR-01 limb (b) allows exactly once over apps/ios.
  - R8 THE GUARD. ops/lib/check-store-links.py (logic) + ops/lib/store_links_pinned.py (data, the cap): a whole-line
    WHITELIST keyed on identifiers over every *.swift under apps/ios, // -leading lines dropped and nothing else -
    every line naming `SubscriptionStoreView`, `restorePurchases`, `subscriptionStoreControlStyle`,
    `termsOfUseURL`, `privacyPolicyURL`, `subscriptionGroupID`, `AppStore.sync()`, `manageSubscriptionsSheet`,
    `onSettings`, `import Entitlements`, `PaywallScreen(`, `SettingsScreen(`, `LegalAttributionScreen(` is one of
    the approved (file, whole line) pairs with multiplicity, plus every `accessibilityIdentifier` and `import` line
    under Sources/Entitlements. --prove-red runs the named mutants on a temp copy (link removed, restore hidden,
    paywall without SubscriptionStoreView, and more), each refused by name; Linux-only, so no mutant branches.
  - R9 SCREENSHOTS. ios-screenshot's capture loop gains `settings` and `paywall` shots per appearance, launched with
    `-screen settings|paywall` (read under `#if DEBUG` in Entitlements; a release build ignores it), and every home
    shot passes `-screen home`. ios_screenshot_pinned.py's CAPTURE_RUN and its LAUNCH/ALIVE anchors move with it,
    plus one mutant: the `-screen` argument dropped.
- 2026-10-06T03:01:08Z BUILD, agent/claude-opus-5.
  - GUARD RED FIRST (2026-10-06T01:04:01Z), with the five Entitlements files written and the home and shell NOT yet
    changed: `python ops/lib/check-store-links.py` -> `P-STORE-01 (ops/lib/check-store-links.py): 11 refusal(s)`,
    exit 1, each by needle, e.g. `onSettings: the approved line is missing from .../ScenicHomeScreen.swift:
    \`public init(onSettings: @escaping () -> Void) { self.onSettings = onSettings }\``, `import Entitlements: the
    approved line is missing from apps/ios/ScenicDrive/ScenicDriveApp.swift`, `settingsButton: ...`,
    `"home.settings": ...`, `SettingsScreen(: ...`, `LaunchScreen.atLaunch: ...`. Then GREEN after the home and
    shell: `P-STORE-01 source half: paywall and Settings links, Restore, SubscriptionStoreView and the ODbL notice at
    exactly their approved sites`, exit 0.
  - --prove-red: `check-store-links --prove-red: 24/24 rows as required (21 mutants refused by name, 3 legitimate
    edits green)`, exit 0. The acceptance's three named mutants, each RED by name: `the paywall's Terms of Use link
    removed <- termsOfUseURL: the approved line is missing from .../PaywallScreen.swift`, `restore hidden on the
    paywall <- restorePurchases: ...`, `the paywall without SubscriptionStoreView <- SubscriptionStoreView: ...`;
    plus Privacy removed (both screens), Terms removed from Settings, restore dropped, restore moved onto the links
    (`the paywall's modifier chain: ... occurs 0 time(s)`), AppStore.sync() replaced, Manage removed, Settings not
    opening the paywall, an identifier removed, the Terms URL retargeted, a literal URL on the paywall, a feature
    target importing Entitlements, Entitlements importing UIKit, `#if true` for the -screen read, the ODbL notice
    edited, the shell dropping onSettings, the gear unmounted, a second paywall file. Linux-only, so run locally
    (no mutant branches, per the dispatch).
  - ios-screenshot guard: `IOS-COMPILE-GUARDRAILS OK` for both workflows; `PROVE-RED OK: 68 mutations red, 6
    legitimate spellings green over 2 workflows, 0 unexpected result(s)` (two new rows: `-screen` dropped, the
    settings/paywall shots dropped).
  - P-SAFE-03 / P-ATTR-01 moved deliberately (ruling R2): the frozen shell and chips lists and the body's ABOVE
    anchor (-frozen); ScenicHomeScreen.swift's approved sha256 typed in (-pinned, now f4d6aeb2...dcb6c); and
    check-map-attribution-sheet's (h4) presentation whitelist gains the shell's ONE whole line
    `.sheet(isPresented: $isShowingSettings) {` (first run refused it: `.sheet( at .../ScenicHomeScreen.swift(1)
    ScenicDrive/ScenicDriveApp.swift(1), tracked .../ScenicHomeScreen.swift(1)` - Settings is a user-opened modal,
    not a drive card; its content is the frozen shell block). `bash ops/lib/check-safety-disclaimer` exit 0 (32 min
    wall on this loaded box). check-pbxproj-graph: `28 assertions, 0 failed`.
  - ios-compile run 37400712681 on 4b178ae: success, first try. ios-screenshot run 37402525626 on 4b178ae: success;
    iOS 26.2, iPhone 17, `** BUILD SUCCEEDED **`, ten `Wrote screenshot to:` lines (home x3, settings, paywall, per
    appearance). LOOKED AT: settings-light - cream `bg`, large "Settings", Done at top right; Subscription section on
    white `surface`: Status "Not subscribed", Scenic Drive Pro, Restore Purchases, Manage Subscription; About:
    Terms of Use, Privacy Policy, Legal & Attribution with a chevron; orange SF Symbols, row text dark `fg`, never
    orange. settings-dark - the same on navy with `surface` cards. paywall-light/dark - pushed from Settings (back
    chevron, title "Scenic Drive Pro"), StoreKit's own "Subscription Unavailable / The subscription is unavailable
    in the current storefront." (the placeholder group id, ruling R3), and our bottom band "Terms of Use  Privacy
    Policy". In that run StoreKit also drew its own close X and painted its ground white / system grey under a
    `bg` band; 9e8397e hid the X (`.storeButton(.hidden, for: .cancellation)`) and set
    `.containerBackground(DesignTokens.bg, for: .subscriptionStore)`. ios-screenshot run 37405158016 on 9e8397e:
    success; the X is gone; the unavailable placeholder STILL draws on white - containerBackground does not reach
    StoreKit's unavailable state. Left as is and recorded: it only shows when there are no products.
    home-light-collapsed - the gear sits as a fourth 44 pt square at the trailing end of the chip band, inside the
    same material; "Westwood loop" now wraps to two lines; route, credit pill, sheet and conditions line unchanged.
  - NOT SEEN, said plainly: the paywall's Restore button. `.storeButton(.visible, for: .restorePurchases)` is in the
    source and pinned, but StoreKit draws no buttons in its unavailable state, so no screenshot shows it; Settings'
    Restore row is on screen. The marketing header (symbol, name, tagline) is not drawn for the same reason. Legal
    & Attribution was not screenshotted (no launch argument reaches it).
