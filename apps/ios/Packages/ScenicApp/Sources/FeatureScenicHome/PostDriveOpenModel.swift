import Observation
import ScenicKit

/// "Prettier than your usual way?" at the next open after a handoff (T-0366 R4-R6): thin wiring over ScenicKit. The
/// shell builds one, wraps the home's moments with `marking(_:)` (the two handoffs set the marker), puts it in the
/// home's environment and calls `opened()` on every foreground open; PostDriveNextOpen decides. The home sheet shows
/// PostDriveCard while `isAsking`, and the answer goes to the same sink as the drive screen's.
@MainActor @Observable
public final class PostDriveOpenModel {
    public private(set) var isAsking = false
    @ObservationIgnored private let marker: any HandoffMarkerStoring
    @ObservationIgnored private let fix: any OpenFixReading
    @ObservationIgnored private let answers: (any PostDriveAnswering)?

    public init(fix: any OpenFixReading, answers: (any PostDriveAnswering)?) {
        self.marker = DefaultsHandoffMarker()
        self.fix = fix
        self.answers = answers
    }

    /// The home's moment reporter: `inner` hears every moment, and a handoff sets this model's marker.
    public func marking(_ inner: any AppMomentReporting) -> any AppMomentReporting {
        HandoffMarkingMoments(inner: inner, marker: marker)
    }

    /// A foreground open: asks when PostDriveNextOpen says so.
    public func opened() {
        Task {
            if await PostDriveNextOpen.opened(marker: marker, fix: fix) { isAsking = true }
        }
    }

    func answered(_ answer: PostDriveAnswer) {
        PostDriveQuestion.send(answer, to: answers)
        isAsking = false
    }
}
