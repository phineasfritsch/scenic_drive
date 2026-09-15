import Foundation

/// Whether a way may be routed over at all, and if not, which rule refused it.
///
/// **Not a `Bool`.** The plan makes `ops/route-autopsy <plan-id>` the gate-failure playbook - *"dumps per-edge
/// GATE/M/E terms"* - and a boolean cannot tell anyone why a road was refused. A refusal nobody can explain is
/// one nobody can argue with, and the first time a gate is wrong it will look exactly like a routing bug.
public enum GateDecision: Equatable, Sendable {
    /// The way may be routed. It may still be dull; that is the scoring function's business, not this one's.
    case allowed

    /// The way is refused, for this reason.
    case refused(GateReason)

    public var isAllowed: Bool {
        if case .allowed = self { return true }
        return false
    }

    /// The rule that refused it, or nil when nothing did.
    public var reason: GateReason? {
        if case let .refused(r) = self { return r }
        return nil
    }
}
