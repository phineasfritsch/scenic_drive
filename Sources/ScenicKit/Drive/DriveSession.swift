import Foundation

/// The drive's decisions, as a pure state machine fed fixes and connectivity (T-0317, P-NAV-01, P-SAFE-09).
///
/// NavAdapter (the only Ferrostar importer) forwards each location update to `observe(_:)` and each reachability
/// change to `connectivity(online:)`, and sends whatever RerouteRequest comes back. Everything it decides is here,
/// so it can be tested on Linux:
///   * AWAY is a fix more than 50 m from the planned line; OFF-ROUTE is away continuously for at least 5 s (R3).
///   * Off-route online asks for the rest of THIS drive once - the pins not yet passed, the same lambda (R4) - and
///     asks nothing more until the reroute lands or fails. Off-route offline is rejoin mode with zero requests,
///     and the offline-to-online edge in rejoin mode asks exactly once (R5). Losing the connection while a
///     reroute is out is rejoin mode too: that reroute is lost with it.
///   * The surface is `.minimal` above 4.5 m/s or at an unknown speed, before the first fix, and after an
///     unusable fix (its speed is as unknown as its position) (R6).
public struct DriveSession: Sendable, Equatable {
    /// A fix further than this from the line is away; exactly this far is on it.
    public static let awayThresholdMeters: Double = 50
    /// Away for at least this long is off-route.
    public static let offRouteDwellSeconds: TimeInterval = 5

    public private(set) var mode: DriveMode = .guiding
    public private(set) var surface: DriveSurface = .minimal
    public private(set) var line: DriveLine
    public private(set) var waypoints: [Coordinate]
    /// The segment the driver was last seen on (DriveLine.progress); a pin at vertex v is passed iff this >= v.
    public private(set) var progressSegment = 0
    public private(set) var isOnline: Bool
    public let lambda: Double
    /// T-0328 R1: the token of the plan being driven - the preview's, then each taken reroute's; nil for none.
    public private(set) var planToken: String?
    private var pinVertices: [Int]
    private var awaySince: TimeInterval?
    private var latest: DriveFix?

    /// nil unless the line is real, every pin is one of its vertices in route order, and lambda is finite.
    public init?(line coordinates: [Coordinate], waypoints: [Coordinate], lambda: Double, online: Bool,
                 planToken: String? = nil) {
        guard lambda.isFinite, let line = DriveLine(coordinates),
              let vertices = line.vertexIndices(of: waypoints) else { return nil }
        self.line = line
        self.waypoints = waypoints
        self.pinVertices = vertices
        self.lambda = lambda
        self.isOnline = online
        self.planToken = planToken
    }

    /// One location fix. Returns the reroute to send, or nil. An unusable fix asks nothing and changes nothing but
    /// the surface, which goes minimal: unknown is moving.
    public mutating func observe(_ fix: DriveFix) -> RerouteRequest? {
        guard fix.isUsable else {
            surface = .minimal
            return nil
        }
        surface = DriveSurface(speedMetersPerSecond: fix.speedMetersPerSecond)
        latest = fix
        if line.distanceMeters(from: fix.coordinate) <= Self.awayThresholdMeters {
            awaySince = nil
            progressSegment = line.progress(from: progressSegment, at: fix.coordinate,
                                            within: Self.awayThresholdMeters)
            if mode == .rejoining { mode = .guiding }
            return nil
        }
        guard mode == .guiding else { return nil }
        let since = awaySince ?? fix.timestamp
        awaySince = since
        guard fix.timestamp - since >= Self.offRouteDwellSeconds else { return nil }
        guard isOnline else {
            mode = .rejoining
            return nil
        }
        mode = .rerouting
        return request(from: fix.coordinate)
    }

    /// A reachability change. The offline-to-online edge in rejoin mode is the one that asks; the online-to-offline
    /// edge while a reroute is out loses that reroute, which is rejoin mode.
    public mutating func connectivity(online: Bool) -> RerouteRequest? {
        let wasOnline = isOnline
        isOnline = online
        if !online, mode == .rerouting { mode = .rejoining }
        guard online, !wasOnline, mode == .rejoining, let latest else { return nil }
        mode = .rerouting
        return request(from: latest.coordinate)
    }

    /// The reroute landed: its line, pins and token (T-0328 R3) replace the plan's, the lambda stays. Ignored unless
    /// a reroute is out; a reply that is not a usable line with its pins on it is a failure (rejoin mode). True when
    /// taken.
    @discardableResult
    public mutating func rerouteArrived(line coordinates: [Coordinate], waypoints: [Coordinate],
                                        planToken: String? = nil) -> Bool {
        guard mode == .rerouting else { return false }
        guard let next = DriveLine(coordinates), let vertices = next.vertexIndices(of: waypoints) else {
            mode = .rejoining
            return false
        }
        line = next
        self.waypoints = waypoints
        pinVertices = vertices
        self.planToken = planToken
        progressSegment = 0
        awaySince = nil
        mode = .guiding
        return true
    }

    /// The reroute could not be had: rejoin mode, and no automatic retry.
    public mutating func rerouteFailed() {
        if mode == .rerouting { mode = .rejoining }
    }

    /// The current line cut at its pins: the steps NavAdapter hands Ferrostar (T-0321 R4).
    public var legs: [DriveLeg] { DriveLeg.split(line, at: pinVertices) }

    /// Where the current leg ends - the first pin vertex past the progress, else the last vertex - and the metres
    /// to it ALONG the line from the latest usable fix (T-0329 R2). nil before the first one, and while that fix is
    /// away from the current line (R8: a driver off the line is not on any leg).
    public var legEnd: (vertex: Int, meters: Double)? {
        guard let at = latest?.coordinate, line.distanceMeters(from: at) <= Self.awayThresholdMeters else { return nil }
        let end = pinVertices.first { $0 > progressSegment } ?? line.segmentCount
        var meters = Geo.distanceMeters(at, line.coordinates[progressSegment + 1])
        for vertex in (progressSegment + 1)..<end {
            meters += Geo.distanceMeters(line.coordinates[vertex], line.coordinates[vertex + 1])
        }
        return (end, meters)
    }

    private func request(from origin: Coordinate) -> RerouteRequest {
        let passed = pinVertices.firstIndex { $0 > progressSegment } ?? pinVertices.count
        return RerouteRequest(origin: origin, remainingWaypoints: Array(waypoints[passed...]),
                              firstRemainingWaypoint: passed, destination: line.destination, lambda: lambda,
                              planToken: planToken)
    }
}
