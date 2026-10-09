import Foundation

/// The device's one corridor learner (T-0343 R1): the learned speeds, the drive's feed into them, and the save
/// that keeps them across launches. The app holds one, PlanAdapter's LiveCorridorLearner.shared; the drive feeds
/// it every fix and the planner reads it for the preview. It never leaves the device (P-PRIV-05).
@MainActor
public final class CorridorLearner {
    public private(set) var speeds: LearnedCorridorSpeeds
    /// Called with every row of `speeds` each time a fix taught an edge, and at no other time.
    private let save: @MainActor ([CorridorSlotRow]) -> Void

    public init(speeds: LearnedCorridorSpeeds, save: @escaping @MainActor ([CorridorSlotRow]) -> Void) {
        self.speeds = speeds
        self.save = save
    }

    /// The clock for a drive on `preview`; nil when it carries no runs or its runs make no CorridorRoute of its line.
    public func clock(for preview: PlanPreview) -> CorridorClock? {
        guard let runs = preview.timeRuns, let route = CorridorRoute(route: preview.route, timeRuns: runs) else {
            return nil
        }
        return CorridorClock(route: route)
    }

    /// One location fix at `date`: the controller observes it first, then the clock reads the controller's session
    /// at that same date and teaches `speeds`; the rows are saved when an edge was taught. Answers the controller's
    /// commands. The fix's timestamp is the date's, so the clock's time cannot drift from the controller's.
    public func observe(coordinate: Coordinate, speedMetersPerSecond: Double, at date: Date,
                        on controller: inout DriveController, clock: inout CorridorClock?) -> [DriveCommand] {
        let commands = controller.observe(DriveFix(coordinate: coordinate, speedMetersPerSecond: speedMetersPerSecond,
                                                   timestamp: date.timeIntervalSinceReferenceDate))
        if (clock?.observe(controller.session, at: date, into: &speeds) ?? 0) > 0 {
            save(speeds.rows)
        }
        return commands
    }
}
