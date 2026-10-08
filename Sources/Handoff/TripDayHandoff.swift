import Foundation
import ScenicKit

/// One road-trip day handed to Apple Maps (T-0313 R6). The day's path is its leg. PINS: walking the path, the first
/// vertex at or past each whole multiple of `pinSpacingMeters` of cumulative distance, never its first or last
/// vertex. SPLIT: while more than `AppleMapsDirections.maxWaypoints` pins remain, a part takes the next nine as
/// waypoints and the tenth as its destination, which is the next part's source; the last part ends at the path's
/// last vertex. Every part has at most nine waypoints, the parts chain end to start, and every pin is used once.
public enum TripDayHandoff {
    public static let pinSpacingMeters = 20_000.0

    public static func pins(along path: [Coordinate]) -> [Coordinate] {
        guard path.count > 2 else { return [] }
        var pins: [Coordinate] = []
        var walked = 0.0
        var next = pinSpacingMeters
        for index in 1..<(path.count - 1) {
            walked += Geo.distanceMeters(path[index - 1], path[index])
            if walked >= next {
                pins.append(path[index])
                while next <= walked { next += pinSpacingMeters }
            }
        }
        return pins
    }

    public static func parts(along path: [Coordinate]) -> [AppleMapsDirections] {
        guard path.count >= 2, let first = path.first, let last = path.last else { return [] }
        let cap = AppleMapsDirections.maxWaypoints
        var remaining = pins(along: path)[...]
        var source = first
        var parts: [AppleMapsDirections] = []
        while remaining.count > cap {
            let stop = remaining[remaining.startIndex + cap]
            parts.append(AppleMapsDirections(source: source, destination: stop, waypoints: Array(remaining.prefix(cap))))
            source = stop
            remaining = remaining.dropFirst(cap + 1)
        }
        parts.append(AppleMapsDirections(source: source, destination: last, waypoints: Array(remaining)))
        return parts
    }

    /// One URL per part, in order, or the first refusal.
    public static func urls(along path: [Coordinate]) throws -> [URL] {
        try parts(along: path).map { try $0.url() }
    }
}
