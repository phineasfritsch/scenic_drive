import Foundation

/// The one body POST /ledger takes (T-0302 R3, T-0307 R3): a corpus place id and the H3 resolution-5 cell of the
/// PLACE - never the device's position, which is not a field here. Built only through `init?`, which refuses what
/// ledger.ts parseEntry would refuse on its first tests, so the device never sends it.
public struct LedgerEntry: Equatable, Sendable, Encodable {
    public let placeId: String
    public let cell: String

    /// segid.py place_id: canonical decimal 1 ... 2^63 - 1 (no sign, no leading zero) - ledger.ts PLACE_ID and
    /// MAX_PLACE_ID. The cell: fifteen lowercase hex digits - h3Res5.ts HEX15, its first test; the mode, resolution
    /// and digit tests stay the Worker's (a cell failing them comes back `.invalidRequest`).
    public init?(placeId: String, cell: String) {
        let digits = Array(placeId.utf8)
        guard (1...19).contains(digits.count), digits.allSatisfy({ (48...57).contains($0) }), digits[0] != 48,
              Int64(placeId) != nil else { return nil }
        let hex = Array(cell.utf8)
        guard hex.count == 15, hex.allSatisfy({ (48...57).contains($0) || (97...102).contains($0) }) else {
            return nil
        }
        self.placeId = placeId
        self.cell = cell
    }

    private enum CodingKeys: String, CodingKey {
        case placeId = "place_id"
        case cell
    }
}
