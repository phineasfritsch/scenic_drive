"""P-STORE-01's approved sites and its --prove-red table (T-0271). DATA, no rules: check-store-links.py reads it.

Every entry is (file relative to the repo root, the WHOLE line, trimmed). A file's kept lines are its lines with a
trailing CR stripped and whitespace trimmed; only a line whose trimmed text STARTS with // is dropped. For each
needle, the multiset of (file, kept line) over every line containing the needle must EQUAL the approved multiset:
a missing site, an extra site, a moved site and an edited line are each refused, naming the needle.
"""
ENT = "apps/ios/Packages/ScenicApp/Sources/Entitlements"
PW = f"{ENT}/PaywallScreen.swift"
ST = f"{ENT}/SettingsScreen.swift"
SC = f"{ENT}/StoreConstants.swift"
LG = f"{ENT}/LegalAttributionScreen.swift"
LS = f"{ENT}/LaunchScreen.swift"
CD = f"{ENT}/CorpusDownloadSheet.swift"
HOME = "apps/ios/Packages/ScenicApp/Sources/FeatureScenicHome/ScenicHomeScreen.swift"
SHELL = "apps/ios/ScenicDrive/ScenicDriveApp.swift"

STORE_VIEW = "SubscriptionStoreView(groupID: StoreConstants.subscriptionGroupID) {"
RESTORE = ".storeButton(.visible, for: .restorePurchases)"
TERMS_DECL = 'public static let termsOfUseURL = URL(string: "https://github.com/phineasfritsch/scenic_drive/blob/main/docs/store/terms.md")!'
PRIVACY_DECL = 'public static let privacyPolicyURL = URL(string: "https://github.com/phineasfritsch/scenic_drive/blob/main/docs/store/privacy.md")!'
SETTINGS_MOUNT = ("SettingsScreen(opensPaywall: LaunchScreen.atLaunch == .paywall, vehicle: VehicleSetting.name, "
                  "onDone: { isShowingSettings = false })")
DEBUG_READ = "return UserDefaults.standard.string(forKey: launchArgumentKey).flatMap(LaunchScreen.init(rawValue:)) ?? .home"

# Over every *.swift under apps/ios.
APP_WIDE = {
    "SubscriptionStoreView": [(PW, STORE_VIEW)],
    "restorePurchases": [(PW, RESTORE)],
    "subscriptionStoreControlStyle": [(PW, ".subscriptionStoreControlStyle(.picker)")],
    "subscriptionGroupID": [
        (SC, 'public static let subscriptionGroupID = "PLANNED-asc-group-id"'),
        (PW, STORE_VIEW),
        (ST, ".subscriptionStatusTask(for: StoreConstants.subscriptionGroupID) { state in"),
    ],
    "termsOfUseURL": [
        (SC, TERMS_DECL),
        (PW, 'Link("Terms of Use", destination: StoreConstants.termsOfUseURL)'),
        (ST, "Link(destination: StoreConstants.termsOfUseURL) {"),
    ],
    "privacyPolicyURL": [
        (SC, PRIVACY_DECL),
        (PW, 'Link("Privacy Policy", destination: StoreConstants.privacyPolicyURL)'),
        (ST, "Link(destination: StoreConstants.privacyPolicyURL) {"),
    ],
    "AppStore.sync()": [(ST, "try await AppStore.sync()")],
    "manageSubscriptionsSheet": [(ST, ".manageSubscriptionsSheet(isPresented: $isShowingManage)")],
    "PaywallScreen(": [(ST, "PaywallScreen()")],
    "LegalAttributionScreen(": [(ST, "LegalAttributionScreen()"), (ST, "LegalAttributionScreen()")],
    "SettingsScreen(": [(SHELL, SETTINGS_MOUNT)],
    "LaunchScreen.atLaunch": [
        (SHELL, "@State private var isShowingSettings = LaunchScreen.atLaunch != .home"),
        (ST, "@State private var isShowingLegal = LaunchScreen.atLaunch == .legal"),
        (SHELL, SETTINGS_MOUNT),
        (SHELL, "_isShowingCorpusDownload = State(initialValue: LaunchScreen.atLaunch == .home && corpus.offersDownload "
                "&& VehicleSetting.isChosen)"),
    ],
    "import Entitlements": [(SHELL, "import Entitlements")],
    "onSettings": [
        (HOME, "private let onSettings: () -> Void"),
        (HOME, "public init(onSettings: @escaping () -> Void, surprise: @escaping SurpriseSlot.Builder) { self.onSettings = onSettings; self.surprise = surprise }"),
        (HOME, "Button(action: onSettings) {"),
        (SHELL, "ScenicHomeScreen(onSettings: { isShowingSettings = true }, surprise: { open, failure in AnyView(SurpriseCard(failure: failure, onOpenInMaps: open)) })"),
    ],
    "settingsButton": [(HOME, "settingsButton"), (HOME, "private var settingsButton: some View {")],
    '"home.settings"': [(HOME, '.accessibilityIdentifier("home.settings")')],
}

