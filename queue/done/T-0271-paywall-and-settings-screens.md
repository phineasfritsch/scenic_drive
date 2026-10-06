---
id: T-0271
title: Entitlements target - the paywall (SubscriptionStoreView with Terms of Use + Privacy links, Restore) and a Settings screen (subscription, Restore, Manage subscription, Terms, Privacy, Legal/Attribution) reachable from home; P-STORE-01 source half
state: done
owner: agent/claude-opus-5
owner_session: null
claimed_at: 2026-10-06T00:42:18Z
lease_expires_at: 2026-10-06T12:42:18Z
worktree: .worktrees/T-0271
branch: task/T-0271
exclusive: [package-swift]
touches: [apps/ios/Packages/ScenicApp/Package.swift, apps/ios/Packages/ScenicApp/Sources/Entitlements/, apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/, apps/ios/Packages/ScenicApp/Sources/DesignSystem/, apps/ios/ScenicDrive/, .github/workflows/ios-screenshot.yml, ops/lib/, pins/PINS.yaml]
pins_affected: [P-STORE-01, P-ATTR-02]
reviewer: agent/rv1-t0271
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
- 2026-10-06T04:01:14Z PRE-REVIEW SURVIVORS CLOSED, agent/claude-opus-5. The fable pass on b48f239 applied six
  unwritten mutants to PaywallScreen/SettingsScreen; five survived (`check-store-links.py` green, exit 0). RULINGS,
  before code: (S1) M1 (the inset draws `EmptyView()`, `policyLinks` left as dead code) and M5 (`about` ->
  `EmptyView()` in Settings' List) are one class - the links' sites were approved, their MOUNTING was not, while
  Restore's was; closed by runs, not needles: the paywall's chain run now continues `.safeAreaInset(edge: .bottom) {`
  / `policyLinks` / `}`, and two new runs `List { / subscription / about / }` (Settings' sections) and the shell's
  `.sheet(isPresented: $isShowingSettings) { / SETTINGS_MOUNT / }` (the same class at the shell's mount: a
  `.hidden()` under SettingsScreen(...) was green too). Runs now compare NON-BLANK kept lines, so the existing
  "blank line between the Settings sections" row stays green. (S2) M2 (`/* */` around the Terms link), M3
  (`.environment(\.openURL, OpenURLAction { _ in .handled })`) and M4 (`.opacity(0)`) are one class - a change that
  leaves every approved line verbatim but hides or disarms a control. The fix shape proposed (empty-approved-list
  needles for `openURL`, `.opacity(`, `.hidden()`, `/*`) is a blacklist of spellings (CLAUDE.md, PR #101):
  `.allowsHitTesting(false)` on a closing brace, `.disabled(true)`, `.scaleEffect(0)`, `.offset(...)` or a
  `extension View` in a sixth file would each be the next round. Ruled instead: Sources/Entitlements is FROZEN - a
  whitelist of content: the *.swift files there are exactly the five approved, and each file's non-blank kept lines
  (CR stripped, trimmed, `//`-leading dropped, which takes `///` with it) hash to an approved sha256 in
  store_links_pinned.FROZEN. Any code change there is refused until a reviewed commit re-approves the digest (the
  P-SAFE-03 ScenicHomeScreen digest is the precedent). Re-indents, blank lines and comment edits stay green. (S3) No
  Swift changed, so no ios-compile dispatch; the PNGs of runs 37400712681/37405158016 stand. Pin text updated:
  29 mutants, 4 legitimate edits, CANNOT SEE now names only a modifier or extension OUTSIDE Sources/Entitlements.
  - RED, with the new MUTATIONS rows in and the guard unchanged: `check-store-links --prove-red: 25/33 rows as
    required (29 mutants refused by name, 4 legitimate edits green)`, exit 1 - MISSED by name: `M1 the paywall's
    links unmounted (inset draws EmptyView)`, `M5 Settings' About section unmounted`, `M2 the Terms link inside a
    /* */ comment`, `M3 the links' taps open nothing (openURL replaced)`, `M4 the paywall drawn at opacity 0`, `the
    links made inert by a modifier on the HStack's closing brace`, `a view extension added to the module beside the
    screens` (refused only as `import :`, not by its name), `the shell hides the Settings it mounts`.
  - GREEN after the runs and FROZEN: shipped tree `P-STORE-01 source half: ... at exactly their approved sites,
    mounted, in a frozen Entitlements module`, exit 0; `check-store-links --prove-red: 33/33 rows as required (29
    mutants refused by name, 4 legitimate edits green)`, exit 0. M1 <- `the paywall's modifier chain: the run ...
    occurs 0 time(s)`; M5 <- `Settings' sections: the run `List { / subscription / about / }` occurs 0 time(s)`;
    M2, M3, M4 and the closing-brace row <- `the frozen Entitlements source: .../PaywallScreen.swift's non-blank kept
    lines hash ..., approved e78e2079...`; the sixth file <- `the frozen Entitlements source: .../ViewTweaks.swift is
    not an approved file`; the shell row <- `the shell's Settings sheet: the run ... occurs 0 time(s)`. Every earlier
    row still RED by its own name; the four GREEN rows green (the new one: a `///` doc comment reworded).
  - Measured: ops/lib/check-store-links.py 191 lines, ops/lib/store_links_pinned.py 179 lines (cap 300).
    pins/PINS.yaml parses with ops/lib/pins.py's loader (40 pins, P-STORE-01 present).
- 2026-10-06T04:36:04Z REVIEW PASS, agent/rv1-t0271 (reviewer, not the owner), PR #162 head 1db5798.
  - Gates run bare on a detached worktree of origin/task/T-0271: `python ops/lib/check-store-links.py` -> `P-STORE-01
    source half: ... at exactly their approved sites, mounted, in a frozen Entitlements module`, exit 0; `--prove-red`
    -> `33/33 rows as required (29 mutants refused by name, 4 legitimate edits green)`, exit 0;
    check-ios-compile-guardrails.py -> `IOS-COMPILE-GUARDRAILS OK` for ios-compile.yml and ios-screenshot.yml, exit 0,
    and `--prove-red` -> `PROVE-RED OK: 68 mutations red, 6 legitimate spellings green over 2 workflows, 0 unexpected
    result(s)`; `bash ops/lib/check-line-cap` -> `P-SRC-02: 229 Swift files tracked (Sources=106, Tests=90,
    apps/ios=33), none over 300 lines`, exit 0; `bash ops/queue-check` -> `QUEUE OK (265 tasks)`; `gh pr checks 162`
    -> core pass, pins-source-only pass; `git merge-base --is-ancestor origin/main origin/task/T-0271` exit 0.
  - Acceptance 1: no project.pbxproj in the diff (0 paths); Entitlements is a target of the FeatureScenicHome PRODUCT
    only, depends on DesignSystem only, imports DesignSystem, StoreKit, SwiftUI; FeatureScenicHome imports no
    Entitlements (home takes `onSettings`, the shell composes `.sheet` -> SettingsScreen -> PaywallScreen). No feature
    target imports another (FeatureScenicHome: DesignSystem Foundation Handoff MapAdapter OSLog ScenicKit SwiftUI
    UIKit, as on main). Acceptance 2: SubscriptionStoreView(groupID: StoreConstants.subscriptionGroupID) with
    .subscriptionStoreControlStyle(.picker), .storeButton(.visible, for: .restorePurchases), Terms + Privacy `Link`s
    in the bottom inset; Settings has status, Restore (`try await AppStore.sync()`), Manage
    (`.manageSubscriptionsSheet`, ruling R5), Terms, Privacy, Legal & Attribution; every control carries an id.
  - Screenshots LOOKED AT myself (ios-screenshot run 37405158016 on 9e8397e; Swift/workflows unchanged since, only a
    corpus .sqlite arrived with the main merge; ios-compile 37409405941 green on b48f239). settings-light/-dark:
    Status "Not subscribed", Scenic Drive Pro, Restore Purchases, Manage Subscription; About: Terms of Use, Privacy
    Policy, Legal & Attribution (chevron); orange icons, fg text, cream/navy grounds. paywall-light/-dark: back chevron,
    "Scenic Drive Pro", StoreKit's "Subscription Unavailable" (placeholder group id, R3), bottom band "Terms of Use
    Privacy Policy" visible in both themes. Restore is NOT drawn on the paywall (StoreKit's unavailable state) - as the
    Log declares; Restore is on screen in Settings. Cosmetic, declared: the unavailable placeholder draws on white /
    system dark grey above the `bg` band. home-light-collapsed / home-dark-fastest: gear as a fourth chip in the same
    band; the credit pill "(c) MapLibre - Natural Earth - (c) OpenStreetMap contributors" still drawn above the sheet.
  - Reviewer's own mutant (not in the author's or the pre-review lists): `.allowsHitTesting(false)` appended after
    `.accessibilityIdentifier("home.settings")` in ScenicHomeScreen.swift (the gear made inert, every pinned line
    verbatim). check-store-links.py stays green (home is outside its FROZEN set), but P-SAFE-03's -pinned refuses it
    by name: `the pinned render surface changed: ScenicHomeScreen.swift content changed (sha256 722552f9..., approved
    f4d6aeb2...)`, exit 1; restored -> `GREEN pinned files=14`, exit 0. Caught, not blocking.
  - Non-blocking, recorded: the frozen Entitlements digests mean every later Settings edit re-approves a sha256; the
    FROZEN missing-file branch has no --prove-red row of its own; the XCUITest half stays T-0180's.
