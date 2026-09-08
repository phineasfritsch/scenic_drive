import Foundation

/// One stretch of route with a length and a scenic score.
///
/// This is what a GraphHopper path detail becomes: the router reports `scenic_score` over intervals of the
/// path, and each interval has a length in metres. Nothing here knows about OSM ways, because the router is
/// free to split, merge and reverse them and the score of a route must not depend on how it did that.
public struct ScoredEdge: Equatable, Sendable {
    /// Metres. Must be positive - a zero-length edge carries no weight and is a sign the caller is passing
    /// path detail boundaries rather than intervals.
    public let length: Double

    /// The scenic score of this stretch, in `0...1`.
    ///
    /// The ETL writes `scenic_score` as `0...10` onto the way for the router's encoded value, because
    /// GraphHopper encoded values are integers. It is normalised back to `0...1` before it reaches here, so
    /// that this file and `score.py` are talking about the same number and the gate-parity fixture can put
    /// one set of inputs through both.
    public let score: Double

    public init(length: Double, score: Double) {
        self.length = length
        self.score = score
    }

    var isValid: Bool {
        length.isFinite && length > 0 && score.isFinite && score >= 0 && score <= 1
    }
}
