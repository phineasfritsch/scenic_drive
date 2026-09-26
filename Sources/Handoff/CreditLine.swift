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
/// names OpenStreetMap contributors, the line adds nothing and the plan's string stands unchanged.
public enum CreditLine {
    /// Between two credited parties, as in the plan's `© OpenStreetMap contributors · Protomaps`.
    public static let separator = " · "

    /// The basemap's credit, then every party of `routeData` the basemap does not already name.
    ///
    /// `nil` route data - a drive that draws no line - returns `basemap` unchanged, character for character, and
    /// so does route data whose every party the basemap already names.
    public static func composed(basemap: String, routeData: String?) -> String {
        guard let routeData else {
            return basemap
        }
        let base = parties(of: basemap)
        var seen = Set(base.map(identity(of:)))
        var added: [String] = []
        for party in parties(of: routeData) where seen.insert(identity(of: party)).inserted {
            added.append(party)
        }
        guard !added.isEmpty else {
            return basemap
        }
        return (base + added).joined(separator: separator)
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
