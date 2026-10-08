import Foundation
import ScenicKit
import Testing

/// T-0312 R5 (rv1-t0310 recordable 2): the card's basis/history split as a value. Every operation over every
/// starting state, the WHOLE result by full equality to a recomputation in this file, and a meta-test that no
/// operation's expected value ignores the state it starts from.
@Suite("SurpriseCardHistoryTests") struct SurpriseCardHistoryTests {
    typealias Shown = SurpriseHistory.Shown
    static let today = SurpriseShowingTests.today
    static let yesterday = SurpriseShowingTests.yesterday
    static let older = CivilDate(year: 2026, month: 8, day: 1)
    static let a = SurpriseShowingTests.a
    static let b = SurpriseShowingTests.b
    static let c = SurpriseShowingTests.place("1111111", .cafe, "malibu")
    static let d = SurpriseShowingTests.place("2222222", .beach, "pch")

    static func shown(_ p: SurpriseCandidate, _ date: CivilDate) -> Shown { SurpriseShowingTests.shown(p, date) }
    static func feedback(_ p: SurpriseCandidate, _ reason: SurpriseFeedback.Reason) -> SurpriseFeedback {
        SurpriseFeedback(candidateId: p.id, category: p.category, roundTripMinutes: 60, date: today, reason: reason)
    }

    static let stored = [shown(b, yesterday), shown(d, older), shown(c, today)]

    /// The starting states: what a card can hold - nothing; a place recorded but not yet in the basis; a "not this"
    /// after two showings (basis == history); a restore and a recording on top of it.
    static let variants: [(String, SurpriseCardHistory)] = [
        ("empty", SurpriseCardHistory()),
        ("recorded only", SurpriseCardHistory(history: SurpriseHistory(shown: [shown(a, today)]),
                                              basis: SurpriseHistory())),
        ("declined", SurpriseCardHistory(
            history: SurpriseHistory(shown: [shown(d, yesterday), shown(a, today)], feedback: [feedback(a, .beenThere)]),
            basis: SurpriseHistory(shown: [shown(d, yesterday), shown(a, today)], feedback: [feedback(a, .beenThere)]))),
        ("restored then recorded", SurpriseCardHistory(
            history: SurpriseHistory(shown: [shown(b, yesterday), shown(c, today)], feedback: [feedback(b, .tooFar)]),
            basis: SurpriseHistory(shown: [shown(b, yesterday)], feedback: [feedback(b, .tooFar)]))),
    ]

    /// The test's own union: `first`'s entries, then `then`'s whose (place, day) is not already present.
    static func union(_ first: [Shown], _ then: [Shown]) -> [Shown] {
        var out: [Shown] = []
        for entry in first + then where !out.contains(where: { $0.candidateId == entry.candidateId && $0.date == entry.date }) {
            out.append(entry)
        }
        return out
    }

    /// Each operation and its recomputed expectation as a function of the starting state.
    static let operations: [(String, @Sendable (SurpriseCardHistory) -> SurpriseCardHistory?,
                             @Sendable (SurpriseHistory, SurpriseHistory) -> SurpriseCardHistory?)] = [
        ("showing a new place", { $0.showing(c, on: today) }, { h, b in
            if h.shown.contains(shown(c, today)) { return nil }
            return SurpriseCardHistory(history: SurpriseHistory(shown: h.shown + [shown(c, today)], feedback: h.feedback),
                                       basis: b)
        }),
        ("showing a place yesterday's or today's", { $0.showing(a, on: today) }, { h, b in
            if h.shown.contains(shown(a, today)) { return nil }
            return SurpriseCardHistory(history: SurpriseHistory(shown: h.shown + [shown(a, today)], feedback: h.feedback),
                                       basis: b)
        }),
        ("declining", { $0.declining(feedback(c, .notMyThing)) }, { h, _ in
            let next = SurpriseHistory(shown: h.shown, feedback: h.feedback + [feedback(c, .notMyThing)])
            return SurpriseCardHistory(history: next, basis: next)
        }),
        ("starting over", { $0.startingOver() }, { h, _ in
            SurpriseCardHistory(history: SurpriseHistory(shown: h.shown), basis: SurpriseHistory(shown: h.shown))
        }),
        ("restoring", { $0.restoring(stored) }, { h, b in
            SurpriseCardHistory(history: SurpriseHistory(shown: union(stored, h.shown), feedback: h.feedback),
                                basis: SurpriseHistory(shown: union(stored, b.shown), feedback: b.feedback))
        }),
    ]

    @Test("Every operation over every starting state is its recomputed history and basis, whole")
    func table() {
        for (vname, state) in Self.variants {
            for (oname, operation, expected) in Self.operations {
                #expect(operation(state) == expected(state.history, state.basis), "\(oname) from \(vname)")
            }
        }
    }

    @Test("No operation's expectation ignores the state it starts from")
    func noRowIgnoresItsState() {
        for (oname, _, expected) in Self.operations {
            let results = Self.variants.map { expected($0.1.history, $0.1.basis) }
            let distinct = results.enumerated().filter { i, r in !results.prefix(i).contains(where: { $0 == r }) }
            let required = oname == "showing a place yesterday's or today's" ? 3 : Self.variants.count
            #expect(distinct.count == required, "\(oname): \(distinct.count) distinct")
        }
    }

    static func pick(_ history: SurpriseHistory) -> String? {
        let pool = [a, b, c, d]
        return Surprise.pick(candidates: pool,
                             reach: SurpriseReach(budgetMinutes: 120,
                                                  roundTripMinutes: Dictionary(uniqueKeysWithValues: pool.map { ($0.id, 60) })),
                             history: history,
                             context: SurpriseContext(userId: "u", date: today, departureMinute: 600,
                                                      utcOffsetMinutes: -420, redFlag: false),
                             seed: 0)?.candidateId
    }

    @Test("Recording the place on the card never moves the pick; recording into the basis would")
    func recordingNeverRepicks() {
        var recorded = 0
        for (vname, state) in Self.variants {
            guard let id = Self.pick(state.basis), let place = [Self.a, Self.b, Self.c, Self.d].first(where: { $0.id == id }),
                  let next = state.showing(place, on: Self.today) else { continue }
            recorded += 1
            #expect(next.basis == state.basis, "\(vname): the basis is untouched")
            #expect(Self.pick(next.basis) == id, "\(vname): the card still shows \(id)")
            #expect(Self.pick(next.history) != id, "\(vname): the history it recorded into would re-pick")
        }
        #expect(recorded >= 3, "the invariant ran over most starting states")
    }
}
