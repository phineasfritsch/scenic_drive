import Foundation

/// What the drive screen shows for one surface and mode (T-0324 R2), the line it draws (T-0328 R4), and the ETA line
/// and fresh-route note of that line (T-0330 R3/R4). The screen renders these ten fields (T-0358: `arrived`, read through PostDriveQuestion) and reads neither DriveSurface nor DriveMode itself, so the motion gate (P-SAFE-09) is
/// decided here, on Linux.
public struct DriveDisplay: Sendable, Equatable {
    /// The one action, on both surfaces.
    public let actionTitle: String
    /// The action's minimum height in points: the one large action while moving, an ordinary target when stopped.
    public let actionMinHeight: Double
    /// The reroute or rejoin state, nil while guiding: one short caption on the minimal surface, a sentence on full.
    public let status: String?
    /// The full surface adds the ETA line, the estimate badge and the conditions line; the minimal one adds nothing.
    public let showsDetails: Bool
    /// T-0328 R4: the line the map draws - the session's current one, so a taken reroute is what is drawn.
    public let line: [Coordinate]
    /// T-0330 R4: the ETA line of the line being driven - the preview's, then each taken answer's.
    public let etaLine: String
    /// T-0330 R3: freshNote on the full surface while the line is a fresh plan; nil otherwise (moving adds nothing).
    public let note: String?
    /// T-0358 R8: the drive has arrived (DriveVoice's arrival, handed in by NavAdapter); false from a session alone.
    public let arrived: Bool
    /// T-0397 R2: the seconds left on the line being driven - its ETA pro rata to the metres left past the progress
    /// vertex. The screen adds them to the clock for "Arrive h:mm".
    public let remainingSeconds: Double
    /// T-0397 R2: the minutes and miles left on the line being driven, "N min · N.N mi".
    public let glanceLine: String

    public static let freshNote = "A new route from here - not the rest of your plan."
    public static let endTitle = "End"
    public static let metersPerMile = 1_609.344
    public static let largeActionHeight = 60.0
    public static let actionHeight = 44.0

    public init(surface: DriveSurface, mode: DriveMode, line: [Coordinate] = [], etaLine: String = "",
                continued: Bool = true, arrived: Bool = false, remainingSeconds: Double = 0,
                remainingMeters: Double = 0) {
        let moving = surface == .minimal
        actionTitle = Self.endTitle
        actionMinHeight = moving ? Self.largeActionHeight : Self.actionHeight
        switch mode {
        case .guiding: status = nil
        case .rerouting: status = moving ? "Finding a new way" : "You left the route. Finding a new way."
        case .rejoining: status = moving ? "Head back to your route" : "You left the route and are offline. Head back to it."
        }
        showsDetails = !moving
        self.line = line
        self.etaLine = etaLine
        note = moving || continued ? nil : Self.freshNote
        self.arrived = arrived
        self.remainingSeconds = remainingSeconds
        glanceLine = Self.glanceLine(seconds: remainingSeconds, meters: remainingMeters)
    }

    init(actionTitle: String, actionMinHeight: Double, status: String?, showsDetails: Bool,
         line: [Coordinate] = [], etaLine: String = "", note: String? = nil, arrived: Bool = false,
         remainingSeconds: Double = 0, glanceLine: String = DriveDisplay.glanceLine(seconds: 0, meters: 0)) {
        self.actionTitle = actionTitle
        self.actionMinHeight = actionMinHeight
        self.status = status
        self.showsDetails = showsDetails
        self.line = line
        self.etaLine = etaLine
        self.note = note
        self.arrived = arrived
        self.remainingSeconds = remainingSeconds
        self.glanceLine = glanceLine
    }

    /// The display for the session as it stands - what NavAdapter's DriveNavigator publishes after every input.
    public init(session: DriveSession, arrived: Bool = false) {
        let whole = DriveSession.meters(along: session.line, to: session.line.segmentCount)
        let left = whole - session.drivenMeters
        self.init(surface: session.surface, mode: session.mode, line: session.line.coordinates,
                  etaLine: PlanPreview.etaLine(etaSeconds: session.etaSeconds,
                                               fastestEtaSeconds: session.fastestEtaSeconds),
                  continued: session.continued, arrived: arrived,
                  remainingSeconds: whole > 0 ? session.etaSeconds * left / whole : session.etaSeconds,
                  remainingMeters: left)
    }

    /// T-0397 R2: "N min · N.N mi" - whole minutes, and miles in tenths under 10 mi, whole miles from 10.
    public static func glanceLine(seconds: Double, meters: Double) -> String {
        let minutes = Int((seconds / 60).rounded())
        let tenths = (meters / metersPerMile * 10).rounded()
        let miles = tenths < 100 ? String(format: "%.1f", tenths / 10) : String(Int((meters / metersPerMile).rounded()))
        return "\(minutes) min · \(miles) mi"
    }
}
