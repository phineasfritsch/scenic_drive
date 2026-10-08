import Foundation

/// What a 422 `nothing_pretty` carries (T-0332): the extra time the driver asked for, and the plan's two offers -
/// "+40" (`moreTimeMinutes`, the budget to re-plan with, nil past the Worker's 180-minute cap) and "all back roads"
/// (`backRoadsEtaSeconds`, that route's real ETA, nil when there is no back-roads route worth offering).
///
/// Read fail-closed, as `PlanResponseReader` reads `resets_at`: every key must be present, every number finite and
/// inside the Worker's own bounds, and `more_time_minutes` must be exactly the budget plus 40. Anything else is not
/// an offer this client can stand behind, and the reader answers `unexpectedResponse` instead.
public struct NothingPrettyOffer: Equatable, Sendable, Decodable {
    /// planRequest.ts MAX_BUDGET_MINUTES.
    public static let maximumBudgetMinutes = 180.0
    /// honestFailure.ts MORE_TIME_MINUTES - the plan's "+40".
    public static let moreTimeMinutes = 40.0

    public let budgetMinutes: Double
    public let moreTimeMinutes: Double?
    public let backRoadsEtaSeconds: Double?

    public init(budgetMinutes: Double, moreTimeMinutes: Double?, backRoadsEtaSeconds: Double?) {
        self.budgetMinutes = budgetMinutes
        self.moreTimeMinutes = moreTimeMinutes
        self.backRoadsEtaSeconds = backRoadsEtaSeconds
    }

    enum CodingKeys: String, CodingKey {
        case budgetMinutes = "budget_minutes"
        case moreTimeMinutes = "more_time_minutes"
        case backRoadsEtaSeconds = "back_roads_eta_s"
    }

    struct Refused: Error {}

    public init(from decoder: Decoder) throws {
        let container = try decoder.container(keyedBy: CodingKeys.self)
        guard container.contains(.moreTimeMinutes), container.contains(.backRoadsEtaSeconds) else { throw Refused() }
        let budget = try container.decode(Double.self, forKey: .budgetMinutes)
        let more = try container.decodeIfPresent(Double.self, forKey: .moreTimeMinutes)
        let backRoads = try container.decodeIfPresent(Double.self, forKey: .backRoadsEtaSeconds)
        guard budget.isFinite, budget >= 0, budget <= Self.maximumBudgetMinutes else { throw Refused() }
        if let more {
            guard more == budget + Self.moreTimeMinutes, more <= Self.maximumBudgetMinutes else { throw Refused() }
        }
        if let backRoads {
            guard backRoads.isFinite, backRoads > 0 else { throw Refused() }
        }
        self.init(budgetMinutes: budget, moreTimeMinutes: more, backRoadsEtaSeconds: backRoads)
    }
}
