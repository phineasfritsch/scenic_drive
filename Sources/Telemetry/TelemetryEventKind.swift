import Foundation

/// The plan fourteen events as a closed, iterable list (T-0265 R1). `TelemetryEvent.kind` maps every case
/// here; the raw value is the wire name except for `paywall`, whose two wire names come from its PaywallStep.
public enum TelemetryEventKind: String, CaseIterable, Sendable {
    case planRequested = "plan_requested"
    case planResult = "plan_result"
    case previewShown = "preview_shown"
    case handoffTapped = "handoff_tapped"
    case driveStarted = "drive_started"
    case driveCompleted = "drive_completed"
    case driveAbandoned = "drive_abandoned"
    case postDriveAnswer = "post_drive_answer"
    case surpriseShown = "surprise_shown"
    case surpriseNotThis = "surprise_not_this"
    case surpriseTakeMeThere = "surprise_take_me_there"
    case surpriseArrived = "surprise_arrived"
    case corpusActivated = "corpus_activated"
    case paywall
}
