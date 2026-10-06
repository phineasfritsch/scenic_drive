import Foundation

/// The Surprise selector (T-0253): one reachable, open, safe, novel place and why. Pure: the reach, hours,
/// weather and history are the caller's inputs and nothing is fetched. The rulings R1-R8 are in the task Log.
public enum Surprise {
    public static let shownDays = 90
    public static let categoryCorridorDays = 30
    public static let notMyThingDays = 30
    public static let closingMarginMinutes = 45
    public static let explorePercent: UInt64 = 20
    /// T-0283 R1: the time-fit is 100 at this percentage of the dial and falls timeFitSlope a point either side.
    public static let timeFitPeakPercent = 70
    public static let timeFitSlope = 2
    public static let blockedBrands: Set<String> = ["Starbucks", "McDonald's", "In-N-Out Burger", "Denny's",
                                                    "7-Eleven", "Chevron", "Walmart", "Target"]

    /// The one pick for (user, local date, seed) over these inputs, or nil when nothing is eligible (R5).
    public static func pick(candidates: [SurpriseCandidate], reach: SurpriseReach, history: SurpriseHistory,
                            context: SurpriseContext, seed: UInt64) -> SurprisePick? {
        let budget = effectiveBudget(reach: reach, history: history, date: context.date)
        var remaining: [Ranked] = candidates.compactMap { c in
            guard let minutes = reach.roundTripMinutes[c.id] else { return nil }
            guard minutes <= budget else { return nil }
            guard eligible(c, minutes: minutes, history: history, context: context) else { return nil }
            return Ranked(candidate: c, minutes: minutes,
                          score: score(c, minutes: minutes, budget: reach.budgetMinutes, history: history,
                                       date: context.date))
        }
        guard !remaining.isEmpty else { return nil }
        remaining.sort { a, b in a.score != b.score ? a.score > b.score : a.candidate.id < b.candidate.id }
        let target = Int(seed % UInt64(remaining.count))
        var taken = remaining[0]
        for step in 0...target {
            let h = draw(userId: context.userId, date: context.date, step: step)
            let index = h % 100 < explorePercent ? Int((h >> 32) % UInt64(remaining.count)) : 0
            taken = remaining.remove(at: index)
        }
        let c = taken.candidate
        return SurprisePick(candidateId: c.id, name: c.name,
                            reason: SurpriseReason(hook: c.hook, roundTripMinutes: taken.minutes,
                                                   goldenHourLine: goldenHourLine(c, minutes: taken.minutes,
                                                                                  context: context)))
    }

    struct Ranked {
        let candidate: SurpriseCandidate
        let minutes: Int
        let score: Int
    }

    /// R2: whole days from `then` to `today`.
    static func days(_ today: CivilDate, since then: CivilDate) -> Int {
        Int((today.julianDayAtMidnightUTC - then.julianDayAtMidnightUTC).rounded())
    }

    /// R6 tooFar: a same-day "too far" lowers the reach to one minute under the rejected round trip.
    static func effectiveBudget(reach: SurpriseReach, history: SurpriseHistory, date: CivilDate) -> Int {
        var budget = reach.budgetMinutes
        for f in history.feedback where f.reason == .tooFar && days(date, since: f.date) == 0 {
            budget = min(budget, f.roundTripMinutes - 1)
        }
        return budget
    }

    /// R3 filters 2-8 and R6's three exclusions.
    static func eligible(_ c: SurpriseCandidate, minutes: Int, history: SurpriseHistory,
                         context: SurpriseContext) -> Bool {
        let date = context.date
        let arrival = arrivalMinute(minutes, context: context)
        if history.shown.contains(where: { $0.candidateId == c.id && days(date, since: $0.date) < shownDays }) {
            return false
        }
        if history.shown.contains(where: { $0.category == c.category && $0.corridor == c.corridor
            && days(date, since: $0.date) < categoryCorridorDays }) {
            return false
        }
        if let brand = c.brand, blockedBrands.contains(brand) { return false }
        if !c.hoursExempt && !isOpen(c, arrival: arrival) { return false }
        if c.category == .viewpoint && !c.lit && c.unpaved && isAfterDusk(c, arrival: arrival, context: context) {
            return false
        }
        if context.redFlag && c.category.closesOnRedFlag { return false }
        if c.privateApproach { return false }
        for f in history.feedback {
            switch f.reason {
            case .beenThere where f.candidateId == c.id: return false
            case .notMyThing where f.category == c.category && days(date, since: f.date) < notMyThingDays:
                return false
            case .wrongTime where f.candidateId == c.id && days(date, since: f.date) == 0: return false
            default: continue
            }
        }
        return true
    }

