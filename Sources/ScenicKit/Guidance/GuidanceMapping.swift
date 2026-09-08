import Foundation

/// Turns what GraphHopper said into what the driver is asked to do.
///
/// **Why "unknown code fails the build" is true here.** `maneuver(for:)` switches over `GuidanceSign` with no
/// `default:` clause. Swift requires that switch to be exhaustive, so adding a case to `GuidanceSign` - which
/// is what happens when GraphHopper declares a new sign - stops this file compiling until somebody decides what
/// the driver should be told. That is the plan's gate, and it is enforced by the compiler rather than by a
/// convention anyone has to remember.
///
/// A `default:` here would silently satisfy the compiler and destroy the guarantee. Do not add one.
public enum GuidanceMapping {

    /// The manoeuvre for a sign this version knows.
    ///
    /// Total over `GuidanceSign` - every case returns something, and nothing is dropped.
    public static func maneuver(for sign: GuidanceSign) -> GuidanceManeuver {
        switch sign {
        case .continueOnStreet:  return .continueStraight

        case .turnSlightLeft:    return .turn(side: .left,  sharpness: .slight)
        case .turnLeft:          return .turn(side: .left,  sharpness: .normal)
        case .turnSharpLeft:     return .turn(side: .left,  sharpness: .sharp)
        case .turnSlightRight:   return .turn(side: .right, sharpness: .slight)
        case .turnRight:         return .turn(side: .right, sharpness: .normal)
        case .turnSharpRight:    return .turn(side: .right, sharpness: .sharp)

        case .keepLeft:          return .keep(side: .left)
        case .keepRight:         return .keep(side: .right)

        case .uTurnLeft:         return .uTurn(side: .left)
        case .uTurnRight:        return .uTurn(side: .right)
        case .uTurnUnknown:      return .uTurn(side: nil)

        case .useRoundabout:     return .enterRoundabout
        case .leaveRoundabout:   return .exitRoundabout

        case .ferry:             return .ferry
        case .reachedVia:        return .reachedWaypoint
        case .finish:            return .arrive

        case .unknown:           return .routerSaidUnknown
        case .ignore:            return .ignore

        case .ptStartTrip, .ptTransfer, .ptEndTrip:
            return .notApplicableToDriving
        }
    }

    /// Decode a raw integer straight off the wire.
    ///
    /// An integer this version has no case for is a **typed throw**, never a fallback to
    /// `.continueStraight`. Falling back would be the worst available behaviour: the driver is told to carry
    /// on at precisely the junction the router wanted to say something about, and nothing anywhere reports it.
    /// A throw makes the caller decide, and makes the condition countable.
    public static func maneuver(forRawSign raw: Int) throws -> GuidanceManeuver {
        guard let sign = GuidanceSign(rawValue: raw) else {
            throw GuidanceDecodingError.unrecognisedSign(raw)
        }
        return maneuver(for: sign)
    }
}

/// What went wrong decoding a router instruction.
public enum GuidanceDecodingError: Error, Equatable, Sendable {
    /// GraphHopper sent a sign integer this build has no case for.
    ///
    /// Carries the raw value so it can be logged and turned into a task, rather than counted as an anonymous
    /// failure. GraphHopper's own sign space is not contiguous - release 11.0 declares -8, -7, -6, then jumps
    /// to -3, with **no -5 and no -4** - so "it is between the ends of the range" is not evidence that a value
    /// is valid, and this error is reachable for small integers, not only for wild ones.
    case unrecognisedSign(Int)
}
