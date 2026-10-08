import Foundation

/// One subscription transaction as `StoreKitAccountToken` reads it from StoreKit 2 (T-0315 R3): when it was
/// purchased and the appAccountToken the paywall attached, if any. `latest` picks the token the app sends.
public struct AccountTokenCandidate: Equatable, Sendable {
    public let purchased: Date
    public let token: UUID?

    public init(purchased: Date, token: UUID?) {
        self.purchased = purchased
        self.token = token
    }

    /// The token of the most recently purchased candidate that carries one - live, expired or revoked alike: the
    /// Worker answers the tier, the client never guesses it. Equal dates keep the greater token, so the answer does
    /// not depend on the order StoreKit lists them in. nil when no candidate carries a token.
    public static func latest(_ candidates: [AccountTokenCandidate]) -> UUID? {
        var best: AccountTokenCandidate?
        for candidate in candidates where candidate.token != nil {
            guard let held = best else { best = candidate; continue }
            if candidate.purchased > held.purchased { best = candidate; continue }
            if candidate.purchased == held.purchased, candidate.token!.uuidString > held.token!.uuidString {
                best = candidate
            }
        }
        return best?.token
    }
}
