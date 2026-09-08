import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// What can and cannot be checked from here.
///
/// **Checkable, and checked below:** the parameter names against Apple's documented set, the coordinate
/// format, that waypoint order survives, that the builder refuses rather than truncates, that a decimal
/// comma cannot appear, and that the round trip through `URLComponents` returns what went in.
///
/// **NOT checkable from here:** whether Apple Maps, on a real iPhone, actually follows the pinned waypoints
/// rather than re-planning between source and destination. No unit test can answer that; it needs a phone.
/// It belongs in `pins/PINS.yaml` as `runs_on: device`, and this file must not be mistaken for having
/// covered it - green here means the URL is well-formed, not that the drive is right.
@Suite("Apple Maps directions URL")
struct AppleMapsDirectionsTests {

    // UCLA, and the Malibu canyon roads the first real scoring run ranked highest.
    static let ucla = Coordinate(latitude: 34.0689, longitude: -118.4452)
    static let latigo = Coordinate(latitude: 34.0421, longitude: -118.7563)
    static let piuma = Coordinate(latitude: 34.0813, longitude: -118.6944)
    static let malibu = Coordinate(latitude: 34.0259, longitude: -118.7798)

    static func items(_ url: URL) -> [(String, String)] {
        let c = URLComponents(url: url, resolvingAgainstBaseURL: false)
        return (c?.queryItems ?? []).map { ($0.name, $0.value ?? "") }
    }

    @Test("the path and host are the documented unified form, not the archived daddr scheme")
    func documentedForm() throws {
        let url = try AppleMapsDirections(destination: Self.malibu).url()
        #expect(url.scheme == "https")
        #expect(url.host == "maps.apple.com")
        #expect(url.path == "/directions")
        // The archived scheme's parameters must not appear. Their presence would mean someone "simplified"
        // this back to the form that is easier to remember and no longer documented.
        let names = Set(Self.items(url).map(\.0))
        #expect(names.isDisjoint(with: ["daddr", "saddr", "dirflg", "q"]))
    }

    @Test("every parameter emitted is one Apple documents for /directions")
    func onlyDocumentedParameters() throws {
        // From "Adopting unified Maps URLs", read 2026-09-08.
        let documented: Set<String> = [
            "source", "source-place-id", "destination", "destination-place-id",
            "waypoint", "waypoint-place-id", "mode", "avoid", "transit-preferences", "start",
        ]
        let url = try AppleMapsDirections(source: Self.ucla,
                                          destination: Self.malibu,
                                          waypoints: [Self.latigo, Self.piuma]).url()
        for (name, _) in Self.items(url) {
            #expect(documented.contains(name), "\(name) is not a documented /directions parameter")
        }
    }

    @Test("a coordinate is a comma-separated pair at five decimals")
    func coordinateFormat() throws {
        let url = try AppleMapsDirections(destination: Self.ucla).url()
        let value = Self.items(url).first { $0.0 == "destination" }?.1
        #expect(value == "34.06890,-118.44520")
    }

