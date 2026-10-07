import PlaceStore
import Testing

/// P-PRIV-05's device half for saved drives (T-0290 R7): every leaf of a populated `SavedDrive` is an Int, Int64,
/// String or Bool - a WHITELIST, so a Double, Float, Date or Decimal at any depth, which could carry more than five
/// decimals, is red. Not GRDB-gated.
@Suite("SavedDrive fields")
struct SavedDriveFieldsTests {
    /// Paths of every leaf whose type is outside the whitelist. A nil Optional is a leaf with nothing in it.
    static func offenders(_ value: Any, at path: String) -> [String] {
        switch value {
        case is Int, is Int64, is String, is Bool:
            return []
        default:
            break
        }
        let mirror = Mirror(reflecting: value)
        if mirror.children.isEmpty {
            return mirror.displayStyle == .optional ? [] : ["\(path): \(type(of: value))"]
        }
        return mirror.children.enumerated().flatMap { index, child in
            offenders(child.value, at: path + "." + (child.label ?? String(index)))
        }
    }

    /// Every field set, every container non-empty, so the walk reaches every leaf type the value can hold.
    static func populated() throws -> SavedDrive {
        try SavedDrive(id: 7, name: "Saddle Peak", segments: [
            SavedSegment(segmentID: 101, midpoint: try SavedMidpoint(latitude: 34.09012, longitude: -118.65432)),
            SavedSegment(segmentID: 102, midpoint: try SavedMidpoint(latitude: 34.09234, longitude: -118.65001)),
        ], lambda: 2.5, budgetMinutes: 40, createdAt: 1_790_000_000, needsReplan: true)
    }

    @Test("no field of a populated SavedDrive carries more than 5 dp: every leaf is Int, Int64, String or Bool")
    func noFieldCarriesMoreThanFiveDecimals() throws {
        #expect(Self.offenders(try Self.populated(), at: "SavedDrive") == [])
    }

    @Test("the walk reaches the leaves: a Double, a Date-like Double and a Float nested in an array are named")
    func walkNamesANestedDouble() {
        struct Leaf { let seconds: Double; let count: Int }
        struct Holder { let name: String; let leaves: [Leaf]; let ratio: Float; let maybe: Int64? }
        let holder = Holder(name: "h", leaves: [Leaf(seconds: 1.5, count: 1)], ratio: 0.5, maybe: nil)
        #expect(Self.offenders(holder, at: "Holder") == ["Holder.leaves.0.seconds: Double", "Holder.ratio: Float"])
    }
}
