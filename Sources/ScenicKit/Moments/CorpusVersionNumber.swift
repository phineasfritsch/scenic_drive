import Foundation

/// corpus_activated's whole-number version (T-0361 R8). A corpus' `meta.corpus_version` is a UTC stamp shaped
/// "YYYYMMDDTHHMMSSZ"; its fourteen digits, read as one Int, are the version (20261006T000000Z -> 20261006000000,
/// below 2^53, so the telemetry double carries it exactly). Any other string has no number and nothing is sent.
public enum CorpusVersionNumber {
    /// The 14 digits of an exact "YYYYMMDDTHHMMSSZ" as an Int; nil for any other string.
    public static func value(of version: String) -> Int? {
        let bytes = Array(version.utf8)
        guard bytes.count == 16, bytes[8] == UInt8(ascii: "T"), bytes[15] == UInt8(ascii: "Z") else { return nil }
        var value = 0
        for (index, byte) in bytes.enumerated() where index != 8 && index != 15 {
            guard byte >= UInt8(ascii: "0"), byte <= UInt8(ascii: "9") else { return nil }
            value = value * 10 + Int(byte - UInt8(ascii: "0"))
        }
        return value
    }
}
