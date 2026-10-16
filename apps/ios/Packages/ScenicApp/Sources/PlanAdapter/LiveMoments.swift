import ScenicKit
import Telemetry

/// The app's one AppMomentReporting (T-0361 R1): each moment a feature reports becomes at most one LiveTelemetry
/// event, constructed there on its one emit line. The shell sets it in every feature's environment key, so no
/// feature imports the telemetry client.
public struct LiveMoments: AppMomentReporting {
    public init() {}

    public func report(_ moment: AppMoment) {
        switch moment {
        case .planPreviewOnScreen:
            LiveTelemetry.previewShown()
        case .driveHandedToAppleMaps:
            LiveTelemetry.handoffTapped(.appleMaps)
        case .surpriseHandedToAppleMaps:
            LiveTelemetry.surpriseTakeMeThere()
        case let .surpriseDeclined(reason):
            guard let wire = Self.wire(reason) else { return }
            LiveTelemetry.surpriseNotThis(wire)
        case .guidanceBegan:
            LiveTelemetry.driveStarted()
        case let .guidanceEnded(arrived, fraction, count):
            if arrived {
                LiveTelemetry.driveCompleted(fraction: fraction, deviations: count)
            } else {
                LiveTelemetry.driveAbandoned(fraction: fraction)
            }
        }
    }

    /// R7: the paywall came on screen - Entitlements' `paywallShown` key (it cannot see a ScenicKit type).
    public static func paywallShown() {
        LiveTelemetry.paywall(.shown)
    }

    /// T-0370: a purchase from the paywall's store view was verified and finished - Entitlements'
    /// `paywallConverted` key.
    public static func paywallConverted() {
        LiveTelemetry.paywall(.converted)
    }

    /// R5: the card's reason on the closed wire list; Wrong time has no wire reason and sends nothing (T-0371).
    static func wire(_ reason: SurpriseFeedback.Reason) -> SurpriseNotThisReason? {
        switch reason {
        case .tooFar: return .tooFar
        case .beenThere: return .beenThere
        case .notMyThing: return .notMyThing
        case .wrongTime: return nil
        }
    }
}
