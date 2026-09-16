import Foundation

/// Why a way was refused.
///
/// A closed enum, one case per rule in the plan. Closed so that a new gate cannot reach a driver - or an
/// autopsy - as an unexplained refusal, and so that adding one forces every switch over this type to be
/// revisited.
///
/// **There is deliberately no case for a motorway** - but that is a statement of intent, not a guard, and
/// this comment used to claim otherwise. A branch that refuses a motorway can reuse `.noAccess` and never
/// touch this enum, which is how four reviews of PR #82 refuted the earlier wording here.
///
/// What guards the invariant lives in `Gates`, not here: `ConsideredTags` answers `nil` for every key
/// outside `Gates.consideredTagKeys`, so no rule can be written on a freeway tag; the key set itself is
/// pinned as a literal; and the behaviour is pinned in `GatesInvariantTests`. Two residuals stay open and
/// `Gates` names them - a refusal keyed on a *considered* key, and a refusal typed into `Gates.decide`
/// itself, where the raw dictionary is still in scope.
///
/// Split out of `GateDecision.swift` on the second review of PR #82: CLAUDE.md's file discipline is one type
/// per file with the filename equal to the type name, and two public types shared that file.
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
