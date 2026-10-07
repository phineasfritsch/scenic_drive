import Foundation

/// A corpus place row -> the selector's candidate (T-0273 R3). Takes the row's columns as primitives, because
/// ScenicKit never imports PlaceStore; the Surprise card hands each `Place` field straight through.
public enum SurprisePlaceMapping {
    /// No approach data exists offline.
    public static let approachScore = 0

    /// The corridor cell: E7 degrees per 0.1 degree.
    public static let corridorCellE7: Int64 = 1_000_000

    /// The candidate, or nil for an unnamed row or a class outside the ten - never a guess.
    public static func candidate(placeID: Int64, cls: String, name: String?, lonE7: Int64,
                                 latE7: Int64) -> SurpriseCandidate? {
        guard let name, !name.isEmpty, let placeClass = SurprisePlaceClass(rawValue: cls) else { return nil }
        let hours = placeClass.assumedHours
        return SurpriseCandidate(
            id: String(placeID),
            name: name,
            hook: placeClass.hook,
            category: placeClass.category,
            corridor: "\(latE7 / corridorCellE7):\(lonE7 / corridorCellE7)",
            brand: nil,
            coordinate: Coordinate(latitude: Double(latE7) / 10_000_000, longitude: Double(lonE7) / 10_000_000),
            quality: placeClass.priorQuality,
            approachScore: approachScore,
            dwellMinutes: placeClass.dwellMinutes,
            opensMinute: hours?.opens,
            closesMinute: hours?.closes,
            hoursExempt: hours == nil,
            lit: false,
            unpaved: false,
            privateApproach: false
        )
    }
}
