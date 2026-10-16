import Foundation

/// Where a feature's moments go (T-0361 R1). The app's one conformer is PlanAdapter's LiveMoments; each feature
/// reads it from an environment key of its own and the shell sets it, so a feature never imports the client.
public protocol AppMomentReporting: Sendable {
    func report(_ moment: AppMoment)
}
