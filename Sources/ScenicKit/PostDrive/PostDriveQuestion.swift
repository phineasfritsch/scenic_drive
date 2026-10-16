import Foundation

/// "Prettier than your usual way?" - when the app asks it and what an answer sends (T-0358 R2-R6), decided here so it
/// is tested on Linux. The drive screen calls `asks(after:alreadyAsked:)` when End drive is tapped and `send(_:to:)`
/// with the button tapped; it decides nothing itself.
///
/// Asked at most once per drive and never in motion: only on the full surface (a known speed at or below the
/// P-SAFE-09 gate; an unknown speed is moving), and only for an in-app drive that arrived, as it ends, or after a
/// handoff, at the next open.
public enum PostDriveQuestion {
    public static let prompt = "Prettier than your usual way?"

    public static func asks(outcome: PostDriveOutcome, moment: PostDriveMoment, surface: DriveSurface,
                            alreadyAsked: Bool) -> Bool {
        guard !alreadyAsked, surface == .full else { return false }
        switch (outcome, moment) {
        case (.arrived, .driveEnded), (.handedOff, .appOpened): return true
        case (.arrived, .appOpened), (.endedEarly, .driveEnded), (.endedEarly, .appOpened), (.handedOff, .driveEnded):
            return false
        }
    }

    /// The in-app drive as End drive is tapped: the display's surface (full exactly when it shows details) and
    /// whether the drive had arrived.
    public static func asks(after display: DriveDisplay, alreadyAsked: Bool) -> Bool {
        asks(outcome: display.arrived ? .arrived : .endedEarly, moment: .driveEnded,
             surface: display.showsDetails ? .full : .minimal, alreadyAsked: alreadyAsked)
    }

    /// Hands the sink the answer's wire value; a dismissal, or no sink, sends nothing.
    public static func send(_ answer: PostDriveAnswer, to sink: (any PostDriveAnswering)?) {
        guard let sink, let prettier = answer.prettier else { return }
        sink.answered(prettier: prettier)
    }
}
