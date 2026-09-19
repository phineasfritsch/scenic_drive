import Foundation
import ScenicKit

/// Which of the two hard-coded drives the screen is showing and the button would hand over.
///
/// ## Why a type and not a second handoff
///
/// The safety gate is a call-graph property: *the handoff is unreachable without the acknowledgement*,
/// flattened by `ops/lib/check-safety-disclaimer` (P-SAFE-03) into "`SkylineHandoff.open(` occurs
/// exactly once in `GatedHandoffButton.swift`, dominated by a guard on the acknowledgement". A second
/// drive added as a second entry point - `SkylineHandoff.laOpen(` beside it - would be a second door
/// with one lock, which is the hole that check exists to refuse. So the drive travels as a VALUE
/// through the one door: the screen holds a `HandoffDrive`, the button carries it, and the single
/// `SkylineHandoff.open(` takes it. Every count the check makes is unchanged by adding a drive, and
/// adding a third one changes none of them either.
///
/// ## Why it lives in `Handoff` and not in the screen
///
/// Both routes' coordinates live here (`SkylineRoute`, `SantaMonicaMountainsRoute`), in a Linux target
/// with a test target beside it. A selector in an Apple-only target with no test bundle could map a
/// case to the wrong array and nothing on this box could tell. `SantaMonicaMountainsChainTests`
/// checks the mapping - `eachDriveMapsToItsOwnRoute`, plus the case count and
/// `defaultDrive` beside it. There is no `HandoffDriveTests` suite; this doc line named one that was
/// never written until 2026-09-19, which is how a reader was told a mapping was covered by a file
/// that did not exist.
public enum HandoffDrive: String, CaseIterable, Sendable {
    /// The walking skeleton's Bay Area loop: `SkylineRoute`.
    case skyline

    /// The owner's Los Angeles loop: `SantaMonicaMountainsRoute`.
    case santaMonicaMountains

    /// What a launch with NOTHING KNOWN shows, which is every launch.
    ///
    /// RULED, because the condition this was asked for cannot be evaluated and saying so is the
    /// honest answer:
    ///
    /// - `Locale.current.region` is a COUNTRY - `US`. There is no region identifier for Southern
    ///   California, so the locale cannot tell Westwood from the Bay Area.
    /// - A last-known coarse position requires CoreLocation authorization. This app has never asked
    ///   for one and must not: `AppleMapsDirections(source: nil, …)` exists precisely so the handoff
    ///   needs no location, CLAUDE.md bans CoreLocation from the Linux targets, and the feature
    ///   targets import DesignSystem, ScenicKit, PlaceStore and their own protocols only.
    ///
    /// So the plan's 5.1.1(iv) "nothing is known" case is the ONLY case, and this is that value. The
    /// owner in Westwood opens the app and sees the LA drive, its roads and its kilometres, with no
    /// permission prompt of any kind. A friend who has denied Location sees exactly the same screen,
    /// because nothing here reads a location to decide - a denial changes nothing - and the Skyline
    /// drive is one 44 pt tap away.
    public static let defaultDrive: HandoffDrive = .santaMonicaMountains

    /// Where this drive ends.
    public var destination: Coordinate {
        switch self {
        case .skyline: return SkylineRoute.destination
        case .santaMonicaMountains: return SantaMonicaMountainsRoute.destination
        }
    }

    /// This drive's pins, in driving order. Read from the route types, never re-typed: the pins have
    /// one home and their provenance lives beside them there.
    public var waypoints: [Coordinate] {
        switch self {
        case .skyline: return SkylineRoute.waypoints
        case .santaMonicaMountains: return SantaMonicaMountainsRoute.waypoints
        }
    }

    /// The pins in driving order, then the destination - the chain `StraightLineDistance` measures.
    public var chain: [Coordinate] { waypoints + [destination] }

    /// This drive as a handoff request: `driving`, no `avoid`, and `source: nil` - "wherever you are",
    /// which is why this app asks for no location permission (`AppleMapsDirections`).
    ///
    /// THE ONE URL BUILDER. `SkylineHandoff.directions(for:)` forwards here, so the URL the button
    /// opens and the URL the clipboard carries are one construction over one drive. A second
    /// `AppleMapsDirections(...)` built beside the copy button would be exactly the drift T-0202 was
    /// filed for: a payload that says one drive while the tap takes another.
    public var directions: AppleMapsDirections {
        AppleMapsDirections(source: nil,
                            destination: destination,
                            waypoints: waypoints,
                            mode: .driving)
    }

