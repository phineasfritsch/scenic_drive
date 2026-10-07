@testable import ScenicKit
import Testing

/// T-0306 acceptance 2: the Saved list's state machine (R4) through the shipping symbols the view calls, as one
/// table over EVERY state x EVERY event, each row compared by full equality of the whole SavedList and of what the
/// call returned. A (state, event) pair absent from `moves` must leave the list exactly as it was and return nothing.
@Suite("SavedListTests")
struct SavedListTests {
    static let topanga = SavedRow(id: 1, name: "Topanga loop", createdAt: 1_000, needsReplan: false,
                                  start: Coordinate(latitude: 34.09312, longitude: -118.60071),
                                  end: Coordinate(latitude: 34.04078, longitude: -118.68511), budgetMinutes: 30)
    static let mulholland = SavedRow(id: 2, name: "Mulholland", createdAt: 3_000, needsReplan: false,
                                     start: Coordinate(latitude: 34.13, longitude: -118.4),
                                     end: Coordinate(latitude: 34.5, longitude: -118.9), budgetMinutes: 45)
    static let canyon = SavedRow(id: 3, name: "Old canyon", createdAt: 2_000, needsReplan: true,
                                 start: Coordinate(latitude: 34.2, longitude: -118.3),
                                 end: Coordinate(latitude: 34.25, longitude: -118.35), budgetMinutes: 60)
    /// Newest first.
    static let sorted = [mulholland, canyon, topanga]
    static let matador = PlanPlace(id: 42, name: "El Matador", coordinate: Coordinate(latitude: 34.04, longitude: -118.685))
    /// A place AT the needs-replan canyon's saved end, so replay(3) is refused for needsReplan alone - not for reach.
    static let canyonEnd = PlanPlace(id: 43, name: "Canyon end", coordinate: Coordinate(latitude: 34.25, longitude: -118.35))
    static let places = [matador, canyonEnd]

    enum Event: Equatable {
        case load, beginRename(Int64), editName, commitRename, askDelete(Int64), confirmDelete, cancel, replay(Int64)
        case finishReplay
    }

    enum Outcome: Equatable {
        case quiet
        case edit(SavedEdit)
        case replay(SavedReplay)
    }

    static let events: [Event] = [.load, .beginRename(1), .beginRename(99), .editName, .commitRename, .askDelete(2),
                                  .askDelete(99), .confirmDelete, .cancel, .replay(1), .replay(3), .replay(2),
                                  .finishReplay]

    static let states: [(String, SavedList)] = [
        ("loading", SavedList()),
        ("list", SavedList(rows: sorted, state: .list)),
        ("renaming", SavedList(rows: sorted, state: .renaming(1, "  Sunset loop  "))),
        ("confirmDelete", SavedList(rows: sorted, state: .confirmDelete(2))),
        ("needsReplan", SavedList(rows: sorted, state: .needsReplan(3))),
        ("replaying", SavedList(rows: sorted, state: .replaying(1))),
    ]

    static let renamedTopanga = SavedRow(id: 1, name: "Sunset loop", createdAt: 1_000, needsReplan: false,
                                         start: topanga.start, end: topanga.end, budgetMinutes: 30)
    static let replayTopanga = SavedReplay(id: 1, start: Coordinate(latitude: 34.09, longitude: -118.6),
                                           destination: matador, budgetMinutes: 30)

    /// Every pair that changes something, written out whole. Everything else is "unchanged, quiet".
    static let moves: [String: (SavedList, Outcome)] = {
        var m: [String: (SavedList, Outcome)] = [:]
        for (name, _) in states { m["\(name) load"] = (SavedList(rows: sorted, state: .list), .quiet) }
        m["list beginRename(1)"] = (SavedList(rows: sorted, state: .renaming(1, "Topanga loop")), .quiet)
        m["renaming editName"] = (SavedList(rows: sorted, state: .renaming(1, "Coast")), .quiet)
        m["renaming commitRename"] = (SavedList(rows: [mulholland, canyon, renamedTopanga], state: .list),
                                      .edit(.rename(1, "Sunset loop")))
        m["renaming cancel"] = (SavedList(rows: sorted, state: .list), .quiet)
        m["list askDelete(2)"] = (SavedList(rows: sorted, state: .confirmDelete(2)), .quiet)
        m["confirmDelete confirmDelete"] = (SavedList(rows: [canyon, topanga], state: .list), .edit(.delete(2)))
        m["confirmDelete cancel"] = (SavedList(rows: sorted, state: .list), .quiet)
        m["needsReplan cancel"] = (SavedList(rows: sorted, state: .list), .quiet)
        m["list replay(1)"] = (SavedList(rows: sorted, state: .replaying(1)), .replay(replayTopanga))
        m["list replay(3)"] = (SavedList(rows: sorted, state: .needsReplan(3)), .quiet)
        m["list replay(2)"] = (SavedList(rows: sorted, state: .needsReplan(2)), .quiet)
        m["replaying finishReplay"] = (SavedList(rows: sorted, state: .list), .quiet)
        return m
    }()