    /// R3 (5): open from arrival through arrival + dwell + 45 min, both ends inclusive; unknown hours are closed.
    static func isOpen(_ c: SurpriseCandidate, arrival: Int) -> Bool {
        guard let opens = c.opensMinute, let closes = c.closesMinute else { return false }
        return opens <= arrival && arrival + c.dwellMinutes + closingMarginMinutes <= closes
    }

    /// R2: one way is half the round trip; the local arrival minute.
    static func arrivalMinute(_ roundTrip: Int, context: SurpriseContext) -> Int {
        context.departureMinute + roundTrip / 2
    }

    /// R2: the local minute `minute` on the context's date as a UTC instant.
    static func instant(_ minute: Int, context: SurpriseContext) -> Date {
        context.date.midnightUTC.addingTimeInterval(Double(minute - context.utcOffsetMinutes) * 60)
    }

    /// R3 (6): arriving after civil dusk at the place (Solar); a Sun that never sets to -6 deg is never dark.
    static func isAfterDusk(_ c: SurpriseCandidate, arrival: Int, context: SurpriseContext) -> Bool {
        guard let dusk = SolarEvents.compute(on: context.date, at: c.coordinate).civilDusk else { return false }
        return instant(arrival, context: context) > dusk
    }

    /// R4: quality + approach-road score + novelty + time-fit (T-0283 R1).
    static func score(_ c: SurpriseCandidate, minutes: Int, budget: Int, history: SurpriseHistory,
                      date: CivilDate) -> Int {
        let since = history.shown.filter { $0.category == c.category }.map { days(date, since: $0.date) }
        let novelty = since.min().map { min(100, max(0, $0)) } ?? 100
        return c.quality + c.approachScore + novelty + timeFit(minutes: minutes, budget: budget)
    }

    /// T-0283 R1: 100 at 70% of the dial (the dial's budget, not a lowered one), 2 less a point either side, never
    /// below 0 - a Surprise lands comfortably inside the time you have, not at its edge.
    static func timeFit(minutes: Int, budget: Int) -> Int {
        max(0, 100 - timeFitSlope * abs(minutes * 100 / max(budget, 1) - timeFitPeakPercent))
    }

    /// R5: splitmix64-finalised FNV-1a-64 over "<userId>|<YYYY-MM-DD>|<step>" - the same on every platform.
    static func draw(userId: String, date: CivilDate, step: Int) -> UInt64 {
        let key = "\(userId)|\(pad(date.year, 4))-\(pad(date.month, 2))-\(pad(date.day, 2))|\(step)"
        var h: UInt64 = 0xcbf2_9ce4_8422_2325
        for byte in key.utf8 {
            h = (h ^ UInt64(byte)) &* 0x0000_0100_0000_01b3
        }
        h = (h ^ (h >> 30)) &* 0xbf58_476d_1ce4_e5b9
        h = (h ^ (h >> 27)) &* 0x94d0_49bb_1331_11eb
        return h ^ (h >> 31)
    }

    static func pad(_ value: Int, _ width: Int) -> String {
        let digits = String(value)
        return String(repeating: "0", count: max(0, width - digits.count)) + digits
    }

    /// R7: "Sunset HH:MM - golden hour while you're there" when sunset falls inside [arrival, arrival + dwell].
    static func goldenHourLine(_ c: SurpriseCandidate, minutes: Int, context: SurpriseContext) -> String? {
        guard let sunset = SolarEvents.compute(on: context.date, at: c.coordinate).sunset else { return nil }
        let arrival = arrivalMinute(minutes, context: context)
        let start = instant(arrival, context: context)
        let end = instant(arrival + c.dwellMinutes, context: context)
        guard sunset >= start && sunset <= end else { return nil }
        let utcMinutes = Int((sunset.timeIntervalSince(context.date.midnightUTC) / 60).rounded(.down))
        let local = ((utcMinutes + context.utcOffsetMinutes) % 1440 + 1440) % 1440
        return "Sunset \(pad(local / 60, 2)):\(pad(local % 60, 2)) - golden hour while you're there"
    }
}
