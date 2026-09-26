import Foundation
import Testing
@testable import ScenicKit

/// P-SAFE-04 over the LA measurement: the extra-time budget is a CEILING - a returned plan's ETA is at most
/// fastest + budget, at every budget, through the REAL bisection (`ScenicPlanner`'s default solver).
///
/// The router here answers T-0244's measured Westwood -> Malibu step table (run1, the adopted per-score band):
/// 1,623,696 ms below lambda 0.5, 1,667,261 ms to 4, 3,578,870 ms to 6, 3,710,979 ms from 6, with car_fast at
/// 1,667,261 ms. A step table is the adversarial case: the bisection brackets a cliff it cannot see across.
@Suite("P-SAFE-04: every plan's ETA <= fastest + budget over the measured LA steps")
struct PlanCeilingOverLATests {

    struct StepRouter: RouteSource {
        var describedSource: String { "t0244 westwood-malibu steps" }

        func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath {
            Self.path(milliseconds: 1_667_261, ways: [1, 2, 3, 4])
        }

        func scenic(from origin: Coordinate, to destination: Coordinate, lambda: Double) throws -> RoutePath {
            switch lambda {
            case ..<0.5: return Self.path(milliseconds: 1_623_696, ways: [1, 2, 3, 5])
            case ..<4: return Self.path(milliseconds: 1_667_261, ways: [1, 2, 3, 4])
            case ..<6: return Self.path(milliseconds: 3_578_870, ways: [11, 12, 13, 14])
            default: return Self.path(milliseconds: 3_710_979, ways: [21, 22, 23, 24])
            }
        }

        static func path(milliseconds: Int, ways: [Int]) -> RoutePath {
            var coordinates: [Coordinate] = []
            var ids: [RoutePath.DetailRun] = []
            for (index, way) in ways.enumerated() {
                coordinates.append(Coordinate(latitude: 34.0 + Double(index) / 100, longitude: -118.5))
                ids.append(RoutePath.DetailRun(from: index, to: index + 1, value: .number(Double(way))))
            }
            coordinates.append(Coordinate(latitude: 34.0 + Double(ways.count) / 100, longitude: -118.5))
            return RoutePath(durationMilliseconds: milliseconds, distanceMeters: 26_776.4,
                             coordinates: coordinates, details: ["osm_way_id": ids])
        }
    }

    @Test("every plan's ETA <= fastest + budget at every whole-minute budget 0..40 over the LA steps")
    func everyPlanStaysUnderTheCeiling() throws {
        let planner = ScenicPlanner(source: StepRouter())
        let origin = Coordinate(latitude: 34.0669, longitude: -118.4399)
        let destination = Coordinate(latitude: 34.0356, longitude: -118.6894)
        var planned: [Int: TimeInterval] = [:]
        for minutes in 0...40 {
            let budget = TimeInterval(minutes * 60)
            do {
                let plan = try planner.plan(from: origin, to: destination, budget: budget)
                #expect(plan.outcome.duration <= 1_667.261 + budget, "budget \(minutes) min returned \(plan.outcome.duration) s")
                planned[minutes] = plan.outcome.duration
            } catch is PlanFailure {
                // A refusal returns no route, so it cannot breach the ceiling.
            } catch is BudgetError {
            }
        }
        // Not vacuous: from +32 min the 59.65-min route fits (3,578.87 <= 1,667.261 + 1,920) and is planned.
        #expect(planned[32] == 3_578.87)
        #expect(planned[40] == 3_710.979)   // from +35 min the 61.85-min route fits too
        #expect(planned.keys.filter { $0 < 32 }.allSatisfy { planned[$0]! <= 1_667.261 + Double($0 * 60) })
    }
}