# Over every *.swift under Sources/Entitlements only.
ENTITLEMENTS = {
    "import ": [(f, "import " + m) for f, mods in ((PW, "DesignSystem StoreKit SwiftUI"), (ST, "DesignSystem StoreKit SwiftUI"),
                                                   (LG, "DesignSystem SwiftUI"), (SC, "SwiftUI"), (LS, "SwiftUI"),
                                                   (CD, "DesignSystem SwiftUI"))
                for m in mods.split()],
    "accessibilityIdentifier": [(f, f'.accessibilityIdentifier("{i}")') for f, ids in (
        (PW, "paywall.store paywall.terms paywall.privacy"),
        (ST, "settings.done settings.status settings.paywall settings.restore settings.restoreNote settings.manage "
             "settings.terms settings.privacy settings.legal settings.corpusWifiOnly settings.vehicle"),
        (CD, "corpus.status corpus.progress corpus.download corpus.later"),
        (LG, "legal.odbl legal.copyright")) for i in ids.split()],
    "#": [(LS, "#if DEBUG"), (LS, "#else"), (LS, "#endif")],
    "UserDefaults": [(LS, DEBUG_READ)],
}

# Runs of consecutive NON-BLANK kept lines that must occur exactly once in their file: the modifiers sit ON the store
# view and the inset MOUNTS the links, Settings' List mounts both sections, the shell's sheet holds Settings bare, and
# the launch argument is read only inside `#if DEBUG`.
SEQUENCES = [
    ("the paywall's modifier chain", PW, [STORE_VIEW, "marketing", "}", ".subscriptionStoreControlStyle(.picker)", RESTORE,
                                          ".safeAreaInset(edge: .bottom) {", "policyLinks", "}"]),
    ("Settings' sections", ST, ["List {", "subscription", "Section {", 'LabeledContent("Vehicle", value: vehicle)',
                                ".frame(minHeight: 44)", '.accessibilityIdentifier("settings.vehicle")', "} header: {",
                                'Text("Vehicle")', "} footer: {",
                                'Text("Only a standard car for now. Other vehicles need road limits the map does not have yet.")',
                                "}", 'Section("Offline places") {',
                                'Toggle("Download on Wi-Fi only", isOn: $corpusWifiOnly)', ".frame(minHeight: 44)",
                                '.accessibilityIdentifier("settings.corpusWifiOnly")', "}", "about", "}"]),
    ("the shell's Settings sheet", SHELL, [".sheet(isPresented: $isShowingSettings) {", SETTINGS_MOUNT, "}"]),
    ("the DEBUG fence around -screen", LS, ["#if DEBUG", DEBUG_READ, "#else", "return .home", "#endif"]),
]

