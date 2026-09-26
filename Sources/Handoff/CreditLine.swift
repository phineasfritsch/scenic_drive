import Foundation

/// The ONE credit line a map surface shows: the basemap's credit, then the credit of the data drawn over it
/// (T-0236, rv1-t0236 B1).
///
/// ## Why a drawn line needs its own credit
///
/// The Saddle Peak line is the recorded GraphHopper path over OpenStreetMap - OpenStreetMap data, whatever tiles
/// sit under it. On a device without `la.pmtiles` (every CI run, every phone before the archive is copied in) the
/// basemap is MapLibre's demo, credited "© MapLibre · Natural Earth", and a footer showing only that credit gave
/// the line to nobody. MapLibre's own (i) cannot carry it either: a GeoJSON shape source takes no attribution.
///
/// ## Why the composition lives here, in a Linux target
///
/// So the function the home screen hands `AttributionFooter` is the function `CreditLineTests` calls: the screen
/// passes `CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit)` and nothing else
/// (P-ATTR-01's check whitelists that one form). The parties are joined with the separator the plan's own credit
/// uses, and a party the basemap already names is not repeated - over the LA Protomaps tiles, whose credit already
/// names OpenStreetMap contributors, the line adds nothing and the plan's words stand unchanged.
///
/// ## Why no party can break across lines (T-0237)
///
/// T-0236 round 2's pill wrapped '... Natural Earth · ©' / 'OpenStreetMap contributors': the copyright sign on one
/// line and the party it credits on the next. A line breaks only at a breakable space, so every space INSIDE a
/// party - after the ©, and between the words of a name - is `noBreakSpace`, and the separator's two spaces are the
/// only places the pill can wrap. A screen reader reads the no-break space as a space.
public enum CreditLine {
    /// Between two credited parties, as in the plan's `© OpenStreetMap contributors · Protomaps`.
    public static let separator = " · "

    /// U+00A0, what joins the words inside one party.
    public static let noBreakSpace = "\u{00A0}"

    /// The basemap's credit, then every party of `routeData` the basemap does not already name, each party
    /// `unbroken(_:)`.
    ///
    /// `nil` route data - a drive that draws no line - returns the basemap's own words, and so does route data whose
    /// every party the basemap already names: the same words, in the same order, each party's inner spaces
    /// non-breaking.
    public static func composed(basemap: String, routeData: String?) -> String {
        let base = parties(of: basemap)
        var seen = Set(base.map(identity(of:)))
        var added: [String] = []
        for party in parties(of: routeData ?? "") where seen.insert(identity(of: party)).inserted {
            added.append(party)
        }
        return (base + added).map(unbroken(_:)).joined(separator: separator)
    }

    /// One party with every space made non-breaking, so no line break can fall inside it.
    static func unbroken(_ party: String) -> String {
        party.replacingOccurrences(of: " ", with: noBreakSpace)
    }

    /// A credit's parties, trimmed, empty pieces dropped.
    static func parties(of credit: String) -> [String] {
        credit.components(separatedBy: separator)
            .map { $0.trimmingCharacters(in: .whitespaces) }
            .filter { !$0.isEmpty }
    }

    /// What makes two parties the same one: the text with a leading © and the space around it ignored, so
    /// "© OpenStreetMap contributors" and "OpenStreetMap contributors" are one party and never printed twice.
    static func identity(of party: String) -> String {
        var text = party.trimmingCharacters(in: .whitespaces)
        if text.hasPrefix("©") {
            text.removeFirst()
        }
        return text.trimmingCharacters(in: .whitespaces)
    }
}