    /// The `maps.apple.com/directions` URL for this drive, or the refusal `Handoff` raises -
    /// `HandoffError` distinguishes "too many waypoints" from "that is not a coordinate".
    public func url() throws -> URL { try directions.url() }

    // MARK: - What each surface says about time

    /// Where the real number comes from, as one named clause: the promise the HOME surface makes.
    ///
    /// A constant rather than a clause typed once per drive, because it is the fragment the tests range
    /// over - every drive's `timingSentence` must CONTAIN it and `failureTimingSentence` must not. That
    /// turns "the failure card does not promise a time" into a property `HandoffDriveTimingSentenceTests`
    /// decides on Linux, rather than a sentence a reviewer has to re-read.
    public static let realTimePromise = "Apple Maps gives you the real time when it opens."

    /// The HOME screen's timing sentence for this drive: what KIND of outing this is, in words, and then
    /// where the number comes from.
    ///
    /// NO DIGIT, on either surface. Nobody has driven either route and nothing in this repository has
    /// timed one, so a figure here would be invented. The words live in THIS target, beside a test
    /// bundle, and not in `DriveFacts`: the feature target has no test bundle and no compiler on the
    /// authoring box, so a number typed into a literal over there ships with every gate green (the
    /// pre-review mutant pass's M3a did exactly that). `DriveFacts` renders this property; there is no
    /// second literal in the Apple-only target for it to drift from.
    ///
    /// Per drive, because the two are not the same outing: the Peninsula loop's straight line is more
    /// than twice the LA loop's (112 km of chain against 47), so it is the longer of the two. That
    /// ORDERING is the only claim made. "runs further than the LA loop" was withdrawn 2026-09-19: on
    /// screen, directly beneath a straight-line figure, "runs further" reads as a driving distance, and
    /// no road distance for either drive has been measured by anything in this repository.
    public var timingSentence: String {
        switch self {
        case .santaMonicaMountains:
            return "Plan an afternoon - about 3 hours - not a commute. " + Self.realTimePromise
        case .skyline:
            return "Plan a long afternoon, not a commute - the longer of the two drives. "
                + Self.realTimePromise
        }
    }

    /// The FAILURE CARD's timing sentence - a different sentence, on purpose.
    ///
    /// `timingSentence` ends in a promise that surface cannot keep: the card is on screen precisely
    /// because Apple Maps did not open. Making the card echo the home sentence is a one-line edit in a
    /// target nothing can test (the pass's M3b), so both sentences are properties of this type and
    /// `HandoffDriveTimingSentenceTests` requires, for every case, that they differ, that neither carries
    /// a digit, and that this one does not carry `realTimePromise`.
    public var failureTimingSentence: String {
        timingSentence
    }

    /// The drive as text somebody can paste, composed from this drive's own URL.
    ///
    /// The caller passes the three sentences it renders (the feature target owns the words); the ORDER
    /// is decided here, in a Linux target with a test bundle, because the order is the property T-0202
    /// is about and an Apple-only target has nothing that can check it.
    public func clipboardPayload(roadList: String, straightLine: String, timing: String) -> String {
        Self.payload(mapsURL: try? url(),
                     roadList: roadList,
                     straightLine: straightLine,
                     timing: timing)
    }

    /// THE PAYLOAD, AND ITS ORDER: the `maps.apple.com` URL FIRST, then the roads, the straight line
    /// and the timing sentence, one per line.
    ///
    /// The URL leads because a paste into Messages or Notes makes its first line the tappable thing -
    /// the whole answer to "paste it where?". The other three follow in the order the screen shows
    /// them, and the timing sentence travels with the distance because a bare distance in a message is
    /// read as an ETA.
    ///
    /// `mapsURL` is optional rather than thrown: when the URL cannot be built there is still a drive
    /// worth pasting, and a refusal here would hand the reader an empty clipboard on the one screen
    /// that exists because something already failed.
    public static func payload(mapsURL: URL?,
                               roadList: String,
                               straightLine: String,
                               timing: String) -> String {
        var lines: [String] = []
        if let mapsURL {
            lines.append(mapsURL.absoluteString)
        }
        lines.append(contentsOf: [roadList, straightLine, timing])
        return lines.joined(separator: "\n")
    }
}
