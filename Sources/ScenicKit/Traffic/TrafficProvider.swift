import Foundation

/// What re-times a planned route's free-flow edges into the ETA the preview shows (plan, ETA honesty). Today the
/// only one is LearnedCorridorSpeeds, on the device; the paid flow source (V1.1) answers the same call.
public protocol TrafficProvider: Sendable {
    /// `edges` re-timed for a departure at `departsAt`; each edge reads the hour it is entered (T-0320 R6).
    func retime(_ edges: [CorridorEdge], departsAt: Date) -> RetimedRoute
}
