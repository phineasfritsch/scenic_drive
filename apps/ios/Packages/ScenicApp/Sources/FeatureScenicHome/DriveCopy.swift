import Foundation
import Handoff
import MapAdapter

/// Every user-visible string that belongs to a DRIVE rather than to the screen: its name, its roads,
/// its selector label, and the caption under the map.
///
/// ## Why the road list is a literal and not a rendering of the pins
///
/// `SkylineRoute` and `SantaMonicaMountainsRoute` hold coordinates - no name, no road names. The line
/// below is written by a human from the same reverse geocodes that produced the coordinates, and the
/// road names in it are the `name` fields those queries returned. Changing a drive, renaming it and
/// rewriting its road list are three edits, and nothing but review ties them together; that was true
/// of the one drive `ScenicHomeScreen.Copy` held and it is still true of two.
///
/// ## Why this is a type and not two more cases in the screen's `Copy`
///
/// The screen's `Copy` keeps the strings that are the SCREEN's - the conditions line, the timing line,
/// the map caption's preamble. These are the ones that must change together with a selection, and a
/// `switch` over `HandoffDrive` in one place is what makes "the title, the roads, the distance and the
/// URL all follow the selection" a property somebody can read rather than four call sites to keep in
/// step. A string catalog would be the later home for all of them; it is serial-only (CLAUDE.md) and
/// there is one language today, so the extraction stays mechanical and is not done here.
///
/// No duration in any of these strings. Nobody has driven either route and nothing in this repository
/// has timed one.
enum DriveCopy {
    /// The drive's name, and where it starts and ends - the round trip is the thing a reader has to
    /// know before tapping.
    static func title(for drive: HandoffDrive) -> String {
        switch drive {
        case .skyline:
            return "Skyline loop · starts and ends in San Francisco"
        case .santaMonicaMountains:
            return "Santa Monica Mountains loop · starts and ends in Westwood"
        }
    }

    /// The roads, in the order the drive takes them - the one line on this screen that says where you
    /// would actually be, while the map says nothing. `HandoffFailureCard` shows the same line, because
    /// when the handoff fails the roads are what a reader can still act on.
    static func route(for drive: HandoffDrive) -> String {
        switch drive {
        case .skyline:
            return "I-280 south, Cañada Road north, CA-92 west, Skyline Boulevard south, then back to the city."
        case .santaMonicaMountains:
            return "Sunset Boulevard west, PCH north, Topanga Canyon Boulevard up, the 101 and 405 back over the pass, Mulholland Drive east, down Beverly Glen."
        }
    }

    /// The selector row's label. Short, because two of them share a row at every Dynamic Type size;
    /// the full name is the title directly above.
    static func shortName(for drive: HandoffDrive) -> String {
        switch drive {
        // NAMES ITS PLACE (T-0212). "Bay Area" beside "Los Angeles" read to an LA driver as somebody
        // else's bookmark left in the app; "SF Peninsula" is unmistakably a drive somewhere else
        // rather than a mistake about where the reader is. The picker cannot instead HIDE it: which
        // drive is local is a question about the reader's position, and this app reads none
        // (HandoffDrive.defaultDrive).
        case .skyline: return "SF Peninsula"
        case .santaMonicaMountains: return "Los Angeles"
        }
    }

    /// What is under the header. First clause: what this build is, naming the drive selected, so the
    /// caption cannot say "Bay Area" over the LA loop. Then what the map underneath actually is.
    ///
    /// THE CAPTION FOLLOWS THE RESOLVED STYLE, NEVER THE SELECTION. Selecting the LA drive does not
    /// mean LA tiles are on screen: `BasemapResolver` falls back to `.maplibreDemoTiles` on every
    /// device without `la.pmtiles`, which is every ios-compile run and every phone before the owner
    /// copies the archive in. A caption keyed on the selection would tell that phone it is looking at
    /// roads while it looks at country polygons - the same lie as a credit line keyed on the selection,
    /// which is why `AttributionFooter` reads the same resolved value. Both halves of "what is on
    /// screen" come from the `MapStyle` that was actually resolved.
    ///
    /// Neither case promises a route line: nothing draws one for either drive yet (M4 draws it).
    static func mapCaption(for drive: HandoffDrive, style: MapStyle) -> String {
        let preamble = "Preview build: two fixed drives, \(shortName(for: drive)) selected."
        switch style {
        case .protomapsLALight, .protomapsLADark:
            return "\(preamble) The map shows Los Angeles roads, but not this drive's line yet - tap below and it opens in Apple Maps."
        case .maplibreDemoTiles:
            return "\(preamble) The map doesn't show roads yet - tap below and it opens in Apple Maps."
        }
    }
}
