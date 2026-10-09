import Foundation
import ScenicKit

/// The Worker's 200 body for POST /plan (T-0248 R8), decoded (T-0251 R5).
///
/// `route` arrives as GeoJSON-order `[lon, lat]` pairs and `waypoints` as `{lat, lon}` objects; both become
/// `Coordinate`. `etaIsEstimate` is always true from the server - learned speeds never leave the device, so only
/// the device can clear the estimate badge.
public struct PlanResponse: Equatable, Sendable {
    public let route: [Coordinate]
    public let distanceMeters: Double
    public let etaSeconds: Double
    public let fastestEtaSeconds: Double
    public let ceilingSeconds: Double
    public let budgetSeconds: Double
    public let lambda: Double
    public let evaluations: Int
    public let usedBudget: Bool
    public let etaIsEstimate: Bool
    public let hazards: [PlanHazard]
    public let waypoints: [Coordinate]
    public let appleMapsURL: URL
    /// T-0319 R6: the token the Worker remembered this plan's pins and lambda under; nil when it remembered nothing.
    public let planToken: String?
    /// T-0330 R2/R3: true exactly when the Worker built this answer as the rest of the recalled drive; false on a fresh
    /// plan, and when the field is absent (fail toward saying more: the drive screen notes a new route).
    public let continued: Bool
    /// T-0342 R4: the router's per-edge free-flow times over `route`, whole ms; nil when the Worker sent none.
    public let timeRuns: [CorridorTimeRun]?

    public init(route: [Coordinate], distanceMeters: Double, etaSeconds: Double, fastestEtaSeconds: Double,
                ceilingSeconds: Double, budgetSeconds: Double, lambda: Double, evaluations: Int, usedBudget: Bool,
                etaIsEstimate: Bool, hazards: [PlanHazard], waypoints: [Coordinate], appleMapsURL: URL,
                planToken: String? = nil, continued: Bool = false, timeRuns: [CorridorTimeRun]? = nil) {
        self.route = route
        self.distanceMeters = distanceMeters
        self.etaSeconds = etaSeconds
        self.fastestEtaSeconds = fastestEtaSeconds
        self.ceilingSeconds = ceilingSeconds
        self.budgetSeconds = budgetSeconds
        self.lambda = lambda
        self.evaluations = evaluations
        self.usedBudget = usedBudget
        self.etaIsEstimate = etaIsEstimate
        self.hazards = hazards
        self.waypoints = waypoints
        self.appleMapsURL = appleMapsURL
        self.planToken = planToken
        self.continued = continued
        self.timeRuns = timeRuns
    }
}

extension PlanResponse: Decodable {
    enum CodingKeys: String, CodingKey {
        case route, coordinates, lat, lon, lambda, evaluations, hazards, waypoints, continued, from, to, ms
        case distanceMeters = "distance_m"
        case etaSeconds = "eta_s"
        case fastestEtaSeconds = "fastest_eta_s"
        case ceilingSeconds = "ceiling_s"
        case budgetSeconds = "budget_s"
        case usedBudget = "used_budget"
        case etaIsEstimate = "eta_is_estimate"
        case appleMapsURL = "apple_maps_url"
        case planToken = "plan_token"
        case timeRuns = "time_runs"
    }

    public init(from decoder: Decoder) throws {
        let top = try decoder.container(keyedBy: CodingKeys.self)
        let route = try top.nestedContainer(keyedBy: CodingKeys.self, forKey: .route)
        var pairs = try route.nestedUnkeyedContainer(forKey: .coordinates)
        var coordinates: [Coordinate] = []
        while !pairs.isAtEnd {
            let pair = try pairs.decode([Double].self)
            guard pair.count == 2 else {
                throw DecodingError.dataCorruptedError(in: pairs, debugDescription: "a route point is [lon, lat]")
            }
            coordinates.append(Coordinate(latitude: pair[1], longitude: pair[0]))
        }
        var points = try top.nestedUnkeyedContainer(forKey: .waypoints)
        var waypoints: [Coordinate] = []
        while !points.isAtEnd {
            let point = try points.nestedContainer(keyedBy: CodingKeys.self)
            waypoints.append(Coordinate(latitude: try point.decode(Double.self, forKey: .lat),
                                        longitude: try point.decode(Double.self, forKey: .lon)))
        }
        let timeRuns = try Self.timeRuns(top, over: coordinates)
        let link = try top.decode(String.self, forKey: .appleMapsURL)
        guard let url = URL(string: link) else {
            throw DecodingError.dataCorruptedError(forKey: .appleMapsURL, in: top, debugDescription: "not a URL")
        }
        self.init(
            route: coordinates,
            distanceMeters: try route.decode(Double.self, forKey: .distanceMeters),
            etaSeconds: try top.decode(Double.self, forKey: .etaSeconds),
            fastestEtaSeconds: try top.decode(Double.self, forKey: .fastestEtaSeconds),
            ceilingSeconds: try top.decode(Double.self, forKey: .ceilingSeconds),
            budgetSeconds: try top.decode(Double.self, forKey: .budgetSeconds),
            lambda: try top.decode(Double.self, forKey: .lambda),
            evaluations: try top.decode(Int.self, forKey: .evaluations),
            usedBudget: try top.decode(Bool.self, forKey: .usedBudget),
            etaIsEstimate: try top.decode(Bool.self, forKey: .etaIsEstimate),
            hazards: try top.decode([PlanHazard].self, forKey: .hazards),
            waypoints: waypoints,
            appleMapsURL: url,
            planToken: try top.decodeIfPresent(String.self, forKey: .planToken),
            continued: try top.decodeIfPresent(Bool.self, forKey: .continued) ?? false,
            timeRuns: timeRuns
        )
    }

    /// T-0342 R4: absent is nil; present must be a list of {from, to, ms} integers that CorridorRoute accepts over
    /// `route` - the shipping tiling rule - or the answer is refused. null is refused: the Worker omits, never nulls.
    static func timeRuns(_ top: KeyedDecodingContainer<CodingKeys>, over route: [Coordinate]) throws -> [CorridorTimeRun]? {
        guard top.contains(.timeRuns) else { return nil }
        var list = try top.nestedUnkeyedContainer(forKey: .timeRuns)
        var runs: [CorridorTimeRun] = []
        while !list.isAtEnd {
            let run = try list.nestedContainer(keyedBy: CodingKeys.self)
            runs.append(CorridorTimeRun(from: try run.decode(Int.self, forKey: .from), to: try run.decode(Int.self, forKey: .to),
                                        milliseconds: try run.decode(Int.self, forKey: .ms)))
        }
        guard CorridorRoute(route: route, timeRuns: runs) != nil else {
            throw DecodingError.dataCorruptedError(forKey: .timeRuns, in: top,
                                                   debugDescription: "the time runs do not tile the route")
        }
        return runs
    }
}
