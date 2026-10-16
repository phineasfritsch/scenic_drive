import Foundation

/// The home's moment reporter (T-0366 R1): the two successful handoffs set the marker to
/// PostDriveNextOpen.opensAfterHandoff, and every moment goes on to the inner reporter unchanged. The shell wraps
/// LiveMoments in it, so the marker is set on exactly the path the handoff moment is reported on.
public struct HandoffMarkingMoments: AppMomentReporting {
    private let inner: (any AppMomentReporting)?
    private let marker: any HandoffMarkerStoring

    public init(inner: (any AppMomentReporting)?, marker: any HandoffMarkerStoring) {
        self.inner = inner
        self.marker = marker
    }

    public func report(_ moment: AppMoment) {
        if Self.marks(moment) {
            marker.setOpensLeft(PostDriveNextOpen.opensAfterHandoff)
        }
        inner?.report(moment)
    }

    /// Whether a moment is a handoff. Exhaustive, so a new moment is classified here before it compiles.
    static func marks(_ moment: AppMoment) -> Bool {
        switch moment {
        case .driveHandedToAppleMaps, .surpriseHandedToAppleMaps:
            return true
        case .planPreviewOnScreen, .surpriseDeclined, .guidanceBegan, .guidanceEnded:
            return false
        }
    }
}
