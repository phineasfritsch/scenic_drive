import Foundation
import PlaceStore
import Testing

/// Activation through the shipped entry point, `CorpusUpdater.openForLaunch(isColdLaunch:)` (T-0300 O7), with a
/// validator that accepts a file starting "GOOD" - the PlaceStore gate itself is CorpusOpenForLaunchStoreTests,
/// GRDB-only. Rows are functions of the active-corpus variant (an old corpus, or a first install with none); each
/// compares the whole outcome and the whole corpus directory afterwards.
struct CorpusActivationTests {
    struct Row {
        let name: String
        let cold: Bool
        /// "none", "held" (a token alive during the call), "ended" (`end()` before it), "dropped" (deinit before it).
        let drive: String
        let before: CorpusSlotState
        let outcome: CorpusActivation
        let after: CorpusSlotState
    }

    static let old = Data("GOOD corpus v1".utf8)
    static let good = Data("GOOD corpus v2".utf8)
    static let bad = Data("BAD corpus v2".utf8)
    static let halfSwapped = Data("GOOD corpus, swap interrupted".utf8)

    static let validate: @Sendable (URL) throws -> Void = { url in
        guard try Data(contentsOf: url).starts(with: Data("GOOD".utf8)) else {
            throw CocoaError(.fileReadCorruptFile)
        }
    }

    static func rows(_ old: Data?) -> [Row] {
        let staged = CorpusSlotState(active: old, pending: good)
        func row(_ name: String, cold: Bool, drive: String = "none", before: CorpusSlotState = staged,
                 _ outcome: CorpusActivation, _ after: CorpusSlotState) -> Row {
            Row(name: name, cold: cold, drive: drive, before: before, outcome: outcome, after: after)
        }
        return [
            row("cold launch, no drive, a good pending: swapped in", cold: true, .activated,
                CorpusSlotState(active: good)),
            row("warm resume: the old corpus kept, pending kept", cold: false, .deferredWarmLaunch, staged),
            row("cold launch while a drive token is held: old kept, pending kept", cold: true, drive: "held",
                .deferredDriveHeld, staged),
            row("warm resume while a drive token is held: old kept", cold: false, drive: "held",
                .deferredWarmLaunch, staged),
            row("cold launch after the token was ended: swapped in", cold: true, drive: "ended", .activated,
                CorpusSlotState(active: good)),
            row("cold launch after the token was released by deinit: swapped in", cold: true, drive: "dropped",
                .activated, CorpusSlotState(active: good)),
            row("cold launch, the pending file fails validation: swap undone, old kept, pending gone", cold: true,
                before: CorpusSlotState(active: old, pending: bad), .rejected, CorpusSlotState(active: old)),
            row("cold launch, no pending: nothing to do", cold: true, before: CorpusSlotState(active: old),
                .noPending, CorpusSlotState(active: old)),
            row("warm resume, no pending: nothing to do", cold: false, before: CorpusSlotState(active: old),
                .noPending, CorpusSlotState(active: old)),
            row("an interrupted swap left the old corpus in previous, cold: it is restored", cold: true,
                before: CorpusSlotState(active: halfSwapped, previous: old),
                .noPending, CorpusSlotState(active: old ?? halfSwapped)),
            row("an interrupted swap on a warm resume: nothing touched", cold: false,
                before: CorpusSlotState(active: halfSwapped, previous: old),
                .noPending, CorpusSlotState(active: halfSwapped, previous: old)),
            row("an interrupted swap and a pending, cold: restored, then the pending swapped in", cold: true,
                before: CorpusSlotState(active: halfSwapped, pending: good, previous: old), .activated,
                CorpusSlotState(active: good)),
        ]
    }

    static func run(_ old: Data?) throws {
        for row in rows(old) {
            let slots = try CorpusSlotState.scratch()
            try row.before.write(to: slots)
            let drives = DriveSessionLock()
            let updater = CorpusUpdater(directory: slots.directory, drives: drives, validate: validate)
            var token: DriveSessionToken?
            switch row.drive {
            case "held": token = drives.hold()
            case "ended": drives.hold().end()
            case "dropped": _ = drives.hold()
            default: break
            }
            #expect(updater.openForLaunch(isColdLaunch: row.cold) == row.outcome, "\(row.name)")
            #expect(CorpusSlotState(reading: slots) == row.after, "\(row.name)")
            token?.end()
        }
    }

    @Test func activationTableOverAnOldCorpus() throws {
        try Self.run(Self.old)
    }

    @Test func activationTableOnFirstInstall() throws {
        try Self.run(nil)
    }

    /// Rows whose expected directory is the same under both variants, by construction: every one swaps the good
    /// pending file in, after which only it remains.
    static let variantFree: Set<String> = [
        "cold launch, no drive, a good pending: swapped in",
        "cold launch after the token was ended: swapped in",
        "cold launch after the token was released by deinit: swapped in",
        "an interrupted swap and a pending, cold: restored, then the pending swapped in",
    ]

    @Test func noActivationRowIgnoresItsVariant() {
        let x = Self.rows(Self.old)
        let y = Self.rows(nil)
        #expect(x.map(\.name) == y.map(\.name))
        #expect(x.count == 12)
        for (r, s) in zip(x, y) {
            #expect(r.before != s.before, "\(r.name): the same starting directory under both variants")
            if !Self.variantFree.contains(r.name) {
                #expect(r.after != s.after, "\(r.name): the same expected directory under both variants")
            }
        }
        #expect(Self.variantFree.isSubset(of: Set(x.map(\.name))))
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
