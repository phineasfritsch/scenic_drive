/// Why a saved drive refused a number (T-0290 R4, R4b). No case carries the refused Double: NaN is unequal to
/// itself, and an error must equal itself to be asserted.
public enum SavedDriveError: Error, Equatable, Sendable {
    /// NaN or an infinity.
    case notFinite(SavedDriveField)
    /// Outside the field's inclusive range: latitude [-90, 90], longitude [-180, 180], lambda [0, 1000].
    case outOfRange(SavedDriveField)
    /// Not the double nearest any decimal with five places: it would have to be rounded, and it is not.
    case moreThanFiveDecimals(SavedDriveField)
}
