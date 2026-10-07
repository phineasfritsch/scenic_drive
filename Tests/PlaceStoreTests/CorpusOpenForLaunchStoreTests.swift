#if canImport(GRDB)
import Foundation
import PlaceStore
import Testing

/// The PRODUCTION validator (T-0300 O7): `CorpusUpdater(directory:drives:)` swaps a pending corpus in only when the
/// shipping `PlaceStore(path:)` opens it. Each pending file is the shipping build (`python -m etl.corpus`) with at
/// most ONE meta edit; the active one is an untouched shipping build. GRDB-only: CI's linux-core runs it.
struct CorpusOpenForLaunchStoreTests {
    @Test func theSwappedInCorpusMustPassPlaceStoresGate() throws {
        let rows: [(String, String?, CorpusActivation)] = [
            ("a shipping build", nil, .activated),
            ("build_complete 0", "UPDATE meta SET value = '0' WHERE key = 'build_complete'", .rejected),
            ("schema_version bumped", "UPDATE meta SET value = '4' WHERE key = 'schema_version'", .rejected),
        ]
        for (name, sql, outcome) in rows {
            let old = try Data(contentsOf: CorpusFixture.build())
            let new = try Data(contentsOf: sql.map { try CorpusFixture.build(rewriting: $0) } ?? CorpusFixture.build())
            let slots = try CorpusSlotState.scratch()
            try CorpusSlotState(active: old, pending: new).write(to: slots)
            let updater = CorpusUpdater(directory: slots.directory, drives: DriveSessionLock())
            #expect(updater.openForLaunch(isColdLaunch: true) == outcome, "\(name)")
            let after = CorpusSlotState(active: outcome == .activated ? new : old)
            #expect(CorpusSlotState(reading: slots) == after, "\(name)")
            #expect(try PlaceStore(path: slots.active.path).meta().schemaVersion == PlaceStore.schemaVersion)
        }
    }
}
#endif
