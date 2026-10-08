import Foundation
import ScenicAPIClient
import StoreKit

/// The purchase id plan, trip and loop requests carry as `x-scenic-account-token` (T-0315 R3): the appAccountToken
/// the paywall attached to this Apple ID's most recent subscription purchase, read from StoreKit 2's own verified
/// transactions - which StoreKit syncs to every device on the Apple ID and restores with AppStore.sync, so there is
/// no second copy to drift. Every transaction counts, live, expired or revoked: the Worker answers the tier from its
/// /asn rows and the client never guesses one. ScenicAPIClient `AccountTokenCandidate.latest` picks, Linux-tested.
/// Nothing here logs: the token is a bearer secret (T-0272 R5).
struct StoreKitAccountToken: AccountTokenProvider {
    func accountToken() async -> UUID? {
        var candidates: [AccountTokenCandidate] = []
        for await result in Transaction.all {
            guard case .verified(let transaction) = result, transaction.productType == .autoRenewable else { continue }
            candidates.append(AccountTokenCandidate(purchased: transaction.purchaseDate,
                                                    token: transaction.appAccountToken))
        }
        return AccountTokenCandidate.latest(candidates)
    }
}