    static func apply(_ event: Event, to list: inout SavedList) -> Outcome {
        switch event {
        case .load: list.load([topanga, mulholland, canyon])
        case .beginRename(let id): list.beginRename(id)
        case .editName: list.editName("Coast")
        case .commitRename: return list.commitRename().map(Outcome.edit) ?? .quiet
        case .askDelete(let id): list.askDelete(id)
        case .confirmDelete: return list.confirmDelete().map(Outcome.edit) ?? .quiet
        case .cancel: list.cancel()
        case .replay(let id): return list.replay(id, near: places).map(Outcome.replay) ?? .quiet
        case .finishReplay: list.finishReplay()
        }
        return .quiet
    }

    @Test("every state x every event lands whole: the moves as written, everything else unchanged and quiet")
    func transitions() {
        var seen = Set<String>()
        for (name, start) in Self.states {
            for event in Self.events {
                let key = "\(name) \(event)"
                var list = start
                let got = Self.apply(event, to: &list)
                let (want, wantOutcome) = Self.moves[key] ?? (start, .quiet)
                if Self.moves[key] != nil { seen.insert(key) }
                #expect(list == want, "\(key)")
                #expect(got == wantOutcome, "\(key)")
            }
        }
        #expect(seen == Set(Self.moves.keys), "a written move no (state, event) pair reached")
        #expect(Self.states.count * Self.events.count == 78)
    }

    @Test("rows are kept newest first, a tie broken by the higher id first")
    func newestFirst() {
        let tie = SavedRow(id: 4, name: "Tie", createdAt: 3_000, needsReplan: false, start: nil, end: nil,
                           budgetMinutes: 15)
        var list = SavedList()
        list.load([Self.topanga, tie, Self.canyon, Self.mulholland])
        #expect(list == SavedList(rows: [tie, Self.mulholland, Self.canyon, Self.topanga], state: .list))
    }

    @Test("a rename commits the trimmed name of 1...60 characters and nothing else")
    func renameBounds() {
        let sixty = String(repeating: "a", count: 60)
        // 60 characters of 61 unicode scalars: the last is "e" + U+0301, one Character. The cap counts characters.
        let accented = String(repeating: "a", count: 59) + "e\u{301}"
        let rows: [(String, SavedEdit?)] = [
            ("", nil), ("   ", nil), ("\n\t", nil), ("a", .rename(1, "a")), (" a ", .rename(1, "a")),
            (sixty, .rename(1, sixty)), ("  " + sixty + "  ", .rename(1, sixty)), (sixty + "b", nil),
            (accented, .rename(1, accented)), (accented + "b", nil),
        ]
        for (typed, want) in rows {
            var list = SavedList(rows: Self.sorted, state: .renaming(1, typed))
            let got = list.commitRename()
            #expect(got == want, "\(typed.debugDescription)")
            if case .rename(_, let name) = want {
                let renamed = SavedRow(id: 1, name: name, createdAt: 1_000, needsReplan: false,
                                       start: Self.topanga.start, end: Self.topanga.end, budgetMinutes: 30)
                #expect(list == SavedList(rows: [Self.mulholland, Self.canyon, renamed], state: .list))
            } else {
                #expect(list == SavedList(rows: Self.sorted, state: .renaming(1, typed)), "\(typed.debugDescription)")
            }
        }
    }

    @Test("a refused replay has its own calm copy line")
    func needsReplanCopy() {
        #expect(SavedList.needsReplanLine
                == "The roads on this drive have changed since you saved it. Plan it fresh from the plan sheet.")
    }

    @Test("a drive missing either saved end cannot be replayed and is shown as needing a re-plan")
    func noEnds() {
        let rows: [(String, Coordinate?, Coordinate?)] = [
            ("both", nil, nil), ("start", nil, Self.topanga.end), ("end", Self.topanga.start, nil),
        ]
        for (label, s, e) in rows {
            let bare = SavedRow(id: 9, name: "Bare", createdAt: 5, needsReplan: false, start: s, end: e,
                                budgetMinutes: 15)
            var list = SavedList(rows: [bare], state: .list)
            #expect(list.replay(9, near: Self.places) == nil, "\(label) missing")
            #expect(list == SavedList(rows: [bare], state: .needsReplan(9)), "\(label) missing")
        }
    }

    @Test("P-PRIV-05: the Saved list never shows an address - a row holds no address and draws only its name and detail")
    func neverAnAddress() {
        let labels = Mirror(reflecting: Self.topanga).children.compactMap(\.label)
        #expect(labels == ["id", "name", "createdAt", "needsReplan", "start", "end", "budgetMinutes"])
        #expect(Self.topanga.detail == "30 min extra")
        #expect(Self.canyon.detail == "Needs a re-plan · 60 min extra")
    }
}
