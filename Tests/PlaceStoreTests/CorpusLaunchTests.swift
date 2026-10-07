import Foundation
import PlaceStore
import Testing

/// T-0305 R7: the corpus the app's searches open after a cold launch - the activated download when one exists, else
/// the bundled fallback - through the shipping `LaunchCorpus.open(updater:fallback:)` and `LaunchCorpus.url(fallback:)`.
///
/// One table over the cross product active {absent, present} x pending {none, good, bad} x fallback {nil, a URL}:
/// the acceptance's four states are rows of it - no download (absent, none), pending (good), activated (present,
/// none: an earlier launch activated it), rejected (bad). Each row's expected `CorpusLaunch` is computed from the row
/// by `expected(_:in:)` and compared by FULL equality, and so is what `url(fallback:)` answers afterwards.
/// Serialized: `LaunchCorpus` records one choice per process, as the app does.
@Suite(.serialized)
struct CorpusLaunchTests {
    enum Pending: CaseIterable { case none, good, bad }

    struct Row: CustomStringConvertible {
        let active: Bool
        let pending: Pending
        let fallback: URL?
        var description: String { "active=\(active) pending=\(pending) fallback=\(fallback?.lastPathComponent ?? "-")" }
    }

    static let old = Data("OLD downloaded corpus".utf8)
    static let good = Data("GOOD pending corpus".utf8)
    static let bad = Data("BAD pending corpus".utf8)
    static let bundled = URL(fileURLWithPath: "/bundle/Corpus/corpus-fallback.sqlite")
    static let askedWith = URL(fileURLWithPath: "/bundle/asked-by-a-feature.sqlite")

    static let rows: [Row] = [false, true].flatMap { active in
        Pending.allCases.flatMap { pending in [nil, bundled].map { Row(active: active, pending: pending, fallback: $0) } }
    }

    /// The ruling, stated apart from the code: a pending file is validated (good kept, bad refused); the corpus is
    /// the active slot when a corpus is active after the launch, else the fallback the caller passed.
    static func expected(_ row: Row, in slots: CorpusSlots) -> (launch: CorpusLaunch, asked: URL?, files: CorpusSlotState) {
        let activation: CorpusActivation
        switch row.pending {
        case .none: activation = .noPending
        case .good: activation = .activated
        case .bad: activation = .rejected
        }
        let activeBytes: Data? = row.pending == .good ? good : (row.active ? old : nil)
        let corpus: URL? = activeBytes == nil ? row.fallback : slots.active
        let asked: URL? = activeBytes == nil ? askedWith : slots.active
        return (CorpusLaunch(activation: activation, corpus: corpus), asked, CorpusSlotState(active: activeBytes))
    }

    @Test func launchChoosesTheActivatedCorpusElseTheFallback() throws {
        #expect(Self.rows.count == 12)
        for row in Self.rows {
            let directory = FileManager().temporaryDirectory
                .appendingPathComponent("t0305-launch-\(UUID().uuidString)", isDirectory: true)
            defer { try? FileManager().removeItem(at: directory) }
            let slots = CorpusSlots(directory: directory)
            let pendingBytes: Data? = row.pending == .none ? nil : (row.pending == .good ? Self.good : Self.bad)
            try CorpusSlotState(active: row.active ? Self.old : nil, pending: pendingBytes).write(to: slots)
            let updater = CorpusUpdater(directory: directory, drives: DriveSessionLock(), validate: { url in
                if try Data(contentsOf: url) == Self.bad { throw CocoaError(.fileReadCorruptFile) }
            })
            let launch = LaunchCorpus.open(updater: updater, fallback: row.fallback)
            let asked = LaunchCorpus.url(fallback: Self.askedWith)
            let want = Self.expected(row, in: slots)
            #expect(launch == want.launch, "\(row)")
            #expect(asked == want.asked, "\(row)")
            #expect(CorpusSlotState(reading: slots) == want.files, "\(row)")
        }
    }

    /// The table cannot pass by ignoring a dimension: flipping `active` or `fallback`, or any pending value, changes
    /// the expectation of every row except where the ruling says it may not (a good pending corpus wins whatever was
    /// active, and then the fallback is not read).
    @Test func noLaunchRowIgnoresADimension() {
        let slots = CorpusSlots(directory: URL(fileURLWithPath: "/corpus"))
        for row in Self.rows {
            let base = Self.expected(row, in: slots)
            let flippedActive = Self.expected(Row(active: !row.active, pending: row.pending, fallback: row.fallback), in: slots)
            #expect((flippedActive.files == base.files) == (row.pending == .good), "\(row)")
            let other = Row(active: row.active, pending: row.pending, fallback: row.fallback == nil ? Self.bundled : nil)
            let usesFallback = !row.active && row.pending != .good
            #expect((Self.expected(other, in: slots).launch == base.launch) == !usesFallback, "\(row)")
            for pending in Pending.allCases where pending != row.pending {
                let moved = Self.expected(Row(active: row.active, pending: pending, fallback: row.fallback), in: slots)
                #expect(moved.launch != base.launch, "\(row) -> \(pending)")
            }
        }
    }
}
