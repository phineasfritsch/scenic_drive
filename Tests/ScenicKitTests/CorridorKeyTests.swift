import Foundation
import Testing
@testable import ScenicKit

/// `CorridorKey` is two halves and both are load-bearing: *where* (an opaque cell id) and *when* (an hour of
/// the week). A reviewer found that only the *when* half had ever been tested — every assertion in the suite
/// used `cell: 1`, so a `Hashable` that forgot `cell` altogether, and a truncating `cell & 0xFFFF`, both left
/// the whole run green. This file exists so the two halves get equal treatment.
@Suite("Corridor key")
struct CorridorKeyTests {

    // MARK: - the hour half

    @Test("an hour outside the week is not a key")
    func rejectsBadHours() {
        #expect(CorridorKey(cell: 1, hourOfWeek: -1) == nil)
        #expect(CorridorKey(cell: 1, hourOfWeek: 168) == nil)
        #expect(CorridorKey(cell: 1, hourOfWeek: 0) != nil)
        #expect(CorridorKey(cell: 1, hourOfWeek: 167) != nil)
    }

    @Test("Monday is bucket zero regardless of what the calendar calls the first weekday")
    func mondayIsZero() throws {
        // The bug this pins: Calendar.firstWeekday is 1 (Sunday) in en_US and 2 (Monday) in most of Europe.
        // Deriving the bucket from it would bucket the same drive differently for two users, and would
        // re-bucket a user's own history when they travelled.
        var us = Calendar(identifier: .gregorian)
        us.firstWeekday = 1
        us.timeZone = TimeZone(identifier: "UTC")!
        var eu = Calendar(identifier: .gregorian)
        eu.firstWeekday = 2
        eu.timeZone = TimeZone(identifier: "UTC")!

        let monday9am = try Self.instant(year: 2026, month: 9, day: 7, hour: 9)   // 2026-09-07 is a Monday
        let a = try #require(CorridorKey(cell: 1, date: monday9am, calendar: us))
        let b = try #require(CorridorKey(cell: 1, date: monday9am, calendar: eu))
        #expect(a.hourOfWeek == 9)
        #expect(a == b)
    }

