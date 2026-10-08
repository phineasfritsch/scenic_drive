import Foundation
import ScenicKit

/// A 200 from /trip (services/api/src/tripPlanner.ts TripResult), decoded strictly: a view other than "preview" or
/// "full" is not an itinerary (T-0313 R3). Route points arrive as [lon, lat].
public struct TripResponse: Equatable, Sendable {
    public let isFull: Bool
    public let route: [Coordinate]
    public let distanceMeters: Double
    public let etaSeconds: Double
    public let fastestEtaSeconds: Double
    public let ceilingSeconds: Double
    public let budgetSeconds: Double
    public let extraBudgetPercent: Int
    public let lambda: Double
    public let etaIsEstimate: Bool
    public let days: [TripResponseDay]

    public init(isFull: Bool, route: [Coordinate], distanceMeters: Double, etaSeconds: Double,
                fastestEtaSeconds: Double, ceilingSeconds: Double, budgetSeconds: Double, extraBudgetPercent: Int,
                lambda: Double, etaIsEstimate: Bool, days: [TripResponseDay]) {
        self.isFull = isFull
        self.route = route
        self.distanceMeters = distanceMeters
        self.etaSeconds = etaSeconds
        self.fastestEtaSeconds = fastestEtaSeconds
        self.ceilingSeconds = ceilingSeconds
        self.budgetSeconds = budgetSeconds
        self.extraBudgetPercent = extraBudgetPercent
        self.lambda = lambda
        self.etaIsEstimate = etaIsEstimate
        self.days = days
    }

    /// `[lon, lat]` pairs, in order; a pair of any other length is corrupt.
    static func coordinates(_ pairs: inout UnkeyedDecodingContainer) throws -> [Coordinate] {
        var out: [Coordinate] = []
        while !pairs.isAtEnd {
            let pair = try pairs.decode([Double].self)
            guard pair.count == 2 else {
                throw DecodingError.dataCorruptedError(in: pairs, debugDescription: "a route point is [lon, lat]")
            }
            out.append(Coordinate(latitude: pair[1], longitude: pair[0]))
        }
        return out
    }
}

extension TripResponse: Decodable {
    enum CodingKeys: String, CodingKey {
        case view, route, coordinates, lambda, days
        case distanceMeters = "distance_m"
        case etaSeconds = "eta_s"
        case fastestEtaSeconds = "fastest_eta_s"
        case ceilingSeconds = "ceiling_s"
        case budgetSeconds = "budget_s"
        case extraBudgetPercent = "extra_budget_pct"
        case etaIsEstimate = "eta_is_estimate"
    }

    public init(from decoder: Decoder) throws {
        let top = try decoder.container(keyedBy: CodingKeys.self)
        let view = try top.decode(String.self, forKey: .view)
        guard view == "preview" || view == "full" else {
            throw DecodingError.dataCorruptedError(forKey: .view, in: top, debugDescription: "not preview or full")
        }
        let route = try top.nestedContainer(keyedBy: CodingKeys.self, forKey: .route)
        var pairs = try route.nestedUnkeyedContainer(forKey: .coordinates)
        self.init(isFull: view == "full", route: try Self.coordinates(&pairs),
                  distanceMeters: try route.decode(Double.self, forKey: .distanceMeters),
                  etaSeconds: try top.decode(Double.self, forKey: .etaSeconds),
                  fastestEtaSeconds: try top.decode(Double.self, forKey: .fastestEtaSeconds),
                  ceilingSeconds: try top.decode(Double.self, forKey: .ceilingSeconds),
                  budgetSeconds: try top.decode(Double.self, forKey: .budgetSeconds),
                  extraBudgetPercent: try top.decode(Int.self, forKey: .extraBudgetPercent),
                  lambda: try top.decode(Double.self, forKey: .lambda),
                  etaIsEstimate: try top.decode(Bool.self, forKey: .etaIsEstimate),
                  days: try top.decode([TripResponseDay].self, forKey: .days))
    }
}
