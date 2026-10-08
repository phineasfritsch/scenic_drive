import Foundation
import Handoff
import ScenicKit
import Testing

/// T-0314 R8: a loop handed to Apple Maps is ONE URL that starts and ends at the loop's start with the loop's pinned
/// waypoints in order, compared by FULL equality to a URL built here; more than nine waypoints is refused.
@Suite("LoopHandoffTests")
struct LoopHandoffTests {
    static let start = Coordinate(latitude: 34.02, longitude: -118.49)

    static func pins(_ count: Int) -> [Coordinate] {
        (0..<count).map { Coordinate(latitude: 34.03 + Double($0) * 0.01, longitude: -118.5 - Double($0) * 0.01) }
    }

    @Test("one URL from the start back to the start through the pins, in order", arguments: [0, 1, 3, 9])
    func loopURL(_ count: Int) throws {
        let url = try LoopHandoff.url(start: Self.start, waypoints: Self.pins(count))
        let expected = try AppleMapsDirections(source: Self.start, destination: Self.start,
                                               waypoints: Self.pins(count)).url()
        #expect(url == expected)
        let items = URLComponents(url: url, resolvingAgainstBaseURL: false)?.queryItems ?? []
        let source = items.first { $0.name == "source" }?.value
        #expect(source != nil && source == items.first { $0.name == "destination" }?.value)
        #expect(items.filter { $0.name == "waypoint" }.count == count)
    }

    @Test("ten pins are refused, never cut to nine")
    func tenPinsRefused() {
        #expect(throws: HandoffError.tooManyWaypoints(count: 10, max: 9)) {
            try LoopHandoff.url(start: Self.start, waypoints: Self.pins(10))
        }
    }
}
