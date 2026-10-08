import Foundation
import ScenicKit

/// The Surprise card's ledger (T-0307 R6, T-0310 R7): GET /ledger's rows handed to the card as
/// `SurpriseLedgerPlace`s, and each shown place POSTed as {place_id, cell} where the cell is `cellOf` the PLACE's
/// own coordinate (P-PRIV-05) - production's `cellOf` is Telemetry H3Cell at resolution 5, wired by PlanAdapter. Any
/// read outcome but `.places` is nil; a place with no cell is not sent; a write's outcome changes nothing on the card.
public struct LedgerSurpriseSource: SurpriseLedgerSource {
    let client: LedgerClient
    let cellOf: @Sendable (Coordinate) -> String?

    public init(client: LedgerClient, cellOf: @escaping @Sendable (Coordinate) -> String?) {
        self.client = client
        self.cellOf = cellOf
    }

    public func ledgerPlaces() async -> [SurpriseLedgerPlace]? {
        guard case .places(let rows) = await client.read() else { return nil }
        return rows.map { SurpriseLedgerPlace(candidateId: $0.placeId, date: $0.day) }
    }

    public func recordShown(_ candidate: SurpriseCandidate) async {
        guard let cell = cellOf(candidate.coordinate) else { return }
        _ = await client.record(placeId: candidate.id, cell: cell)
    }
}
