/// What the remote config does to planning on this device (T-0357 R5, R6): nothing, a pause, or an update prompt.
/// The plan sheet's gate issues no ticket unless it is `clear`, and the form shows the notice in place of Plan.
public enum ConfigDegrade: String, CaseIterable, Equatable, Sendable {
    case clear
    case planningPaused
    case updateRequired

    /// The update prompt's one line (R6).
    public static let updateLine = "This version can't plan drives anymore. Update Scenic Drive from the App Store to keep planning."

    /// R5: an update when our build is known and below the minimum; else the pause; else clear. An unknown build never
    /// prompts an update - the Worker enforces no build, and we cannot claim one is needed.
    public static func of(_ config: RemoteConfig, appBuild: Int?) -> ConfigDegrade {
        if let appBuild, config.minAppBuild > appBuild { return .updateRequired }
        return config.planningPaused ? .planningPaused : .clear
    }

    /// The line shown before the user taps Plan: the typed planningPaused copy by reference, the update line, or nil.
    public var notice: String? {
        switch self {
        case .clear: return nil
        case .planningPaused: return PlanFailureCopy.of(.planningPaused).line
        case .updateRequired: return Self.updateLine
        }
    }
}
