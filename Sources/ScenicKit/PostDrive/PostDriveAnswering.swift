import Foundation

/// Where a post-drive answer goes (T-0358 R7). The app's one conformer is PlanAdapter's, which hands it to the
/// telemetry client as post_drive_answer; the feature that asks never imports the client.
public protocol PostDriveAnswering: Sendable {
    func answered(prettier: Bool)
}
