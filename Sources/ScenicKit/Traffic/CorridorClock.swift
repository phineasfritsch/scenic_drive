import Foundation

/// A drive's completed corridor edges, timed and taught to the learner on the device (T-0325 R3, P-PRIV-05).
///
/// The caller hands it the shipped DriveSession after each observe, with the fix's wall-clock date. An edge is
/// taught only when it was driven end to end on the line: entered from the edge before it (or, for the first edge,
/// at the drive's first on-line observation in it) with the observation before on the line too, every observation
/// inside it on the line, and left into the next edge (or, for the last edge, arrived: the destination within
/// DriveSession.awayThresholdMeters along the line). Actual seconds run from that entry to that exit; the hour of
/// the week is the entry's. A skipped edge, an off-line observation and anything after a reroute (the session's
/// line is no longer the route's) teach nothing - a ratio from a partial or detoured edge would be a lie.
public struct CorridorClock: Sendable, Equatable {
    public let route: CorridorRoute
    /// The edge the latest on-line observation was in; nil before the first.
    private var edge: Int?
    /// When `edge` was entered cleanly; nil when its entry was not seen or the drive left the line inside it.
    private var enteredAt: Date?
    /// Whether the previous observation was on the line.
    private var previousOnLine = false
    /// Arrived, or the line was replaced: nothing more is taught this drive.
    private var finished = false

    public init(route: CorridorRoute) {
        self.route = route
    }

    /// One observation of the session at `date`. Returns how many edges it taught `speeds`.
    @discardableResult
    public mutating func observe(_ session: DriveSession, at date: Date,
                                 into speeds: inout LearnedCorridorSpeeds) -> Int {
        guard !finished else { return 0 }
        guard session.line.coordinates == route.coordinates else {
            finished = true
            return 0
        }
        guard let end = session.legEnd else {
            enteredAt = nil
            previousOnLine = false
            return 0
        }
        let now = route.edge(containingSegment: session.progressSegment)
        var taught = 0
        if let current = edge {
            if now != current {
                let clean = previousOnLine && now == current + 1
                if clean, let since = enteredAt, teach(current, from: since, to: date, into: &speeds) { taught += 1 }
                enteredAt = clean ? date : nil
                edge = now
            }
        } else {
            edge = now
            enteredAt = now == 0 ? date : nil
        }
        previousOnLine = true
        let arrived = end.vertex == route.coordinates.count - 1 && end.meters <= DriveSession.awayThresholdMeters
        if arrived, now == route.edges.count - 1 {
            if let since = enteredAt, teach(now, from: since, to: date, into: &speeds) { taught += 1 }
            finished = true
        }
        return taught
    }

    private func teach(_ index: Int, from start: Date, to stop: Date, into speeds: inout LearnedCorridorSpeeds) -> Bool {
        let edge = route.edges[index]
        return speeds.record(cell: edge.cell, hourOfWeek: HourOfWeek.of(start, in: speeds.timeZone),
                             actualSeconds: stop.timeIntervalSince(start), freeFlowSeconds: edge.freeFlowSeconds)
    }
}
