import Foundation
import Handoff
import ScenicKit

/// The Apple Maps link for a loop (T-0314 R8), for the shell to hand the plan sheet - that target cannot see Handoff,
/// and this one already does. Start and end at the loop's start, through its pins; a loop Handoff refuses gives no
/// link.
public enum LoopLinks {
    public static func url(_ start: Coordinate, _ waypoints: [Coordinate]) -> URL? {
        try? LoopHandoff.url(start: start, waypoints: waypoints)
    }
}
