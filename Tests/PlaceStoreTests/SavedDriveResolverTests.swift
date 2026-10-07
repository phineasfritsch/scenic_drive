import PlaceStore
import Testing

/// `SavedDriveResolver.resolve(_:against:)` over the whole re-resolve table, both drive variants, each row by FULL
/// equality of the returned SavedDrive (T-0290 R5). Not GRDB-gated; SavedDriveStoreTests runs the same table
/// through the shipped `SavedDriveStore.reresolve(against:)`.
@Suite("SavedDriveResolver")
struct SavedDriveResolverTests {
    @Test("every re-resolve row over both drives: the whole returned drive equals the row's expected drive")
    func table() throws {
        for row in SavedDriveResolveTable.rows {
            for drive in try SavedDriveResolveTable.drives() {
                let input = try row.input(drive)
                let corpus = FakeSavedDriveCorpus(segments: try row.corpus(input))
                #expect(try SavedDriveResolver.resolve(input, against: corpus) == row.expected(input),
                        "\(row.name) / \(drive.name)")
            }
        }
    }

    @Test("meta: no row's corpus or expected drive ignores its input, and the table holds the acceptance's rows")
    func noRowIgnoresItsInput() throws {
        let drives = try SavedDriveResolveTable.drives()
        #expect(drives.count == 2)
        for row in SavedDriveResolveTable.rows {
            let a = try row.input(drives[0])
            let b = try row.input(drives[1])
            #expect(try row.expected(a) != row.expected(b), "\(row.name): expected ignores the input")
            let corpusDiffers = try a.segments.isEmpty ? true : row.corpus(a) != row.corpus(b)
            #expect(corpusDiffers, "\(row.name): corpus ignores the input")
        }
        let names = SavedDriveResolveTable.rows.map(\.name)
        #expect(Set(names).count == names.count)
        for prefix in ["all present", "first moved 24.9 m", "first moved 25.1 m", "first gone", "empty drive"] {
            #expect(names.contains { $0.hasPrefix(prefix) }, "missing row \(prefix)")
        }
    }

    @Test("the expected drives differ from their inputs where the rule changes something")
    func rowsChangeWhatTheyClaim() throws {
        let drive = try SavedDriveResolveTable.drives()[0]
        let changed = try SavedDriveResolveTable.rows.filter { try $0.expected($0.input(drive)) != $0.input(drive) }
        #expect(changed.map(\.name) == [
            "first moved 24.9 m north: replaced; a 24.997 m decoy loses",
            "first moved 25.1 m north: needsReplan, old ids kept",
            "first gone: needsReplan, old ids kept",
            "last moved 24.997 m south: replaced",
            "last moved 25.008 m south: needsReplan",
            "second moved 24 m east at its own latitude: replaced",
            "second moved 24 m west: replaced",
            "tie at one point: the lowest id wins",
            "first resolves, second gone: needsReplan, ALL old ids kept",
        ])
    }
}
