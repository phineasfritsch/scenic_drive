/// A route's edges re-timed by a traffic provider, and whether the ETA they add up to is still an estimate - the
/// *estimate · no traffic data* badge (P-SAFE-07).
public struct RetimedRoute: Equatable, Sendable {
    /// One entry per edge, in the route's order.
    public let edgeSeconds: [Double]
    /// True unless every edge was re-timed from a learned ratio.
    public let isEstimate: Bool

    public init(edgeSeconds: [Double], isEstimate: Bool) {
        self.edgeSeconds = edgeSeconds
        self.isEstimate = isEstimate
    }

    /// The re-timed ETA: the edges' seconds, summed in order.
    public var etaSeconds: Double { edgeSeconds.reduce(0, +) }
}