    @Test("waypoints repeat, in the order given, and are not sorted or deduplicated")
    func waypointOrder() throws {
        // NOT a palindrome. The first version of this fixture was [piuma, latigo, piuma], which reads the
        // same forwards and backwards - so `for w in waypoints.reversed()` passed a test named "in the
        // order given". A reviewer found it by mutating the reversal in, and the round-trip test could not
        // help either, because it compares the URL against a reparse of itself.
        //
        // Still deliberately out of geographic order and still with a repeat - the planner may legitimately
        // pin the same junction twice on an out-and-back, and it is not this type's place to decide
        // otherwise - but the repeat is now at one end only, so order is observable.
        let route = [Self.piuma, Self.latigo, Self.latigo, Self.malibu]
        #expect(Array(route.reversed()) != route, "the fixture must be able to detect a reversal")

        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                          waypoints: route).url()
        let pinned = Self.items(url).filter { $0.0 == "waypoint" }.map(\.1)
        #expect(pinned == route.map { try! AppleMapsDirections.pair($0) })
        #expect(pinned.count == 4)
        #expect(pinned.first == (try AppleMapsDirections.pair(Self.piuma)))
        #expect(pinned.last == (try AppleMapsDirections.pair(Self.malibu)))
    }

    @Test("the cap is nine, and the number itself is pinned")
    func capValueIsPinned() {
        // Every other test reaches the cap through `AppleMapsDirections.maxWaypoints`, so raising it from 9
        // to 99 left the whole suite green - the value had no witness. A reviewer found that by mutating it.
        // Nine is OUR choice (Apple documents no maximum), which makes it a decision that should have to be
        // changed deliberately rather than drift.
        #expect(AppleMapsDirections.maxWaypoints == 9)
    }

    @Test("the source is omitted entirely when there is none, rather than sent empty")
    func noSource() throws {
        let url = try AppleMapsDirections(destination: Self.malibu).url()
        #expect(!Self.items(url).contains { $0.0 == "source" })
    }

    @Test("the source carries the origin, under the name Apple documents")
    func sourceValueIsPinned() throws {
        // Of the four things url() emits - source, destination, waypoint, mode - three had a value
        // assertion and source had none. A reviewer showed what that permitted: emitting source under
        // another documented name (`start`, `source-place-id`), or emitting `source=` with the
        // DESTINATION's coordinate. All three passed 30 tests.
        //
        // That last one is a URL telling Apple Maps the drive starts where it ends.
        //
        // The existing tests could not see it. `refusesNonCoordinates` guards only the validation call, so
        // keeping `try Self.pair(source)` leaves the value free. `onlyDocumentedParameters` asserts every
        // emitted name is a MEMBER of the documented set, never which names must appear - it would pass
        // over an empty query string. `roundTrip` compares the URL against a reparse of itself.
        //
        // Literals, not `pair(...)`, so the assertion does not go through the code it is checking.
        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu).url()
        let items = Self.items(url)
        #expect(items.first { $0.0 == "source" }?.1 == "34.06890,-118.44520")
        #expect(items.first { $0.0 == "destination" }?.1 == "34.02590,-118.77980")
        #expect(items.filter { $0.0 == "source" }.count == 1)
        #expect(!items.contains { $0.0 == "start" })
        #expect(!items.contains { $0.0 == "source-place-id" })
    }

    @Test("every parameter the builder must emit is present, not merely permitted")
    func requiredParametersArePresent() throws {
        // `onlyDocumentedParameters` checks membership in the documented set and would be satisfied by an
        // empty query string. This checks the other direction.
        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                          waypoints: [Self.latigo]).url()
        let names = Self.items(url).map(\.0)
        for required in ["source", "destination", "waypoint", "mode"] {
            #expect(names.contains(required), "\(required) is missing from the URL")
        }
    }

    @Test("more waypoints than the cap is refused, not truncated")
    func refusesTruncation() {
        let many = Array(repeating: Self.latigo, count: AppleMapsDirections.maxWaypoints + 1)
        #expect(throws: HandoffError.tooManyWaypoints(count: AppleMapsDirections.maxWaypoints + 1,
                                                      max: AppleMapsDirections.maxWaypoints)) {
            _ = try AppleMapsDirections(destination: Self.malibu, waypoints: many).url()
        }
    }

    @Test("exactly the cap is allowed - an off-by-one here silently drops a decision point")
    func capIsInclusive() throws {
        let atCap = Array(repeating: Self.latigo, count: AppleMapsDirections.maxWaypoints)
        let url = try AppleMapsDirections(destination: Self.malibu, waypoints: atCap).url()
        #expect(Self.items(url).filter { $0.0 == "waypoint" }.count == AppleMapsDirections.maxWaypoints)
    }

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

    @Test("the poles and the antimeridian are coordinates, not errors")
    func edgesAreValid() throws {
        for c in [Coordinate(latitude: 90, longitude: 180),
                  Coordinate(latitude: -90, longitude: -180),
                  Coordinate(latitude: 0, longitude: 0)] {
            #expect(throws: Never.self) { _ = try AppleMapsDirections(destination: c).url() }
        }
    }

    @Test("the coordinate arithmetic rounds, signs, pads and carries correctly")
    func coordinateArithmetic() throws {
        // RENAMED. This was called "the coordinate format consults no locale at all", and a reviewer showed
        // it cannot observe that: a mutant using `Locale.current` passes here, while the same body pinned to
        // de_DE goes red - so the locale path is live and the test simply does not see it. A test whose NAME
        // promises a property nothing checks is the same shape as the finding it replaced, one level up.
        //
        // What it actually pins is the integer arithmetic that replaced the formatter, so that is now its
        // name. The no-locale property is pinned separately, on an identifier, by `noLocaleInTheSource`.
        // The failure: `String(format:)` follows the current locale, so on a German device "34.06890"
        // becomes "34,06890" - a decimal comma inside a comma-separated pair, which Apple Maps reads as four
        // numbers. The first version pinned the formatter to en_US_POSIX and asserted one value; a reviewer
        // mutated the locale to `Locale.current` and the suite stayed green, because CI runs on en_US. The
        // defence was untested by construction.
        //
        // `decimal` now uses integer arithmetic and `String(Int)`, which have no locale to consult. These
        // cases pin the arithmetic that replaced it - the rounding, the negative sign, the zero padding, and
        // the carry - none of which the old one-value assertion covered either.
        for (input, expected) in [(34.0689, "34.06890"),
                                  (-118.4452, "-118.44520"),
                                  (0.0, "0.00000"),
                                  (-0.0, "0.00000"),
                                  (1.000005, "1.00001"),          // rounds up
                                  (1.0000049, "1.00000"),         // rounds down
                                  (89.999999, "90.00000"),        // carries into the whole part
                                  (-179.999999, "-180.00000"),
                                  (0.000001, "0.00000"),
                                  (-0.000004, "0.00000")] {
            let s = AppleMapsDirections.decimal(input)
            #expect(s == expected, "decimal(\(input)) was \(s)")
            #expect(!s.contains(","))
        }
    }

    @Test("the scale is derived from coordinateDecimals, not a literal beside it")
    func scaleFollowsTheConstant() {
        // The assertion the source comment used to point at and that did not exist. `scale` was hardcoded
        // 100_000 while the padding loop read `coordinateDecimals`, so the two could disagree - and at 2
        // decimals the result was 34.6890, a different coordinate about 69 km north rather than a coarser
        // one. Checked as a property of the OUTPUT so it holds however the scale is computed.
        let s = AppleMapsDirections.decimal(34.0689)
        let fraction = s.split(separator: ".").last.map(String.init) ?? ""
        #expect(fraction.count == AppleMapsDirections.coordinateDecimals)
        #expect(AppleMapsDirections.coordinateDecimals == 5)

        // The whole part must not move when the precision does - that is exactly what the mismatch did.
        #expect(s.split(separator: ".").first.map(String.init) == "34")
        #expect(AppleMapsDirections.decimal(-118.4452).split(separator: ".").first.map(String.init) == "-118")
    }

    @Test("no locale is consulted anywhere in the shipping source")
    func noLocaleInTheSource() throws {
        // The property the renamed test could not observe, anchored on identifiers rather than behaviour -
        // which CLAUDE.md permits and prefers over anchoring on a comment. `String(format:)` follows the
        // current locale and is the only way a decimal comma can reach a comma-separated coordinate pair.
        //
        // Deliberately excludes comments: the file discusses `String(format:)` at length to explain why it
        // is gone, and a check that failed on that prose would be anchored on a comment, which is the thing
        // CLAUDE.md forbids.
        let root = URL(fileURLWithPath: #filePath)
            .deletingLastPathComponent()      // HandoffTests
            .deletingLastPathComponent()      // Tests
            .deletingLastPathComponent()      // repo root
            .appendingPathComponent("Sources/Handoff")
        let files = try FileManager.default.contentsOfDirectory(atPath: root.path)
            .filter { $0.hasSuffix(".swift") }
        #expect(files.count >= 2, "expected the Handoff sources; found \(files)")

        for name in files {
            let source = try String(contentsOf: root.appendingPathComponent(name), encoding: .utf8)
            let code = source.split(separator: "\n")
                .filter { !$0.trimmingCharacters(in: .whitespaces).hasPrefix("//") }
                .joined(separator: "\n")
            #expect(!code.contains("String(format:"), "\(name) formats with String(format:)")
            #expect(!code.contains("Locale"), "\(name) mentions Locale outside a comment")
        }
    }

    @Test("the mode is present and driving by default, because this is a car product")
    func mode() throws {
        let url = try AppleMapsDirections(destination: Self.malibu).url()
        #expect(Self.items(url).first { $0.0 == "mode" }?.1 == "driving")
        for m in AppleMapsDirections.Mode.allCases {
            let u = try AppleMapsDirections(destination: Self.malibu, mode: m).url()
            #expect(Self.items(u).first { $0.0 == "mode" }?.1 == m.rawValue)
        }
    }

    @Test("avoid=highways is never emitted")
    func neverAvoidsHighways() throws {
        // CLAUDE.md product invariant: motorway and trunk are penalised, not excluded. The route already
        // decided where the freeway shoulders go; asking Apple to avoid them would re-plan a different
        // drive. This asserts the invariant at the one place it could be violated by a one-line "fix".
        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                          waypoints: [Self.latigo]).url()
        #expect(!Self.items(url).contains { $0.0 == "avoid" })
    }

    @Test("the built URL survives a parse, so nothing is over- or under-encoded")
    func roundTrip() throws {
        let url = try AppleMapsDirections(source: Self.ucla, destination: Self.malibu,
                                          waypoints: [Self.latigo, Self.piuma]).url()
        let reparsed = try #require(URL(string: url.absoluteString))
        #expect(Self.items(reparsed).map(\.1) == Self.items(url).map(\.1))
        // A comma inside a coordinate must reach Apple as a comma. `%2C` here reads as a search string.
        #expect(url.absoluteString.contains("destination=34.02590,-118.77980"))
    }
}
