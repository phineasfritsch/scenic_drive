import Foundation

/// Which product surface asked for a plan - the `feature` of `plan_requested`. A closed list, never a
/// free-form string (P-PRIV-05); the raw value is the label written to the data point.
public enum PlanFeature: String, CaseIterable, Sendable {
    case scenic
    case loop
    case surprise
    case roadTrip = "road_trip"
}