    @Test("Sunday is the last day of the week, not the first")
    func sundayIsSix() throws {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "UTC")!
        let sunday = try Self.instant(year: 2026, month: 9, day: 13, hour: 0)     // 2026-09-13 is a Sunday
        let k = try #require(CorridorKey(cell: 1, date: sunday, calendar: cal))
        #expect(k.hourOfWeek == 6 * 24)
    }

    @Test("the bucket is read in the calendar's own time zone, not in UTC")
    func bucketUsesTheCalendarsTimeZone() throws {
        // `mondayIsZero` pins `firstWeekday` but sets BOTH calendars to UTC, and `sundayIsSix` is UTC too.
        // So the half of Calendar that shifts the WEEK was pinned while the half that shifts the DAY was
        // free: forcing `calendar.timeZone = .UTC` inside the initialiser left the entire suite green. That
        // is verbatim the failure `mondayIsZero` exists to prevent, arrived at through the other parameter.
        //
        // Fixed offsets rather than "Australia/Sydney", deliberately: an identifier lookup depends on a
        // tzdata snapshot that differs between this box, Linux CI and a future OS update, and a test whose
        // expected value moves with the host is not a pin. The offsets are the real ones for these dates.

        // Monday 22:00 UTC. In UTC+10 (Sydney in September, before DST) that is TUESDAY 08:00 — the
        // commute this whole type is for, and a different DAY from the UTC reading.
        let mondayNight = try Self.instant(year: 2026, month: 9, day: 7, hour: 22)
        var sydney = Calendar(identifier: .gregorian)
        sydney.timeZone = TimeZone(secondsFromGMT: 10 * 3600)!
        let east = try #require(CorridorKey(cell: 1, date: mondayNight, calendar: sydney))
        #expect(east.hourOfWeek == 32, "Tuesday 08:00 is day 1 hour 8; got \(east.hourOfWeek)")

        // Tuesday 02:00 UTC. In UTC-7 (US Pacific in September, during DST) that is MONDAY 19:00.
        let tuesdayMorning = try Self.instant(year: 2026, month: 9, day: 8, hour: 2)
        var pacific = Calendar(identifier: .gregorian)
        pacific.timeZone = TimeZone(secondsFromGMT: -7 * 3600)!
        let west = try #require(CorridorKey(cell: 1, date: tuesdayMorning, calendar: pacific))
        #expect(west.hourOfWeek == 19, "Monday 19:00 is day 0 hour 19; got \(west.hourOfWeek)")

        // And what UTC would have said about the same two instants, written out, so the failure names itself.
        var utc = Calendar(identifier: .gregorian)
        utc.timeZone = TimeZone(identifier: "UTC")!
        let utcEast = try #require(CorridorKey(cell: 1, date: mondayNight, calendar: utc))
        let utcWest = try #require(CorridorKey(cell: 1, date: tuesdayMorning, calendar: utc))
        #expect(utcEast.hourOfWeek == 22)
        #expect(utcWest.hourOfWeek == 26)
    }

    // MARK: - the cell half

    @Test("the cell id arrives intact, all sixty-four bits of it")
    func cellIsNotTruncated() throws {
        // `self.cell = cell & 0xFFFF` was uncaught: every other assertion in the suite used `cell: 1`, which
        // survives any mask. H3-8 indexes live in the high bits, so a truncating key merges unrelated roads.
        let h3ish = try #require(CorridorKey(cell: 0x8829_a1d6_ffff_ffff, hourOfWeek: 32))
        let biggest = try #require(CorridorKey(cell: UInt64.max, hourOfWeek: 0))
        let smallest = try #require(CorridorKey(cell: 0, hourOfWeek: 0))
        #expect(h3ish.cell == 0x8829_a1d6_ffff_ffff)
        #expect(biggest.cell == UInt64.max)
        #expect(smallest.cell == 0)
    }

    @Test("two cells at the same hour are two different keys, and hash apart")
    func differentCellsAreDifferentKeys() throws {
        // These two differ ONLY above the low sixteen bits, so `cell & 0xFFFF` collapses them onto each
        // other; a hand-written `Hashable` that combines only `hourOfWeek` collapses them too. Equality and
        // hashing are asserted separately because a `==` that agrees with a `hash(into:)` that does not is
        // still a broken dictionary key.
        let freeway = try #require(CorridorKey(cell: 0x8829_a1d6_ffff_ffff, hourOfWeek: 32))
        let backRoad = try #require(CorridorKey(cell: 0x8829_a1d7_ffff_ffff, hourOfWeek: 32))
        #expect(freeway != backRoad)
        #expect(Set([freeway, backRoad]).count == 2)
        #expect(freeway.hourOfWeek == 32)
        #expect(backRoad.hourOfWeek == 32, "same hour: the cell is the only difference")

        // The same cell at the same hour is the same key — the other direction, so the test above cannot be
        // satisfied by a `==` that simply returns false.
        let again = try #require(CorridorKey(cell: 0x8829_a1d6_ffff_ffff, hourOfWeek: 32))
        #expect(freeway == again)
        #expect(Set([freeway, again]).count == 1)
    }

    /// An instant built from UTC wall-clock components, so every expected bucket above can be worked out by
    /// hand from a UTC date and an offset.
    static func instant(year: Int, month: Int, day: Int, hour: Int) throws -> Date {
        var cal = Calendar(identifier: .gregorian)
        cal.timeZone = TimeZone(identifier: "UTC")!
        var comps = DateComponents()
        comps.year = year; comps.month = month; comps.day = day; comps.hour = hour
        comps.timeZone = TimeZone(identifier: "UTC")!
        return try #require(cal.date(from: comps))
    }
}
