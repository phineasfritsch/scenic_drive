import Foundation

/// The "via" line of a route option on the home sheet (T-0408 R4): the roads this option drives that the fastest
/// option does not - the reason to pay its extra minutes - first two, then "+N more". An option that adds no road
/// (the fastest itself) names its own first roads. A road listed twice is named and counted once; no roads at all is
/// an empty line, so a view shows nothing rather than a bare "via".
public enum OptionVia {
    /// How many road names the line spells out before the count.
    public static let named = 2

    public static func line(roads: [String], fastest: [String]) -> String {
        var seen = Set<String>()
        let distinct = roads.filter { seen.insert($0).inserted }
        let added = distinct.filter { !fastest.contains($0) }
        let pool = added.isEmpty ? distinct : added
        guard !pool.isEmpty else { return "" }
        let head = pool.prefix(named)
        let rest = pool.count - head.count
        let text = "via " + head.joined(separator: " · ")
        return rest > 0 ? "\(text) · +\(rest) more" : text
    }
}
