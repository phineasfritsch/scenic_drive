import Foundation

/// The hazard strip's words (T-0339): ONE closed table from what the router reported to what the driver reads.
///
/// The strip is the safety half of the product, and a line the driver cannot read is a line they learn to skip -
/// `road_access: destination` is a fact about a database, not a warning. So every hazard the Worker can send has a
/// ruled sentence here (T-0339 R3): what is on the road, then what to do about it, calm and specific, the
/// meaning never softened.
///
/// **Closed, and never widened by guessing.** A run matches a row only exactly - the Worker already lowercases.
/// Anything else reads its kind's fallback, which keeps the safety meaning (still restricted access, still a
/// surface warning), or the generic line when even the kind is unknown. No line ever carries a raw key, value or
/// tag: an unrecognised hazard reaches the screen as "something here needs a closer look", never as nothing and
/// never as a database word.
public enum HazardCopy {
    private static let suits = "on part of this route - check it suits your car"
    private static let through = "on part of this route - you may not be allowed through"

    /// kind -> value -> line: every non-whitelisted value services/api/src/hazards.ts can emit (T-0339 M1).
    public static let runLines: [String: [String: String]] = [
        "surface": [
            "paving_stones": "Paving stones on part of this route - expect a slower, rougher ride",
            "cobblestone": "Cobblestones on part of this route - expect a slower, rougher ride",
            "unpaved": "Unpaved road \(suits)",
            "compacted": "Packed dirt \(suits)",
            "fine_gravel": "Fine gravel \(suits)",
            "gravel": "Gravel \(suits)",
            "ground": "Dirt road \(suits)",
            "dirt": "Dirt road \(suits)",
            "grass": "Grass track on part of this route - most cars should not drive it",
            "sand": "Sand on part of this route - cars can get stuck",
            "wood": "Wooden road surface on part of this route - slippery when wet",
            "other": "Unusual road surface \(suits)",
        ],
        "road_access": [
            "destination": "Local traffic only \(through)",
            "customers": "Customers only \(through)",
            "delivery": "Deliveries only \(through)",
            "agricultural": "Farm vehicles only \(through)",
            "forestry": "Forestry vehicles only \(through)",
            "private": "Private road on this route - you may not have permission to drive it",
            "no": "No entry for cars on part of this route - do not drive it",
        ],
    ]

    /// A surface value the table does not list: still a surface warning.
    public static let surfaceFallback = "Road surface we cannot name on part of this route - check it suits your car"
    /// An access value the table does not list: still restricted access.
    public static let accessFallback = "Restricted access on part of this route - check the signs before you drive it"
    /// A kind the table does not know, or a HazardFlag.unrecognised tag.
    public static let genericLine =
        "Something on part of this route needs a closer look - check the road before you drive it"
    /// The strip when the route has no hazard runs.
    public static let noneFlagged = "Nothing unpaved or restricted is flagged on this route."

    /// Whether `run` is one of the table's rows. False is an unknown the strip still shows, as a fallback.
    public static func isKnown(_ run: PlanHazardRun) -> Bool {
        runLines[run.kind]?[run.value] != nil
    }

    /// The line one hazard run reads.
    public static func line(for run: PlanHazardRun) -> String {
        if let line = runLines[run.kind]?[run.value] { return line }
        switch run.kind {
        case "surface": return surfaceFallback
        case "road_access": return accessFallback
        default: return genericLine
        }
    }

    /// The strip: one line per run, in the order the Worker reported them. Nothing is merged or dropped.
    public static func lines(for preview: PlanPreview) -> [String] {
        preview.hazards.map { line(for: $0) }
    }

    /// The line one derived flag reads, its times in `timeZone`.
    public static func line(for flag: HazardFlag, timeZone: TimeZone) -> String {
        switch flag {
        case let .closure(source, until):
            let when = until.map { " until " + format($0, "MMM d, h:mm a", timeZone) } ?? ", no reopening time given"
            let named = source.trimmingCharacters(in: .whitespacesAndNewlines)
            return "Road closed on this route\(when) - " + (named.isEmpty ? "source not named" : "reported by \(named)")
        case .ford:
            return "Ford on this route - the road crosses water; do not drive in if it is deep or flowing"
        case .gate:
            return "Gate on this route - it may be closed or locked"
        case let .noCell(minutes):
            return "No phone signal for about \(minutes) min on this route - tell someone your plans"
        case let .twilightArrival(at):
            return "You arrive after dusk, around \(format(at, "h:mm a", timeZone))"
                + " - expect to drive part of this in the dark"
        case let .surfaceUnknown(km):
            return "Road surface not recorded for \(String(format: "%.1f", km)) km of this route - it may be unpaved"
        case .unrecognised:
            return genericLine
        }
    }

    private static func format(_ date: Date, _ pattern: String, _ timeZone: TimeZone) -> String {
        let formatter = DateFormatter()
        formatter.locale = Locale(identifier: "en_US_POSIX")
        formatter.timeZone = timeZone
        formatter.dateFormat = pattern
        return formatter.string(from: date)
    }
}
