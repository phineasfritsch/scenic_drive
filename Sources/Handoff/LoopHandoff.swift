import Foundation
import ScenicKit

/// A loop handed to Apple Maps (T-0314 R8): ONE URL that starts and ends at the loop's start - the ticket's 2-dp
/// start, the coordinate the Worker planned from - with the loop's pinned waypoints between, in order. More than
/// AppleMapsDirections.maxWaypoints is refused by AppleMapsDirections, never truncated.
public enum LoopHandoff {
    public static func directions(start: Coordinate, waypoints: [Coordinate]) -> AppleMapsDirections {
        AppleMapsDirections(source: start, destination: start, waypoints: waypoints)
    }

    public static func url(start: Coordinate, waypoints: [Coordinate]) throws -> URL {
        try directions(start: start, waypoints: waypoints).url()
    }
}
