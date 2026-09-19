import Foundation
import Testing
import ScenicKit
@testable import Handoff

/// What the failure card's Copy button puts on the clipboard, and in what order.
///
/// ## Why this suite exists
///
/// T-0202: the card copied three lines of prose and the reader asked 'paste it where?'. The URL the
/// app already builds is the one line of that payload a friend can tap out of a text message, and a
/// payload whose first line is prose buries it. So the order is the property, and it is pinned here.
///
/// ## Why it binds to `clipboardPayload` and not to the card
///
/// `HandoffFailureCard.clipboardText` is SwiftUI in an Apple-only target with no test bundle and no
/// compiler on the authoring box. Its whole body is one call to `HandoffDrive.clipboardPayload`, which
/// is the shipping symbol production runs and the symbol this suite measures - not a helper beside it
/// and not a literal copied out of it (CLAUDE.md: a test named for a defect binds to the shipping
/// symbol). The same instance method takes its URL from `url()`, which is `directions`, which is what
/// `SkylineHandoff.directions(for:)` forwards to and `SkylineHandoff.open(` leaves through: one
/// builder, so the pasted link and the tapped link cannot be different drives.
@Suite("The clipboard payload of a failed handoff")
struct HandoffDriveClipboardPayloadTests {

    // MARK: - The three sentences the feature target renders, as this suite types them

    static let roads = "Sunset Boulevard west, PCH north, Topanga Canyon Boulevard up."
    static let straightLine = "About 29 miles as the crow flies, pin to pin. The roads are longer."
    static let timing = "Plan an afternoon, not a commute."

    // MARK: - The tests

    @Test("the URL is the FIRST line of the payload, for both drives", arguments: HandoffDrive.allCases)
    func theURLIsTheFirstLine(drive: HandoffDrive) throws {
        let payload = drive.clipboardPayload(roadList: Self.roads,
                                             straightLine: Self.straightLine,
                                             timing: Self.timing)
        let opened = try drive.url().absoluteString
        let first = try #require(payload.split(separator: "\n", omittingEmptySubsequences: false).first)
        #expect(first.hasPrefix("https://maps.apple.com/directions"), "the payload opens with \(first)")
        #expect(String(first) == opened,
                "the pasted URL is not the URL this drive opens: \(first)")
    }

    @Test("the payload is the four lines in order: URL, roads, straight line, timing",
          arguments: HandoffDrive.allCases)
    func thePayloadIsTheFourLinesInOrder(drive: HandoffDrive) throws {
        let payload = drive.clipboardPayload(roadList: Self.roads,
                                             straightLine: Self.straightLine,
                                             timing: Self.timing)
        let opened = try drive.url().absoluteString
        let lines = payload.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
        #expect(lines == [opened, Self.roads, Self.straightLine, Self.timing], "got \(lines)")
    }

    @Test("the URL in the payload is the one the button opens, waypoints and all",
          arguments: HandoffDrive.allCases)
    func theURLIsTheOneTheButtonOpens(drive: HandoffDrive) throws {
        // `directions` is the single builder: the payload's URL and the handoff's URL are the same
        // value, not two constructions that happen to agree today.
        #expect(drive.directions == AppleMapsDirections(source: nil,
                                                        destination: drive.destination,
                                                        waypoints: drive.waypoints,
                                                        mode: .driving))
        let url = try drive.url().absoluteString
        #expect(url.contains("destination="), "no destination in \(url)")
        #expect(url.contains("mode=driving"), "not a driving URL: \(url)")
        #expect(url.components(separatedBy: "waypoint=").count - 1 == drive.waypoints.count,
                "the payload's URL drops waypoints: \(url)")
    }

    @Test("with no URL to paste the three sentences are still there, in order")
    func withNoURLThePayloadIsStillTheThreeSentences() {
        // The composer is total on purpose: the failure card exists because something already failed,
        // and an empty clipboard is the one thing worse than a payload with no link in it.
        let payload = HandoffDrive.payload(mapsURL: nil,
                                           roadList: Self.roads,
                                           straightLine: Self.straightLine,
                                           timing: Self.timing)
        #expect(payload.split(separator: "\n", omittingEmptySubsequences: false).map(String.init)
                == [Self.roads, Self.straightLine, Self.timing], "got \(payload)")
    }
}
