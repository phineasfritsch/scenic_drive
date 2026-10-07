import PlaceStore

/// One row of the re-resolve table (T-0290 R5): the drive it starts from, the corpus that activates and the whole
/// drive the rule must return - each a FUNCTION of the input drive, so the same row runs over every variant in
/// `SavedDriveResolveTable.drives()` and the meta-test can show that no expected value ignores its input.
struct SavedDriveResolveRow {
    let name: String
    let input: (SavedDrive) throws -> SavedDrive
    let corpus: (SavedDrive) throws -> [Segment]
    let expected: (SavedDrive) throws -> SavedDrive
}
