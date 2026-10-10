import Foundation
import ScenicKit

/// POST /search's body (T-0359 R3, R7): the typed text and at most ONE bias coordinate, rounded HERE to two decimals -
/// the server never receives more than one coordinate per action, never more than 2 dp (CLAUDE.md). nil when the
/// Worker would refuse the query or the bias, so nothing is sent.
struct SearchRequestBody: Encodable, Equatable {
    struct Near: Encodable, Equatable {
        let lat: Double
        let lon: Double
    }

    /// The Worker's SEARCH_MAX_QUERY, in UTF-16 code units (JavaScript's String length).
    static let maxQueryUnits = 100

    let q: String
    let near: Near?

    init?(query: String, near: Coordinate?) {
        guard Self.acceptable(query) else { return nil }
        if let near {
            guard let lat = Self.twoDecimals(near.latitude, limit: 90),
                  let lon = Self.twoDecimals(near.longitude, limit: 180) else { return nil }
            self.near = Near(lat: lat, lon: lon)
        } else {
            self.near = nil
        }
        self.q = query
    }

    /// `value` rounded to 2 dp, -0 as 0, or nil when it is not finite or lies outside [-limit, limit].
    static func twoDecimals(_ value: Double, limit: Double) -> Double? {
        guard value.isFinite, value >= -limit, value <= limit else { return nil }
        return (value * 100).rounded() / 100 + 0.0
    }

    /// 1...maxQueryUnits UTF-16 units, not whitespace only (JavaScript's trim set, U+FEFF included), no C0 or DEL.
    static func acceptable(_ query: String) -> Bool {
        let units = query.utf16.count
        guard units >= 1, units <= maxQueryUnits else { return false }
        let scalars = query.unicodeScalars
        guard !scalars.contains(where: { $0.value < 0x20 || $0.value == 0x7F }) else { return false }
        return !scalars.allSatisfy { $0.properties.isWhitespace || $0.value == 0xFEFF }
    }
}
