import Foundation
import ScenicKit

/// One row of the Worker's /search answer (T-0359 R6): the label Photon's address parts make and where it is. The
/// coordinate came FROM the server; it is never sent back. T-0362 R1: `place` is the id the Worker remembered this row
/// under - a negative Int64, the namespace corpus ids never use - and the ONLY thing /plan is sent for it; nil when the
/// Worker issued none, and then the row cannot be planned to.
public struct SearchResult: Equatable, Sendable {
    public let label: String
    public let coordinate: Coordinate
    public let place: Int64?

    public init(label: String, coordinate: Coordinate, place: Int64?) {
        self.label = label
        self.coordinate = coordinate
        self.place = place
    }
}
