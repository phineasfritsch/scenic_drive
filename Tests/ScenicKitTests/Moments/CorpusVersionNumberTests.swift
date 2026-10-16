@testable import ScenicKit
import Testing

/// T-0361 R8: corpus_activated's version - exactly "YYYYMMDDTHHMMSSZ" is its 14 digits as an Int; every bound of
/// the shape is a row (memory range-checks-every-bound): each digit position at '0' and '9' and one past each side,
/// the length one short and one long, the T and the Z moved, lower-cased or missing.
@Suite("CorpusVersionNumberTests")
struct CorpusVersionNumberTests {
    static let rows: [(String, Int?)] = [
        ("20261006T000000Z", 20_261_006_000_000),
        ("20261006T123456Z", 20_261_006_123_456),
        ("00000000T000000Z", 0),
        ("99999999T999999Z", 99_999_999_999_999),
        ("19700101T235959Z", 19_700_101_235_959),
        ("2026100T000000Z", nil),
        ("202610060T000000Z", nil),
        ("20261006T0000000Z", nil),
        ("20261006T00000Z", nil),
        ("20261006t000000Z", nil),
        ("20261006T000000z", nil),
        ("20261006 000000Z", nil),
        ("20261006T000000", nil),
        ("2026-10-06T00:00Z", nil),
        ("20261006T000000ZZ", nil),
        ("", nil),
        ("2026100６T000000Z", nil),
    ]

    @Test("T-0361 R8: the version of each stamp, whole", arguments: rows)
    func value(_ row: (String, Int?)) {
        #expect(CorpusVersionNumber.value(of: row.0) == row.1)
    }

    @Test("T-0361 R8: a character one below '0' or one above '9' at any digit position is no version")
    func everyDigitBound() {
        let stamp = Array("20261006T000000Z")
        for position in stamp.indices where position != 8 && position != 15 {
            for bad in ["/", ":"] {
                var chars = stamp
                chars[position] = Character(bad)
                #expect(CorpusVersionNumber.value(of: String(chars)) == nil)
            }
            for digit in ["0", "9"] {
                var chars = stamp
                chars[position] = Character(digit)
                var expected = 0
                for (i, c) in chars.enumerated() where i != 8 && i != 15 { expected = expected * 10 + Int(String(c))! }
                #expect(CorpusVersionNumber.value(of: String(chars)) == expected)
            }
        }
    }
}
