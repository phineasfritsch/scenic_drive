import DesignSystem
import StoreKit
import SwiftUI

/// The paywall (plan M6, pin P-STORE-01): StoreKit's own `SubscriptionStoreView` for the one subscription group,
/// with Restore shown and a Terms of Use and a Privacy Policy link always on screen (App Review 3.1.2).
///
/// The store view draws the price, the trial and the subscribe button from App Store Connect; nothing about money
/// is typed here. The two links are OURS, in a bottom inset, not StoreKit's policy buttons (ruling R6): StoreKit
/// draws those only once products load and gives them no identifier, and the links must be on screen - and
/// findable by a UI test - whether or not the store answers.
///
/// Calm, in the DesignSystem tokens: `fg` and `fgMuted` text on `bg`, the scenic green on the one symbol, and no
/// `primary` text anywhere (DesignTokens' note). Text styles only, so every line grows with Dynamic Type.
public struct PaywallScreen: View {
    public init() {}

    public var body: some View {
        SubscriptionStoreView(groupID: StoreConstants.subscriptionGroupID) {
            marketing
        }
        .subscriptionStoreControlStyle(.picker)
        .storeButton(.visible, for: .restorePurchases)
        .safeAreaInset(edge: .bottom) {
            policyLinks
        }
        // The store view draws its own ground (white / system grey) and its own close button. The ground is `bg`,
        // so the store and the links band are one surface (the first screenshot run showed two); the close button
        // is hidden because the paywall is pushed inside Settings, whose back button already leaves it.
        .containerBackground(DesignTokens.bg, for: .subscriptionStore)
        .storeButton(.hidden, for: .cancellation)
        .navigationTitle("Scenic Drive Pro")
        .navigationBarTitleDisplayMode(.inline)
        .accessibilityIdentifier("paywall.store")
    }

    /// The header the store view draws above its plans: one symbol, the name, the promise.
    private var marketing: some View {
        VStack(spacing: 12) {
            Image(systemName: "mountain.2")
                .font(.largeTitle)
                .foregroundStyle(DesignTokens.scenic)
                .accessibilityHidden(true)
            Text("Scenic Drive Pro")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .accessibilityAddTraits(.isHeader)
            Text("Take the long way. Unwind.")
                .font(.body)
                .foregroundStyle(DesignTokens.fgMuted)
                .multilineTextAlignment(.center)
                .fixedSize(horizontal: false, vertical: true)
        }
        .padding(.top, 24)
        .padding(.horizontal, 16)
    }

    /// Terms of Use and Privacy Policy, each a 44 pt target, in `fg` on `bg`.
    private var policyLinks: some View {
        HStack(spacing: 24) {
            Link("Terms of Use", destination: StoreConstants.termsOfUseURL)
                .frame(minHeight: 44)
                .accessibilityIdentifier("paywall.terms")
            Link("Privacy Policy", destination: StoreConstants.privacyPolicyURL)
                .frame(minHeight: 44)
                .accessibilityIdentifier("paywall.privacy")
        }
        .font(.footnote)
        .tint(DesignTokens.fg)
        .frame(maxWidth: .infinity)
        .background(DesignTokens.bg)
    }
}
