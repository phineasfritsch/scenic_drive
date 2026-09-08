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

/// Why a way was refused.
///
/// A closed enum, one case per rule in the plan. Closed so that a new gate cannot reach a driver - or an
/// autopsy - as an unexplained refusal, and so that adding one forces every switch over this type to be
/// revisited.
///
/// **There is deliberately no case for a motorway.** See `Gates` for why that is the point rather than an
/// omission.
public enum GateReason: String, Equatable, Sendable, CaseIterable {
    /// `surface` names a material a sedan should not be sent onto.
    case unpavedSurface

    /// `highway = track`, or `tracktype` at grade3 or worse.
    case track

    /// `smoothness` worse than intermediate.
    case tooRough

    /// `access` forbids the public, or `motor_vehicle = no`.
    case noAccess

    /// A gate that is recorded as locked. An unlocked one is not refused - the driver decides.
    case lockedBarrier

    /// `ford = yes`. Positive evidence of water across the road.
    case ford

    /// A service way that is a driveway, a parking aisle or similar - not a road anyone drives for pleasure.
    case serviceWay
}
