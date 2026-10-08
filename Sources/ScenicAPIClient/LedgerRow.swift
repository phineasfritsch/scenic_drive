import Foundation
import ScenicKit

/// One row of GET /ledger (T-0302 R5): a corpus place id, the H3 resolution-5 cell of the PLACE and the UTC day it
/// was shown. No coordinate and no instant finer than a day exists on the wire, so none exists here.
public struct LedgerRow: Equatable, Sendable {
    public let placeId: String
    public let cell: String
    public let day: CivilDate

    public init(placeId: String, cell: String, day: CivilDate) {
        self.placeId = placeId
        self.cell = cell
        self.day = day
    }
}
