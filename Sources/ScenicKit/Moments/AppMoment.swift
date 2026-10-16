import Foundation

/// The moments the app's features report (T-0361 R1): what happened, in the features' own terms. PlanAdapter's one
/// conformer of AppMomentReporting turns each into at most one telemetry event, so no feature target imports the
/// telemetry client. Nothing here is a place: a reason, a flag, a fraction and a count.
public enum AppMoment: Equatable, Sendable {
    /// A plan's preview card - scenic, loop or road trip - came on screen (R2).
    case planPreviewOnScreen
    /// The home's drive was handed to Apple Maps: the open succeeded (R3).
    case driveHandedToAppleMaps
    /// The Surprise's place was handed to Apple Maps: the open succeeded (R4).
    case surpriseHandedToAppleMaps
    /// The Surprise was turned down, for this reason (R5).
    case surpriseDeclined(SurpriseFeedback.Reason)
    /// In-app guidance started (R6).
    case guidanceBegan
    /// In-app guidance ended: whether it arrived, the fraction of the drive driven (DriveSession.fractionDriven)
    /// and how many times it went off-route (DriveSession.offRouteCount) (R6).
    case guidanceEnded(arrived: Bool, fractionDriven: Double, offRouteCount: Int)
}
