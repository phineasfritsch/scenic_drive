import PlaceStore
import Testing

/// P-PRIV-05 for the kept corridor slots (T-0343 R6): a stored slot is exactly a cell index, an hour, a ratio and
/// its samples - a WHITELIST of labels and leaf types - and it cannot be handed to an encoder or built by a decoder.
/// Not GRDB-gated.
@Suite("CorridorRatioRecord fields")
struct CorridorRatioRecordFieldsTests {
    @Test("a kept slot is {cell, hour, ratio, samples} and is neither Encodable nor Decodable")
    func fieldsAndNoCodable() {
        let record = CorridorRatioRecord(cell: 617_700_169_958_293_503, hour: 8, ratio: 0.8, samples: 3)
        let fields = Mirror(reflecting: record).children.map { child -> String in
            "\(child.label ?? "?"): \(type(of: child.value))"
        }
        #expect(fields == ["cell: UInt64", "hour: Int", "ratio: Double", "samples: Int"])
        #expect(!(CorridorRatioRecord.self is Encodable.Type))
        #expect(!(CorridorRatioRecord.self is Decodable.Type))
        #expect(!([CorridorRatioRecord].self is Encodable.Type))
    }
}
