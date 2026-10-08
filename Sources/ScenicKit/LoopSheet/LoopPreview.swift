/// A planned loop as the sheet shows it (T-0314 R6): the path out and back, the pinned waypoints the Apple Maps
/// handoff carries (R8), the drive time and distance, the retrace fraction the DEVICE measured on that path
/// (RetraceDetector), and the estimate flag (CLAUDE.md: the badge stays until a corridor has learned samples).
public struct LoopPreview: Equatable, Sendable {
    public let path: [Coordinate]
    public let waypoints: [Coordinate]
    public let durationSeconds: Double
    public let distanceMeters: Double
    public let retraceFraction: Double
    public let etaIsEstimate: Bool

    public init(path: [Coordinate], waypoints: [Coordinate], durationSeconds: Double, distanceMeters: Double,
                retraceFraction: Double, etaIsEstimate: Bool) {
        self.path = path
        self.waypoints = waypoints
        self.durationSeconds = durationSeconds
        self.distanceMeters = distanceMeters
        self.retraceFraction = retraceFraction
        self.etaIsEstimate = etaIsEstimate
    }
}