# The module frozen: the *.swift files under Sources/Entitlements are exactly these, and each file's non-blank kept
# lines, joined by LF, hash to this sha256. Any code change there - a modifier that hides or disarms a pinned control,
# a /* */ block, a view extension - is refused until a reviewed commit re-approves the digest.
FROZEN = {
    LS: "57f6af62de6787d5c129bee12dbf45bc6fefd70292806c3415b0376c8e075d71",
    LG: "b72965b1635d4d8b109a0f966e6cfe8fd1f1fe9d7bdf4bd9bac2148f081e30a6",
    PW: "333b33ed55630cb3ec5f0bf57c17b44bfdb334d1d33ea2b2d5057ab830579ba9",
    ST: "7727c2bfd3996030b9be0a69d611c92d35cffcf4aa5a071b1b50f51aa60e2b6d",
    SC: "6da6ddadc509df44f9a9dadec770e0c3a84738af14715eeb6cee9c221bf63706",
    CD: "7e63f62eb351c5b45c5bed74cf5a63beff43e9b697747c01973e40eefe060906",
}

# The in-app ODbL notice: LICENSE-DATA's section under this heading, one Swift string element per line, exactly.
NOTICE_HEADING = "## OpenStreetMap — ODbL 1.0"
NOTICE_FILE = LG
NOTICE_OPEN = "static let odblNotice: [String] = ["

