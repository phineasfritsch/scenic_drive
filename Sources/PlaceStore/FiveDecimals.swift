/// The one gate every Double a saved drive keeps passes through: at most five decimal places, never rounded.
///
/// A Double `value` has at most 5 dp iff it is finite and `(value * 1e5).rounded() / 1e5 == value` - the value is
/// the double nearest the decimal k/100000 - and it is stored as that integer k (T-0290 R4). Checked in order:
/// finite, then the inclusive range, then the decimals; a refusal is a typed `SavedDriveError` naming the field.
/// Nothing here uses GRDB, so this file builds on every toolchain (T-0290 R5).
enum FiveDecimals {
    /// Fixed point 1e-5: the plan's "5-dp midpoints".
    static let scale: Double = 100_000

    static func fixedPoint(_ value: Double, in range: ClosedRange<Double>, field: SavedDriveField) throws -> Int {
        guard value.isFinite else { throw SavedDriveError.notFinite(field) }
        guard range.contains(value) else { throw SavedDriveError.outOfRange(field) }
        let scaled = (value * scale).rounded()
        guard scaled / scale == value else { throw SavedDriveError.moreThanFiveDecimals(field) }
        return Int(scaled)
    }

    /// The double nearest `fixed` / 100000 - the inverse of `fixedPoint` on every value it accepts.
    static func degrees(_ fixed: Int) -> Double {
        Double(fixed) / scale
    }
}
