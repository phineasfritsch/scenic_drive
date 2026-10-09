import DesignSystem
import StoreKit
import SwiftUI

/// Settings (plan Screens): the subscription - its status, the paywall, Restore (`AppStore.sync()`) and the system's
/// manage-subscription sheet - then Terms of Use, Privacy Policy and Legal & Attribution. Vehicle, Sign in with
/// Apple, Delete account and the offline-data rows arrive with the features they control.
///
/// Presented by the app shell from the home's settings action; it never knows the home exists, and the home never
/// imports this target (CLAUDE.md: feature targets never import each other). `opensPaywall` is the DEBUG-only
/// `-screen paywall` launch, which opens Settings with the paywall already pushed - the same path a tap takes.
///
/// Every control carries an accessibility identifier (`settings.*`), every row is at least 44 pt, row text is `fg`
/// on `surface` and the only `primary` is on the SF Symbols beside it - an accent, never text (DesignTokens' note).
public struct SettingsScreen: View {
    private let onDone: () -> Void
    /// T-0309 R4: the vehicle onboarding stored, by name, handed in by the shell (this target has no ScenicKit).
    private let vehicle: String

    @State private var isShowingPaywall: Bool
    /// T-0336: a DEBUG `-screen legal` launch opens on Legal & Attribution; home in every release build.
    @State private var isShowingLegal = LaunchScreen.atLaunch == .legal
    @State private var isShowingManage = false
    @State private var isRestoring = false
    @State private var status = "Checking…"
    @State private var restoreNote: String?
    /// T-0305 R6: the places download uses Wi-Fi only unless this is off; absent = on. PlanAdapter's LiveCorpus reads
    /// the same key, handed to it by the shell as `SettingsScreen.corpusWifiOnlyKey`.
    @AppStorage(SettingsScreen.corpusWifiOnlyKey) private var corpusWifiOnly = true

    public static let corpusWifiOnlyKey = "corpus.wifi.only"

    public init(opensPaywall: Bool, vehicle: String, onDone: @escaping () -> Void) {
        self.onDone = onDone
        self.vehicle = vehicle
        _isShowingPaywall = State(initialValue: opensPaywall)
    }

    public var body: some View {
        NavigationStack {
            List {
                subscription
                Section {
                    LabeledContent("Vehicle", value: vehicle)
                        .frame(minHeight: 44)
                        .accessibilityIdentifier("settings.vehicle")
                } header: {
                    Text("Vehicle")
                } footer: {
                    Text("Only a standard car for now. Other vehicles need road limits the map does not have yet.")
                }
                Section("Offline places") {
                    Toggle("Download on Wi-Fi only", isOn: $corpusWifiOnly)
                        .frame(minHeight: 44)
                        .accessibilityIdentifier("settings.corpusWifiOnly")
                }
                about
            }
            .scrollContentBackground(.hidden)
            .background(DesignTokens.bg)
            .navigationTitle("Settings")
            .toolbar {
                ToolbarItem(placement: .confirmationAction) {
                    Button("Done", action: onDone)
                        .frame(minHeight: 44)
                        .accessibilityIdentifier("settings.done")
                }
            }
            .navigationDestination(isPresented: $isShowingPaywall) {
                PaywallScreen()
            }
            .navigationDestination(isPresented: $isShowingLegal) {
                LegalAttributionScreen()
            }
            .subscriptionStatusTask(for: StoreConstants.subscriptionGroupID) { state in
                let text = SettingsScreen.describe(state)
                await MainActor.run { status = text }
            }
            .manageSubscriptionsSheet(isPresented: $isShowingManage)
        }
        .tint(DesignTokens.fg)
    }

    /// Status, the paywall, Restore, Manage.
    private var subscription: some View {
        Section("Subscription") {
            LabeledContent("Status", value: status)
                .foregroundStyle(DesignTokens.fg)
                .frame(minHeight: 44)
                .accessibilityIdentifier("settings.status")
            Button {
                isShowingPaywall = true
            } label: {
                row("Scenic Drive Pro", symbol: "mountain.2")
            }
            .accessibilityIdentifier("settings.paywall")
            Button {
                Task { await restore() }
            } label: {
                row(isRestoring ? "Restoring…" : "Restore Purchases", symbol: "arrow.clockwise")
            }
            .disabled(isRestoring)
            .accessibilityIdentifier("settings.restore")
            if let restoreNote {
                Text(restoreNote)
                    .font(.footnote)
                    .foregroundStyle(DesignTokens.fgMuted)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("settings.restoreNote")
            }
            Button {
                isShowingManage = true
            } label: {
                row("Manage Subscription", symbol: "creditcard")
            }
            .accessibilityIdentifier("settings.manage")
        }
        .listRowBackground(DesignTokens.surface)
    }

    /// Terms, Privacy, Legal & Attribution.
    private var about: some View {
        Section("About") {
            Link(destination: StoreConstants.termsOfUseURL) {
                row("Terms of Use", symbol: "doc.text")
            }
            .accessibilityIdentifier("settings.terms")
            Link(destination: StoreConstants.privacyPolicyURL) {
                row("Privacy Policy", symbol: "hand.raised")
            }
            .accessibilityIdentifier("settings.privacy")
            NavigationLink {
                LegalAttributionScreen()
            } label: {
                row("Legal & Attribution", symbol: "map")
            }
            .accessibilityIdentifier("settings.legal")
        }
        .listRowBackground(DesignTokens.surface)
    }

    /// One row's label: an SF Symbol in the accent, the title in `fg`, at least 44 pt tall.
    private func row(_ title: String, symbol: String) -> some View {
        Label {
            Text(title)
                .foregroundStyle(DesignTokens.fg)
        } icon: {
            Image(systemName: symbol)
                .foregroundStyle(DesignTokens.primary)
        }
        .frame(minHeight: 44)
    }

    /// Restore: `AppStore.sync()`, which asks the user to sign in to the App Store if needed, then says what happened.
    private func restore() async {
        isRestoring = true
        defer { isRestoring = false }
        do {
            try await AppStore.sync()
            restoreNote = "Purchases restored."
        } catch {
            restoreNote = "Couldn't restore right now. Check your connection and try again."
        }
    }

    /// The status line for one answer from StoreKit. Nonisolated: StoreKit may call the task's action off the main
    /// actor, and the result is handed back to it.
    nonisolated private static func describe(_ state: EntitlementTaskState<[Product.SubscriptionInfo.Status]>) -> String {
        switch state {
        case .loading:
            return "Checking…"
        case .failure:
            return "Couldn't check right now"
        case .success(let statuses):
            let active = statuses.contains { $0.state == .subscribed || $0.state == .inGracePeriod }
            return active ? "Active" : "Not subscribed"
        @unknown default:
            return "Not subscribed"
        }
    }
}
