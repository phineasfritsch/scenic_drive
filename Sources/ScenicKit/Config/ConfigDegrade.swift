/// What the remote config does to one planning screen on this device (T-0357 R5, R6; T-0364 R3-R5): nothing, a
/// pause, an update prompt, or the screen's feature switched off. A sheet's gate issues no ticket unless it is
/// `clear`, and its form shows `notice(on:)` in place of its Go button.
public enum ConfigDegrade: String, CaseIterable, Equatable, Sendable {
    case clear
    case planningPaused
    case updateRequired
    /// The pause on the plan screen while feature_surprise is false: its line does not offer Surprise Me (R4).
    case pausedSurpriseOff
    /// The loop's or the trip's own flag is false (R3).
    case featureOff

    /// The update prompt's one line (T-0357 R6), on every screen.
    public static let updateLine = "This version can't plan drives anymore. Update Scenic Drive from the App Store to keep planning."
    /// R4: the plan screen's pause before the tap; the sheet has no Surprise button, so the line says where it is.
    public static let pausedLine = "Planning is paused right now. Surprise Me on the home screen still works."
    public static let pausedQuietLine = "Planning is paused right now. Try again in a little while."
    /// R5: each screen's switched-off line.
    public static let planOffLine = "Planning is switched off for now. Try again later."
    public static let loopOffLine = "Loops are switched off for now. You can still plan a drive."
    public static let tripOffLine = "Road trips are switched off for now. You can still plan a drive."

    /// R3: an update when our build is known and below the minimum; else the pause; else the screen's flag; else
    /// clear. An unknown build never prompts an update - the Worker enforces no build, and we cannot claim one is needed.
    public static func of(_ config: RemoteConfig, appBuild: Int?, on screen: ConfigScreen) -> ConfigDegrade {
        if let appBuild, config.minAppBuild > appBuild { return .updateRequired }
        if config.planningPaused {
            return screen == .plan && !config.featureSurprise ? .pausedSurpriseOff : .planningPaused
        }
        switch screen {
        case .plan: return .clear
        case .loop: return config.featureLoop ? .clear : .featureOff
        case .trip: return config.featureTrip ? .clear : .featureOff
        }
    }

    /// The line shown on `screen` before the tap: nil exactly when clear. Loop and trip pauses are their own typed copy.
    public func notice(on screen: ConfigScreen) -> String? {
        switch (self, screen) {
        case (.clear, _): return nil
        case (.updateRequired, _): return Self.updateLine
        case (.planningPaused, .plan): return Self.pausedLine
        case (.pausedSurpriseOff, .plan): return Self.pausedQuietLine
        case (.planningPaused, .loop), (.pausedSurpriseOff, .loop): return LoopFailure.planningPaused.line
        case (.planningPaused, .trip), (.pausedSurpriseOff, .trip): return TripFailure.planningPaused.line
        case (.featureOff, .plan): return Self.planOffLine
        case (.featureOff, .loop): return Self.loopOffLine
        case (.featureOff, .trip): return Self.tripOffLine
        }
    }
}
