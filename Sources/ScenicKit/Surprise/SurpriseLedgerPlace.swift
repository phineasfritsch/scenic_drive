import Foundation

/// One place the server's Surprise ledger says this driver was shown, and the (UTC) day (T-0307 R5). The merge
/// takes its category and corridor from the deck's candidate of the same id; the ledger carries neither.
public struct SurpriseLedgerPlace: Sendable, Equatable {
    public let candidateId: String
    public let date: CivilDate

    public init(candidateId: String, date: CivilDate) {
        self.candidateId = candidateId
        self.date = date
    }
}
