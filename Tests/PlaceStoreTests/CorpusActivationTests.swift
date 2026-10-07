import Foundation
import PlaceStore
import Testing

/// Activation through the shipped entry point, `CorpusUpdater.openForLaunch(isColdLaunch:)` (T-0300 O7), with a
/// validator that accepts a file starting "GOOD" - the PlaceStore gate itself is CorpusOpenForLaunchStoreTests,
/// GRDB-only. The table is the CROSS PRODUCT of every slot state the two-rename swap can leave - active
/// present/absent x previous present/absent x pending none/good/bad - with every drive state and both launch kinds
/// (rv1-t0300 B1/B2: a hand-picked list never crossed a held drive with an interrupted swap, nor had the crash state
/// {active absent, previous old}). Each row's expected outcome and directory is `expected(_:)` of its inputs, and the
/// run compares the whole outcome and the whole corpus directory afterwards.
struct CorpusActivationTests {
    enum Pending: String, CaseIterable { case none, good, bad }
    /// held: a token alive during the call; ended: `end()` before it; dropped: released by deinit before it.
    enum Drive: String, CaseIterable { case none, held, ended, dropped }

    struct Row: Hashable {
        var active: Bool
        var previous: Bool
        var pending: Pending
        var drive: Drive
        var cold: Bool

        var name: String {
            "active \(active ? "present" : "absent"), previous \(previous ? "present" : "absent"), pending "
                + "\(pending.rawValue), drive \(drive.rawValue), \(cold ? "cold" : "warm") launch"
        }

        var before: CorpusSlotState {
            let staged: Data?
            switch pending {
            case .none: staged = nil
            case .good: staged = CorpusActivationTests.good
            case .bad: staged = CorpusActivationTests.bad
            }
            return CorpusSlotState(active: active ? CorpusActivationTests.inActive : nil, pending: staged,
                                   previous: previous ? CorpusActivationTests.inPrevious : nil)
        }
    }

    /// Distinct bytes per slot, so a rename between any two slots changes the directory a row reads back.
    static let inActive = Data("GOOD corpus in the active slot".utf8)
    static let inPrevious = Data("GOOD corpus in the previous slot".utf8)
    static let good = Data("GOOD corpus v2".utf8)
    static let bad = Data("BAD corpus v2".utf8)

    static let validate: @Sendable (URL) throws -> Void = { url in
        guard try Data(contentsOf: url).starts(with: Data("GOOD".utf8)) else {
            throw CocoaError(.fileReadCorruptFile)
        }
    }

    static let rows: [Row] = {
        var rows: [Row] = []
        for active in [true, false] {
            for previous in [true, false] {
                for pending in Pending.allCases {
                    for drive in Drive.allCases {
                        for cold in [true, false] {
                            rows.append(Row(active: active, previous: previous, pending: pending, drive: drive,
                                            cold: cold))
                        }
                    }
                }
            }
        }
        return rows
    }()

    /// The specification, as a function of the row. A warm launch and a held drive touch nothing - not even an
    /// interrupted swap's previous slot (B1). Otherwise the previous slot is the corpus that was active before an
    /// interrupted swap and is restored first, so the corpus kept on no pending or a refused one is previous ?? active
    /// (B2: with active absent and previous present, a refused pending leaves previous's bytes active).
    static func expected(_ row: Row) -> (CorpusActivation, CorpusSlotState) {
        let before = row.before
        let staged = row.pending != .none
        guard row.cold else { return (staged ? .deferredWarmLaunch : .noPending, before) }
        guard row.drive != .held else { return (staged ? .deferredDriveHeld : .noPending, before) }
        let kept = before.previous ?? before.active
        switch row.pending {
        case .none: return (.noPending, CorpusSlotState(active: kept))
        case .good: return (.activated, CorpusSlotState(active: good))
        case .bad: return (.rejected, CorpusSlotState(active: kept))
        }
    }

    @Test func activationTableOverEverySlotState() throws {
        for row in Self.rows {
            let slots = try CorpusSlotState.scratch()
            try row.before.write(to: slots)
            let drives = DriveSessionLock()
            let updater = CorpusUpdater(directory: slots.directory, drives: drives, validate: Self.validate)
            var token: DriveSessionToken?
            switch row.drive {
            case .held: token = drives.hold()
            case .ended: drives.hold().end()
            case .dropped: _ = drives.hold()
            case .none: break
            }
            let (outcome, after) = Self.expected(row)
            #expect(updater.openForLaunch(isColdLaunch: row.cold) == outcome, "\(row.name)")
            #expect(CorpusSlotState(reading: slots) == after, "\(row.name)")
            token?.end()
        }
    }

    /// The flips of one input that leave a row's expectation unchanged, stated apart from `expected(_:)`: active is
    /// irrelevant on a touching launch when a good pending replaces it or previous is restored over it; previous is
    /// irrelevant on a touching launch only when a good pending replaces both; the drive only on a warm launch or when
    /// the directory holds nothing to move; the launch kind only when nothing is staged and nothing would move.
    static func ignores(_ row: Row, _ dimension: String) -> Bool {
        let touching = row.cold && row.drive != .held
        let nothingToMove = !row.previous && row.pending == .none
        switch dimension {
        case "active": return touching && (row.pending == .good || row.previous)
        case "previous": return touching && row.pending == .good
        case "pending": return false
        case "held": return !row.cold || nothingToMove
        case "cold": return row.pending == .none && (row.drive == .held || !row.previous)
        default: return false
        }
    }

    @Test func noActivationRowIgnoresADimension() {
        let rows = Self.rows
        #expect(rows.count == 2 * 2 * 3 * 4 * 2)
        #expect(Set(rows).count == rows.count)
        #expect(Set(rows.map(\.before)).count == 2 * 2 * 3)
        func same(_ a: Row, _ b: Row) -> Bool { Self.expected(a) == Self.expected(b) }
        for row in rows {
            var flip = row
            flip.active.toggle()
            #expect(same(row, flip) == Self.ignores(row, "active"), "\(row.name): active")
            flip = row
            flip.previous.toggle()
            #expect(same(row, flip) == Self.ignores(row, "previous"), "\(row.name): previous")
            for other in Pending.allCases where other != row.pending {
                flip = row
                flip.pending = other
                #expect(same(row, flip) == Self.ignores(row, "pending"), "\(row.name): pending \(other)")
            }
            flip = row
            flip.cold.toggle()
            #expect(same(row, flip) == Self.ignores(row, "cold"), "\(row.name): cold")
            if row.drive == .held || row.drive == .none {
                flip = row
                flip.drive = row.drive == .held ? .none : .held
                #expect(same(row, flip) == Self.ignores(row, "held"), "\(row.name): held")
            } else {
                flip = row
                flip.drive = .none
                #expect(same(row, flip), "\(row.name): a released token is no drive")
            }
        }
    }

    @Test func aDriveTokenIsHeldUntilItsLastEndOrDeinit() {
        let drives = DriveSessionLock()
        #expect(drives.isHeld == false)
        let first = drives.hold()
        let second = drives.hold()
        #expect(drives.isHeld == true)
        first.end()
        first.end()
        #expect(drives.isHeld == true)
        second.end()
        #expect(drives.isHeld == false)
    }
}
