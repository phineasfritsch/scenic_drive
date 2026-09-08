import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// The whole query string, transcribed by hand.
///
/// Every assertion in the sibling suite names one parameter at a time, and each of them stayed green while
/// the URL carried something extra, something twice, or something derived from the wrong field. Four
/// reviewer mutations lived in exactly that gap, all four with a green 34-test suite:
///
///   * `avoid=highways` appended only when `waypoints.isEmpty` - the branch that serves every short drive
///     and every first plan. `neverAvoidsHighways` had one fixture and it carried a waypoint.
///   * the first waypoint promoted to `source` when the caller gave none - a URL that starts the drive at
///     the first pinned stop instead of where the user is. `noSource` built a destination-only route, so the
///     branch was unreachable from it.
///   * `destination` emitted twice. `source` had an exactly-once assertion; `destination` had none, and
///     every reader uses `.first { ... }`.
///   * the mode raw values renamed to `walk`/`public`/`bike`, which Apple does not document. The mode test
///     looped over `allCases` comparing the emitted value to `m.rawValue`, so it recomputed its expectation
///     from the object under test and only `driving` had a witness.
///
/// The expectations below are LITERALS, typed out from Apple's documented grammar and this type's stated
/// parameter order. Never `pair(...)`, never `rawValue`, never a set built from `allCases`: an assertion
/// whose expected value is computed from the thing it checks is this repository's signature defect, and it
/// is what let all four of those through.
@Suite("Apple Maps directions URL - the whole query string")
struct AppleMapsDirectionsURLTests {

    // The same four places as the sibling suite, restated here so the expectations below can be read against
    // their inputs without opening another file.
    static let ucla = Coordinate(latitude: 34.0689, longitude: -118.4452)
    static let latigo = Coordinate(latitude: 34.0421, longitude: -118.7563)
    static let piuma = Coordinate(latitude: 34.0813, longitude: -118.6944)
    static let malibu = Coordinate(latitude: 34.0259, longitude: -118.7798)

    @Test("destination only - the first plan, and the shape avoid=highways would hide in")
    func destinationOnly() throws {
        let url = try AppleMapsDirections(destination: Self.malibu).url()
        #expect(url.absoluteString
                == "https://maps.apple.com/directions?destination=34.02590,-118.77980&mode=driving",
                "got \(url.absoluteString)")
    }

    @Test("source and destination, nothing else")
    func sourceAndDestination() throws {
        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu).url()
        #expect(url.absoluteString
                == "https://maps.apple.com/directions?source=34.06890,-118.44520"
                + "&destination=34.02590,-118.77980&mode=driving",
                "got \(url.absoluteString)")
    }

    @Test("waypoints without a source - no source is invented from the first pinned stop")
    func waypointsWithoutASource() throws {
        let url = try AppleMapsDirections(destination: Self.malibu,
                                          waypoints: [Self.latigo, Self.piuma]).url()
        #expect(url.absoluteString
                == "https://maps.apple.com/directions?destination=34.02590,-118.77980"
                + "&waypoint=34.04210,-118.75630&waypoint=34.08130,-118.69440&mode=driving",
                "got \(url.absoluteString)")
    }

    @Test("the full route - source, destination, two waypoints in order, mode")
    func fullRoute() throws {
        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                          waypoints: [Self.latigo, Self.piuma]).url()
        #expect(url.absoluteString
                == "https://maps.apple.com/directions?source=34.06890,-118.44520"
                + "&destination=34.02590,-118.77980"
                + "&waypoint=34.04210,-118.75630&waypoint=34.08130,-118.69440&mode=driving",
                "got \(url.absoluteString)")
    }

    @Test("each mode reaches the URL as the exact string Apple documents, written out one by one")
    func modeValuesAreWrittenOut() throws {
        // Four whole URLs, hand-typed. The previous version was
        //     for m in Mode.allCases { #expect(emitted(m) == m.rawValue) }
        // which passes for any raw values at all, documented or not.
        let expected: [(AppleMapsDirections.Mode, String)] = [
            (.driving, "https://maps.apple.com/directions?destination=34.02590,-118.77980&mode=driving"),
            (.walking, "https://maps.apple.com/directions?destination=34.02590,-118.77980&mode=walking"),
            (.transit, "https://maps.apple.com/directions?destination=34.02590,-118.77980&mode=transit"),
            (.cycling, "https://maps.apple.com/directions?destination=34.02590,-118.77980&mode=cycling"),
        ]
        for (mode, literal) in expected {
            let url = try AppleMapsDirections(destination: Self.malibu, mode: mode).url()
            #expect(url.absoluteString == literal, "mode \(mode) gave \(url.absoluteString)")
        }

        // And the table is exhaustive, so a fifth case cannot arrive without a written-out expectation.
        // `contains { $0.0 == m }` compares CASES, not raw values, so renaming a raw value cannot satisfy it.
        #expect(AppleMapsDirections.Mode.allCases.count == 4)
        for m in AppleMapsDirections.Mode.allCases {
            #expect(expected.contains { $0.0 == m }, "no written-out expectation for \(m)")
        }
    }

    @Test("the default mode is driving, because this is a car product")
    func defaultModeIsDriving() throws {
        let url = try AppleMapsDirections(destination: Self.malibu).url()
        #expect(url.absoluteString.hasSuffix("&mode=driving"), "got \(url.absoluteString)")
    }

    @Test("nothing is emitted twice - not source, not destination, not mode")
    func nothingIsEmittedTwice() throws {
        // `destination` had no exactly-once assertion, and every reader in this file and in the app uses
        // `.first { $0.0 == ... }`, which cannot see a second one.
        for plan in [AppleMapsDirections(destination: Self.malibu),
                     AppleMapsDirections(source: Self.ucla, destination: Self.malibu),
                     AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                         waypoints: [Self.latigo, Self.piuma], mode: .cycling)] {
            let names = (URLComponents(url: try plan.url(), resolvingAgainstBaseURL: false)?
                .queryItems ?? []).map(\.name)
            for once in ["destination", "mode"] {
                #expect(names.filter { $0 == once }.count == 1,
                        "\(once) appears \(names.filter { $0 == once }.count) times in \(names)")
            }
            #expect(names.filter { $0 == "source" }.count == (plan.source == nil ? 0 : 1))
        }
    }
}
