import Foundation

/// A curated, public place Surprise may offer (T-0253 R1). Scores are 0-100 integers; hours are local minutes
/// after midnight, absent when unknown.
public struct SurpriseCandidate: Sendable, Equatable {
    public let id: String
    public let name: String
    public let hook: String
    public let category: SurpriseCategory
    public let corridor: String
    public let brand: String?
    public let coordinate: Coordinate
    public let quality: Int
    public let approachScore: Int
    public let dwellMinutes: Int
    public let opensMinute: Int?
    public let closesMinute: Int?
    public let hoursExempt: Bool
    public let lit: Bool
    public let unpaved: Bool
    public let privateApproach: Bool

    public init(id: String, name: String, hook: String, category: SurpriseCategory, corridor: String,
                brand: String?, coordinate: Coordinate, quality: Int, approachScore: Int, dwellMinutes: Int,
                opensMinute: Int?, closesMinute: Int?, hoursExempt: Bool, lit: Bool, unpaved: Bool,
                privateApproach: Bool) {
        self.id = id
        self.name = name
        self.hook = hook
        self.category = category
        self.corridor = corridor
        self.brand = brand
        self.coordinate = coordinate
        self.quality = quality
        self.approachScore = approachScore
        self.dwellMinutes = dwellMinutes
        self.opensMinute = opensMinute
        self.closesMinute = closesMinute
        self.hoursExempt = hoursExempt
        self.lit = lit
        self.unpaved = unpaved
        self.privateApproach = privateApproach
    }
}
