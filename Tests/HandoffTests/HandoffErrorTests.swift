import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// `HandoffError` itself: which coordinates are refused, what the refusal carries, and what it says.
///
/// Two gaps a reviewer found, both with 41 tests green:
///
///   * **the type had no coverage at all.** `ops/mutate/handoff.py` opened with "Mutation harness for
///     Sources/Handoff" while `SRC` named `AppleMapsDirections.swift` and nothing else, so
///     `HandoffError.swift` - public API, `Equatable` with associated values and a
///     `CustomStringConvertible` description - was mutated by nothing and asserted by nothing. Replacing
///     the whole `tooManyWaypoints` description with `"too many waypoints"` was MISSED. That description
///     is what a support ticket quotes; a refusal that will not say how many stops were pinned, or what the
///     limit was, cannot be acted on by the person reading it.
///   * **the refusal payload was never asserted, only its type.** `refusesNonCoordinates` said
///     `#expect(throws: HandoffError.self)` and stopped there, so
///     `notACoordinate(latitude: c.longitude, longitude: c.latitude)` - the two arguments swapped at the
///     throw site - was MISSED. `tooManyWaypoints` was pinned by value; this one was not.
///
/// Every expectation below is hand-typed. The descriptions are transcribed from `HandoffError.swift` by
/// reading it, not by calling anything that builds them - an expected value computed from the thing it
/// checks is this repository's signature defect, and the two findings above are what it costs.
///
/// The fixtures are deliberately ASYMMETRIC - 91 against -12, not 91 against 91 - because a swapped pair is
/// exactly the mutation in question and a symmetric fixture cannot see it.
@Suite("HandoffError")
struct HandoffErrorTests {

    static let malibu = Coordinate(latitude: 34.0259, longitude: -118.7798)

    @Test("a non-coordinate is refused wherever it appears",
          arguments: [Coordinate(latitude: .nan, longitude: 0),
                      Coordinate(latitude: 0, longitude: .nan),
                      Coordinate(latitude: .infinity, longitude: 0),
                      Coordinate(latitude: 91, longitude: 0),
                      Coordinate(latitude: -90.5, longitude: 0),
                      Coordinate(latitude: 0, longitude: 180.1),
                      Coordinate(latitude: 0, longitude: -181)])
    func refusesNonCoordinates(bad: Coordinate) {
        #expect(throws: HandoffError.self) { _ = try AppleMapsDirections(destination: bad).url() }
        #expect(throws: HandoffError.self) {
            _ = try AppleMapsDirections(source: bad, destination: Self.malibu).url()
        }
        #expect(throws: HandoffError.self) {
            _ = try AppleMapsDirections(destination: Self.malibu, waypoints: [bad]).url()
        }
    }

    @Test("the refusal names the coordinate that was refused, latitude first")
    func refusalCarriesTheOffendingCoordinate() {
        // NaN is left out on purpose: `HandoffError` is `Equatable` and NaN != NaN, so an `#expect(throws:)`
        // comparing a payload that contains one can never match. These three are finite, out of range, and
        // asymmetric, so a swapped pair produces a DIFFERENT value rather than the same one.
        #expect(throws: HandoffError.notACoordinate(latitude: 91, longitude: -12)) {
            _ = try AppleMapsDirections(destination: Coordinate(latitude: 91, longitude: -12)).url()
        }
        #expect(throws: HandoffError.notACoordinate(latitude: -7, longitude: 181)) {
            _ = try AppleMapsDirections(source: Coordinate(latitude: -7, longitude: 181),
                                        destination: Self.malibu).url()
        }
        #expect(throws: HandoffError.notACoordinate(latitude: 0.5, longitude: -190.25)) {
            _ = try AppleMapsDirections(destination: Self.malibu,
                                        waypoints: [Coordinate(latitude: 0.5, longitude: -190.25)]).url()
        }
    }

    @Test("the refusal message says how many stops were pinned and what the limit was")
    func tooManyWaypointsDescribesItself() {
        let d = HandoffError.tooManyWaypoints(count: 10, max: 9).description
        #expect(d == "10 waypoints exceeds the 9 this builder will pin; "
                + "select decision points upstream rather than truncating here", "got \(d)")
        // Asymmetric, so count and max swapped in the interpolation is a different string.
        let other = HandoffError.tooManyWaypoints(count: 25, max: 9).description
        #expect(other == "25 waypoints exceeds the 9 this builder will pin; "
                + "select decision points upstream rather than truncating here", "got \(other)")
    }

    @Test("the not-a-coordinate message quotes the pair, latitude first")
    func notACoordinateDescribesItself() {
        let d = HandoffError.notACoordinate(latitude: 91.0, longitude: -12.5).description
        #expect(d == "not a coordinate: 91.0, -12.5", "got \(d)")
    }

    @Test("the two refusals are distinguishable, and so are their payloads")
    func refusalsAreEquatableByPayload() {
        // `Equatable` is synthesised here, and a hand-written `==` in an extension silently replaces the
        // synthesised one - nothing stops compiling, and every `#expect(throws: HandoffError.someCase(...))`
        // in this module quietly stops comparing the numbers. That is a mutation in ops/mutate/handoff.py,
        // so this test has been seen red. Every expectation is over written-out values.
        #expect(HandoffError.tooManyWaypoints(count: 10, max: 9)
                != HandoffError.tooManyWaypoints(count: 9, max: 10))
        #expect(HandoffError.notACoordinate(latitude: 1, longitude: 2)
                != HandoffError.notACoordinate(latitude: 2, longitude: 1))
        #expect(HandoffError.notACoordinate(latitude: 1, longitude: 2)
                == HandoffError.notACoordinate(latitude: 1, longitude: 2))
        #expect(HandoffError.tooManyWaypoints(count: 10, max: 9)
                != HandoffError.notACoordinate(latitude: 10, longitude: 9))
        #expect(HandoffError.tooManyWaypoints(count: 10, max: 9).description
                != HandoffError.notACoordinate(latitude: 10, longitude: 9).description)
    }
}