# (name, file, exact text that must occur exactly once - or None to ADD the file, replacement, the reason's needle).
MUTATIONS = [
    ("the paywall's Terms of Use link removed", PW, 'Link("Terms of Use", destination: StoreConstants.termsOfUseURL)',
     'Text("Terms of Use")', "termsOfUseURL"),
    ("the paywall's Privacy Policy link removed", PW, 'Link("Privacy Policy", destination: StoreConstants.privacyPolicyURL)',
     'Text("Privacy Policy")', "privacyPolicyURL"),
    ("Settings' Terms of Use row removed", ST, "Link(destination: StoreConstants.termsOfUseURL) {", "Group {",
     "termsOfUseURL"),
    ("Settings' Privacy Policy row removed", ST, "Link(destination: StoreConstants.privacyPolicyURL) {", "Group {",
     "privacyPolicyURL"),
    ("restore hidden on the paywall", PW, RESTORE, ".storeButton(.hidden, for: .restorePurchases)", "restorePurchases"),
    ("restore dropped from the paywall", PW, "        " + RESTORE + "\n", "", "restorePurchases"),
    ("the paywall without SubscriptionStoreView", PW, STORE_VIEW, "VStack {", "SubscriptionStoreView"),
    ("restore moved off the store view (onto the links)", PW,
     "        " + RESTORE + "\n        .safeAreaInset(edge: .bottom) {\n            policyLinks\n",
     "        .safeAreaInset(edge: .bottom) {\n            policyLinks\n                " + RESTORE + "\n",
     "the paywall's modifier chain"),
    ("Settings' Restore no longer calls AppStore.sync()", ST, "try await AppStore.sync()",
     "try await Task.sleep(for: .seconds(1))", "AppStore.sync()"),
    ("Manage subscription removed", ST, ".manageSubscriptionsSheet(isPresented: $isShowingManage)",
     ".sheet(isPresented: $isShowingManage) { EmptyView() }", "manageSubscriptionsSheet"),
    ("Settings no longer opens the paywall", ST, "PaywallScreen()", "EmptyView()", "PaywallScreen("),
    ("the paywall's Terms identifier removed", PW, '.accessibilityIdentifier("paywall.terms")',
     '.accessibilityLabel("Terms of Use")', "accessibilityIdentifier"),
    ("the Terms URL pointed elsewhere", SC, 'docs/store/terms.md")!', 'docs/store/README.md")!', "termsOfUseURL"),
    ("a link typed as a literal URL on the paywall", PW, 'destination: StoreConstants.privacyPolicyURL)',
     'destination: URL(string: "https://example.com/privacy")!)', "privacyPolicyURL"),
    ("a feature target imports Entitlements", HOME, "import DesignSystem\n", "import DesignSystem\nimport Entitlements\n",
     "import Entitlements"),
    ("Entitlements imports UIKit", ST, "import SwiftUI\n", "import SwiftUI\nimport UIKit\n", "import "),
    ("the -screen read compiled into release", LS, "#if DEBUG\n", "#if true\n", "#"),
    ("the app's ODbL notice edited", LG, "are themselves offered under the ODbL", "are themselves offered under a licence",
     "ODbL notice"),
    ("the shell drops the home's settings action", SHELL,
     "ScenicHomeScreen(onSettings: { isShowingSettings = true }, surprise: { open, failure in AnyView(SurpriseCard(failure: failure, onOpenInMaps: open)) })",
     "ScenicHomeScreen(onSettings: {}, surprise: { open, failure in AnyView(SurpriseCard(failure: failure, onOpenInMaps: open)) })", "onSettings"),
    ("the settings button no longer mounted in the chip band", HOME, "            settingsButton\n", "", "settingsButton"),
    ("a second paywall surface with no links", f"{ENT}/QuickPaywall.swift", None,
     "import StoreKit\nimport SwiftUI\n\nstruct QuickPaywall: View {\n    var body: some View {\n"
     "        " + STORE_VIEW + "\n            EmptyView()\n        }\n    }\n}\n", "SubscriptionStoreView"),
    # Pre-review mutant pass (2026-10-06): each kept every approved line verbatim and was green before the rows below.
    ("M1 the paywall's links unmounted (inset draws EmptyView)", PW,
     ".safeAreaInset(edge: .bottom) {\n            policyLinks\n",
     ".safeAreaInset(edge: .bottom) {\n            EmptyView()\n", "the paywall's modifier chain"),
    ("M5 Settings' About section unmounted", ST, "                about\n", "                EmptyView()\n",
     "Settings' sections"),
    ("M2 the Terms link inside a /* */ comment", PW,
     'HStack(spacing: 24) {\n            Link("Terms of Use", destination: StoreConstants.termsOfUseURL)\n'
     '                .frame(minHeight: 44)\n                .accessibilityIdentifier("paywall.terms")\n',
     'HStack(spacing: 24) {\n            /*\n            Link("Terms of Use", destination: StoreConstants.termsOfUseURL)\n'
     '                .frame(minHeight: 44)\n                .accessibilityIdentifier("paywall.terms")\n            */\n',
     "the frozen Entitlements source"),
    ("M3 the links' taps open nothing (openURL replaced)", PW, "        .tint(DesignTokens.fg)\n        .frame(maxWidth",
     "        .tint(DesignTokens.fg)\n        .environment(\\.openURL, OpenURLAction { _ in .handled })\n        .frame(maxWidth",
     "the frozen Entitlements source"),
    ("M4 the paywall drawn at opacity 0", PW, '.accessibilityIdentifier("paywall.store")\n',
     '.accessibilityIdentifier("paywall.store")\n        .opacity(0)\n', "the frozen Entitlements source"),
    ("the links made inert by a modifier on the HStack's closing brace", PW, "        }\n        .font(.footnote)",
     "        }.allowsHitTesting(false)\n        .font(.footnote)", "the frozen Entitlements source"),
    ("a view extension added to the module beside the screens", f"{ENT}/ViewTweaks.swift", None,
     "import SwiftUI\n\nextension View {\n    func calm() -> some View { hidden() }\n}\n",
     "the frozen Entitlements source"),
    ("the shell hides the Settings it mounts", SHELL, SETTINGS_MOUNT + "\n",
     SETTINGS_MOUNT + "\n                        .hidden()\n", "the shell's Settings sheet"),
]

# Legitimate edits that must stay GREEN - a check that refuses them teaches people to stop running it.
STILL_GREEN = [
    ("a // comment naming SubscriptionStoreView", PW, "import StoreKit\n",
     "import StoreKit\n// SubscriptionStoreView(groupID: somewhereElse) {\n", None),
    ("the restore line re-indented", PW, "        " + RESTORE + "\n", "            " + RESTORE + "\n", None),
    ("a blank line between the Settings sections", ST, "                subscription\n", "                subscription\n\n",
     None),
    ("a /// doc comment reworded on the paywall", PW, "/// The header the store view draws above its plans",
     "/// The header StoreKit draws above the plans", None),
]
