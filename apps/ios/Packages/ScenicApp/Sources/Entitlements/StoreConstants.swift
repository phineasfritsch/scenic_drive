import SwiftUI

/// The paywall's typed constants (T-0271, rulings R3 and R4). Every one of them is read by name by
/// ops/lib/check-store-links.py (P-STORE-01): a link typed as a literal at a call site is refused there.
///
/// The price - the plan's $29.99 a year with a 7-day trial - is App Store Connect data and is deliberately NOT
/// here: StoreKit reads it from the subscription group at run time, so a price change never ships as a build.
public enum StoreConstants {
    /// PLANNED. App Store Connect assigns a group id when the owner creates the subscription group (the M6 listing
    /// task, owner-only). Until then this placeholder matches no group, and the paywall shows StoreKit's own
    /// unavailable state - which is what every simulator run without a StoreKit configuration shows anyway.
    public static let subscriptionGroupID = "PLANNED-asc-group-id"

    /// PLANNED hosting: docs/store/terms.md on the main branch of this public repository, which resolves today. It
    /// moves to the owner's domain before submission, and the draft is a lawyer's to finish first (plan M0).
    public static let termsOfUseURL = URL(string: "https://github.com/phineasfritsch/scenic_drive/blob/main/docs/store/terms.md")!

    /// PLANNED hosting, exactly as `termsOfUseURL`: docs/store/privacy.md.
    public static let privacyPolicyURL = URL(string: "https://github.com/phineasfritsch/scenic_drive/blob/main/docs/store/privacy.md")!
}
