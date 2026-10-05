import Foundation

/// The Worker's /isochrone body on the device (T-0262 R7) and the reach Surprise.pick takes from it (T-0262 R8,
/// T-0263): a place's round trip is the `round_trip_minutes` of the SMALLEST bucket whose polygon holds it - inside
/// the outer ring and inside no hole - and a place in no bucket is outside the reach. A port, operation for
/// operation, of services/api/src/surpriseReach.ts roundTripMinutesAt; Tests/Fixtures/t0263 holds both to one answer.
public struct SurpriseIsochrone: Sendable, Equatable, Decodable {
    /// The dial: the request's round-trip minutes, echoed by the Worker.
    public let minutes: Int
    public let buckets: [SurpriseIsochroneBucket]

    public init(minutes: Int, buckets: [SurpriseIsochroneBucket]) {
        self.minutes = minutes
        self.buckets = buckets
    }

    /// The response body, or PlanFailure.malformedResponse when it is not the shape T-0262 R7 rules (R4): a Polygon
    /// of at least one ring, every ring - outer and hole - at least four positions, every position two numbers.
    public static func decode(_ body: Data) throws -> SurpriseIsochrone {
        let decoder = JSONDecoder()
        decoder.keyDecodingStrategy = .convertFromSnakeCase
        let reach: SurpriseIsochrone
        do {
            reach = try decoder.decode(SurpriseIsochrone.self, from: body)
        } catch {
            throw PlanFailure.malformedResponse("the isochrone body does not decode: \(error)")
        }
        for bucket in reach.buckets {
            guard bucket.polygon.type == "Polygon" else {
                throw PlanFailure.malformedResponse("an isochrone bucket is a \(bucket.polygon.type), not a Polygon")
            }
            guard !bucket.polygon.coordinates.isEmpty,
                  bucket.polygon.coordinates.allSatisfy({ $0.count >= 4 }) else {
                throw PlanFailure.malformedResponse("an isochrone polygon has no ring, or a ring short of four positions")
            }
            guard bucket.polygon.coordinates.allSatisfy({ ring in ring.allSatisfy { $0.count >= 2 } }) else {
                throw PlanFailure.malformedResponse("an isochrone position carries fewer than two numbers")
            }
        }
        return reach
    }

    /// The round trip of the smallest bucket holding `point`, or nil when it is outside the reach.
    public func roundTripMinutes(at point: Coordinate) -> Int? {
        var best: Int?
        for bucket in buckets {
            let rings = bucket.polygon.coordinates
            guard let outer = rings.first, Self.inRing(outer, point),
                  !rings.dropFirst().contains(where: { Self.inRing($0, point) }) else { continue }
            if best.map({ bucket.roundTripMinutes < $0 }) ?? true { best = bucket.roundTripMinutes }
        }
        return best
    }

    /// What Surprise.pick takes: the dial as the budget, and each candidate's round trip; a candidate outside
    /// every bucket is absent (R2).
    public func reach(for candidates: [SurpriseCandidate]) -> SurpriseReach {
        var roundTrips: [String: Int] = [:]
        for candidate in candidates {
            if let minutes = roundTripMinutes(at: candidate.coordinate) { roundTrips[candidate.id] = minutes }
        }
        return SurpriseReach(budgetMinutes: minutes, roundTripMinutes: roundTrips)
    }

    /// Even-odd ray casting over a GeoJSON ring of [lon, lat], in the reference's IEEE expression order.
    static func inRing(_ ring: [[Double]], _ point: Coordinate) -> Bool {
        var inside = false
        var j = ring.count - 1
        for i in ring.indices {
            let xi = ring[i][0], yi = ring[i][1], xj = ring[j][0], yj = ring[j][1]
            if (yi > point.latitude) != (yj > point.latitude)
                && point.longitude < (xj - xi) * (point.latitude - yi) / (yj - yi) + xi {
                inside.toggle()
            }
            j = i
        }
        return inside
    }
}
