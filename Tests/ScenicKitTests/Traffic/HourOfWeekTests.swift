import Foundation
import Testing
@testable import ScenicKit

/// T-0320 R4, R5: the hour of the week, Monday 00:00 = 0 ... Sunday 23:00 = 167, read in the learner's zone.
@Suite("hour of the week (T-0320)") struct HourOfWeekTests {
    @Test("HourOfWeek(_:) holds 0...167 and refuses -1, 168 and the Int extremes")
    func initBounds() {
        for value in [Int.min, -1, 168, Int.max] { #expect(HourOfWeek(value) == nil, "\(value)") }
        for value in [0, 1, 166, 167] { #expect(HourOfWeek(value)?.value == value, "\(value)") }
    }

    @Test("Sunday 23:00 is 167 and wraps to Monday 00:00 = 0; the zone decides the hour")
    func wrapAndZone() {
        let utc = TimeZone(secondsFromGMT: 0)!
        let pacific = TimeZone(secondsFromGMT: -7 * 3600)!
        let rows: [(epoch: TimeInterval, zone: TimeZone, hour: Int)] = [
            (1_791_158_400, utc, 0),        // Monday 2026-10-05 00:00:00Z
            (1_791_158_399, utc, 167),      // one second earlier: Sunday 23:59:59Z
            (1_791_759_600, utc, 167),      // Sunday 2026-10-11 23:00:00Z
            (1_791_763_199, utc, 167),      // Sunday 23:59:59Z
            (1_791_763_200, utc, 0),        // Monday 2026-10-12 00:00:00Z
            (1_791_379_800, utc, 61),       // Wednesday 13:30Z
            (1_791_183_600, utc, 7),        // Monday 07:00Z
            (1_791_183_600, pacific, 0),    // the same instant is Monday 00:00 at UTC-7
            (1_791_158_400, pacific, 161)]  // Monday 00:00Z is Sunday 17:00 at UTC-7
        for row in rows {
            #expect(HourOfWeek.of(Date(timeIntervalSince1970: row.epoch), in: row.zone) == HourOfWeek(row.hour),
                    "\(row.epoch) \(row.zone.secondsFromGMT())")
        }
    }
}
