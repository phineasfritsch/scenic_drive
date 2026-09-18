import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// The waypoint cap, in both shapes a caller can build: with an origin and without one.
///
/// Three of the tests below used to live in `AppleMapsDirectionsTests`, and every fixture there that reached
/// the cap omitted `source` - so the cap was proved only for the shape the product never uses. `source`
/// exists precisely because the app knows where the user is standing when they tap the button. A reviewer
/// showed what that permitted, with 41 tests green both times, on the single line `url()` opens with:
///
///   * `if waypoints.count + (source == nil ? 0 : 1) > Self.maxWaypoints` - the off-by-one somebody writes
///     on deciding the origin counts as a stop. A legitimate nine-stop scenic route with a known origin now
///     THROWS, and the free tier's only button fails;
///   * `if source == nil, waypoints.count > Self.maxWaypoints` - "refuse, never truncate", one of the three
///     decisions the task log says are worth arguing with, simply not enforced whenever a source is present.
///
/// Neither mutation can change a fixture that has no source, which is why `capIsInclusive`'s old title -
/// "exactly the cap is allowed" - claimed a property unconditionally while proving it for one branch. Both
/// shapes are enumerated below, the same way `neverAvoidsHighways` and `noSource` were fixed in the pass
/// before this one.
///
/// The counts here are WRITTEN OUT as 9 and 10 rather than reached through `AppleMapsDirections.maxWaypoints`.
/// Building the fixture out of the constant under test is what left the cap without a witness in the first
/// place: raising it from 9 to 99 kept every such fixture in range and the whole suite green.
@Suite("Apple Maps directions - the waypoint cap")
struct AppleMapsDirectionsCapTests {

    static let ucla = Coordinate(latitude: 34.0689, longitude: -118.4452)
    static let latigo = Coordinate(latitude: 34.0421, longitude: -118.7563)
    static let malibu = Coordinate(latitude: 34.0259, longitude: -118.7798)

    static func items(_ url: URL) -> [(String, String)] {
        let c = URLComponents(url: url, resolvingAgainstBaseURL: false)
        return (c?.queryItems ?? []).map { ($0.name, $0.value ?? "") }
    }

    @Test("the cap is nine, and the number itself is pinned")
    func capValueIsPinned() {
        // Every other test used to reach the cap through `AppleMapsDirections.maxWaypoints`, so raising it
        // from 9 to 99 left the whole suite green - the value had no witness. A reviewer found that by
        // mutating it. Nine is OUR choice (Apple documents no maximum), which makes it a decision that
        // should have to be changed deliberately rather than drift.
        #expect(AppleMapsDirections.maxWaypoints == 9)
    }

    @Test("exactly nine pinned stops is allowed, with no origin")
    func capIsInclusive() throws {
        let url = try AppleMapsDirections(destination: Self.malibu,
                                          waypoints: Array(repeating: Self.latigo, count: 9)).url()
        let pinned = Self.items(url).filter { $0.0 == "waypoint" }.map(\.1)
        #expect(pinned == Array(repeating: "34.04210,-118.75630", count: 9), "got \(pinned)")
    }

    @Test("exactly nine pinned stops is allowed WITH an origin - the shape the app always builds")
    func capIsInclusiveWithASource() throws {
        // MISSED before this test existed: `waypoints.count + (source == nil ? 0 : 1) > maxWaypoints`
        // refuses this route while every no-source fixture stays green.
        let url = try AppleMapsDirections(source: Self.ucla,
                                          destination: Self.malibu,
                                          waypoints: Array(repeating: Self.latigo, count: 9)).url()
        let items = Self.items(url)
        let pinned = items.filter { $0.0 == "waypoint" }.map(\.1)
        #expect(pinned == Array(repeating: "34.04210,-118.75630", count: 9), "got \(pinned)")
        // The origin is still the origin, and is not one of the nine.
        #expect(items.filter { $0.0 == "source" }.map(\.1) == ["34.06890,-118.44520"])
        #expect(items.filter { $0.0 == "destination" }.map(\.1) == ["34.02590,-118.77980"])
    }

    @Test("ten pinned stops is refused, not truncated, with no origin")
    func refusesTruncation() {
        #expect(throws: HandoffError.tooManyWaypoints(count: 10, max: 9)) {
            _ = try AppleMapsDirections(destination: Self.malibu,
                                        waypoints: Array(repeating: Self.latigo, count: 10)).url()
        }
    }

    @Test("ten pinned stops is refused, not truncated, WITH an origin")
    func refusesTruncationWithASource() {
        // MISSED before this test existed: `if source == nil, waypoints.count > maxWaypoints` truncates
        // nothing and refuses nothing on the live path - it emits an eleven-stop URL and says so to no one.
        #expect(throws: HandoffError.tooManyWaypoints(count: 10, max: 9)) {
            _ = try AppleMapsDirections(source: Self.ucla,
                                        destination: Self.malibu,
                                        waypoints: Array(repeating: Self.latigo, count: 10)).url()
        }
    }

    @Test("a refusal emits no URL at all, rather than a shorter drive")
    func refusalEmitsNothing() {
        // The refusal must not be a truncation wearing an error's name: `let waypoints = Array(prefix(9))`
        // returns a perfectly good URL for a route that is no longer the scenic one.
        for plan in [AppleMapsDirections(destination: Self.malibu,
                                         waypoints: Array(repeating: Self.latigo, count: 10)),
                     AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                         waypoints: Array(repeating: Self.latigo, count: 10)),
                     AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                         waypoints: Array(repeating: Self.latigo, count: 25))] {
            #expect(throws: HandoffError.self) { _ = try plan.url() }
        }
    }
}
