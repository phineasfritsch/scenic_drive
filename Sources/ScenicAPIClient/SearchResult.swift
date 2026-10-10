import Foundation
import ScenicKit

/// One row of the Worker's /search answer (T-0359 R6): the label Photon's address parts make and where it is. The
/// coordinate came FROM the server; nothing here is ever sent back to it.
public struct SearchResult: Equatable, Sendable {
    public let label: String
    public let coordinate: Coordinate

    public init(label: String, coordinate: Coordinate) {
        self.label = label
        self.coordinate = coordinate
    }
}
