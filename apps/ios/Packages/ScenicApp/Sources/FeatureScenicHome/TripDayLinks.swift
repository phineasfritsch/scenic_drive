import Foundation
import Handoff
import ScenicKit

/// The per-day Apple Maps links for a road-trip day's path (T-0313 R6), for the shell to hand the plan sheet - that
/// target cannot see Handoff, and this one already does. A path Handoff refuses gives no link.
public enum TripDayLinks {
    public static func urls(_ path: [Coordinate]) -> [URL] {
        (try? TripDayHandoff.urls(along: path)) ?? []
    }
}
