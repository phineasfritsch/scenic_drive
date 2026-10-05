import Foundation

/// How a plan request ended - the `kind` of `plan_result`. A closed list; the raw value is the wire label.
public enum PlanResultKind: String, CaseIterable, Sendable {
    case routed
    case noAlternative = "no_alternative"
    case quotaExceeded = "quota_exceeded"
    case failed
}
