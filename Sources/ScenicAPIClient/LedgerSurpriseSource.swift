import Foundation
import ScenicKit

/// The Surprise card's ledger (T-0307 R6, T-0310 R7). STUB (RED).
public struct LedgerSurpriseSource: SurpriseLedgerSource {
    let client: LedgerClient
    let cellOf: @Sendable (Coordinate) -> String?

    public init(client: LedgerClient, cellOf: @escaping @Sendable (Coordinate) -> String?) {
        self.client = client
        self.cellOf = cellOf
    }

    public func ledgerPlaces() async -> [SurpriseLedgerPlace]? { nil }

    public func recordShown(_ candidate: SurpriseCandidate) async {}
}
