import Foundation

/// What the drive screen shows for one surface and mode (T-0324 R2). The screen renders these four fields and reads
/// neither DriveSurface nor DriveMode itself, so the motion gate (P-SAFE-09) is decided here, on Linux.
public struct DriveDisplay: Sendable, Equatable {
    /// The one action, on both surfaces.
    public let actionTitle: String
    /// The action's minimum height in points: the one large action while moving, an ordinary target when stopped.
    public let actionMinHeight: Double
    /// The reroute or rejoin state, nil while guiding: one short caption on the minimal surface, a sentence on full.
    public let status: String?
    /// The full surface adds the ETA line, the estimate badge and the conditions line; the minimal one adds nothing.
    public let showsDetails: Bool

    public static let endTitle = "End drive"
    public static let largeActionHeight = 60.0
    public static let actionHeight = 44.0

    public init(surface: DriveSurface, mode: DriveMode) {
        let moving = surface == .minimal
        actionTitle = Self.endTitle
        actionMinHeight = moving ? Self.largeActionHeight : Self.actionHeight
        switch mode {
        case .guiding: status = nil
        case .rerouting: status = moving ? "Finding a new way" : "You left the route. Finding a new way."
        case .rejoining: status = moving ? "Head back to your route" : "You left the route and are offline. Head back to it."
        }
        showsDetails = !moving
    }

    init(actionTitle: String, actionMinHeight: Double, status: String?, showsDetails: Bool) {
        self.actionTitle = actionTitle
        self.actionMinHeight = actionMinHeight
        self.status = status
        self.showsDetails = showsDetails
    }

    /// The display for the session as it stands - what NavAdapter's DriveNavigator publishes after every input.
    public init(session: DriveSession) {
        self.init(surface: session.surface, mode: session.mode)
    }
}
