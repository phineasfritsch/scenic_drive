import PlaceStore
import Testing

/// P-PRIV-05's device half for the Surprise history (T-0312 R9): a stored shown place is exactly a place id, a
/// category, a corridor and a whole day - a WHITELIST of labels and leaf types, so a coordinate, a cell, a time of
/// day or any other field is red until it is ruled. Not GRDB-gated.
@Suite("SurpriseShownRecord fields")
struct SurpriseShownRecordFieldsTests {
    @Test("a stored shown place is {placeID, category, corridor, day}, String and Int leaves only - no coordinate")
    func noFieldIsACoordinate() {
        let record = SurpriseShownRecord(placeID: "1234567", category: "viewpoint", corridor: "pch", day: 20_733)
        let fields = Mirror(reflecting: record).children.map { child -> String in
            let kind = child.value is String ? "String" : child.value is Int ? "Int" : "\(type(of: child.value))"
            return "\(child.label ?? "?"): \(kind)"
        }
        #expect(fields == ["placeID: String", "category: String", "corridor: String", "day: Int"])
    }
}
