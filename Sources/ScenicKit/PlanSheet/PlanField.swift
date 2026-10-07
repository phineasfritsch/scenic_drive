/// Which end of the drive the plan sheet's search is filling (T-0294 R2, R4): the destination, or the typed start
/// that stands in for the device location - the location-denied path, and today the only path.
public enum PlanField: Equatable, Sendable {
    case destination
    case start
}
