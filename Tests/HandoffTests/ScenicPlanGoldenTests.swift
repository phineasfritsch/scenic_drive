import Foundation
import Testing
import Handoff
import ScenicKit

/// The whole CLI pipeline over a REAL routed response: decode, bisect, check, table, pins, URL.
///
/// ## What the fixture is, exactly
///
/// `Tests/Fixtures/t0182/` holds responses recorded off T-0213's canyon-window GraphHopper 11.0 graph -
/// the same image (`scenic-routing:t0213`), the same shipped jar, the same `graph/properties` sha256
/// (170bfe37...) T-0213 recorded, with the per-request custom models the CLI itself emits. Every number in
/// it is GraphHopper's. The JSON ENVELOPE around those numbers was written by
/// Tests/Fixtures/t0182-recorder/Recorder.java rather than by graphhopper-web, because this slice of the
/// router has no HTTP surface (T-0209 owns it); each fixture says so in its own `recorded.envelope` field.
///
/// Two pairs, and the second is not a spare:
///   * `plan-pair` - Topanga village to PCH at Malibu Canyon, where the window HAS an alternative: 17m56s
///     fastest, 37m33s at lambda >= 6.
///   * `t0213-pair` - T-0213's own pair up Topanga Canyon Boulevard, where it has none. The route is
///     identical at every lambda, and the planner refuses it. That is the actually-different guard failing
///     over REAL data rather than over a stub, which is the only way to know it can fail at all.
@Suite("Scenic plan golden")
struct ScenicPlanGoldenTests {

    static let fixtures = URL(fileURLWithPath: #filePath)   // Tests/HandoffTests/<this file>
        .deletingLastPathComponent()                        // Tests/HandoffTests
        .deletingLastPathComponent()                        // Tests
        .appendingPathComponent("Fixtures/t0182")

    static let origin = Coordinate(latitude: 34.0944, longitude: -118.6013)
    static let destination = Coordinate(latitude: 34.0365, longitude: -118.6870)
    static let budget: TimeInterval = 25 * 60

    static func plan() throws -> ScenicPlan {
        let source = RecordedRouteSource(directory: fixtures.appendingPathComponent("plan-pair"))
        return try ScenicPlanner(source: source).plan(from: origin, to: destination, budget: budget)
    }

    // MARK: - the numbers the router returned

    @Test("the recorded canyon pair plans at lambda 7.75 inside the ceiling")
    func theRecordedPairPlans() throws {
        let plan = try Self.plan()
        // GraphHopper's own milliseconds: 1075693 fastest, 2253369 at lambda >= 6.
        #expect(plan.fastestDuration == 1075.693)
        #expect(plan.outcome.duration == 2253.369)
        #expect(plan.outcome.lambda == 7.75)
        #expect(plan.outcome.evaluations == 6)
        #expect(plan.outcome.usedBudget)
        // The invariant, against a bound this test computes rather than reads back out of the plan.
        #expect(plan.outcome.duration <= 1075.693 + Self.budget)
        // The recorder writes `distance` at three decimals, which is GraphHopper's metres to the
        // millimetre; the report rounds it to one for a person to read.
        #expect(plan.distanceMeters == 33068.866)
    }

    @Test("the report says what the run said")
    func theReportIsTheRunsOutput() throws {
        let lines = try Self.plan().report()
        #expect(lines[1] == "LAMBDA 7.75 evaluations=6 used-budget=true monotonicity-violated=false")
        #expect(lines[2] == "ETA fastest=17m56s returned=37m33s ceiling=42m56s distance=33068.9m")
        #expect(lines[3] == "OVERLAP jaccard=0.112 required<0.600")
        #expect(lines[5] == "WAY         HIGHWAY         SCORE  METRES     SECONDS")
        #expect(lines[6] == "13388359    residential     5      151.9      10.4")
        #expect(lines.last == "WAYPOINTS 9 of max 9")
    }

    // MARK: - the table

    @Test("the table is one row per road under one score, over the real path details")
    func theTableIsBuiltFromTheRealDetails() throws {
        let table = try Self.plan().table
        #expect(table.rows.count == 58)
        let first = try #require(table.rows.first)
        #expect(first.wayId == 13388359)
        #expect(first.highway == "residential")
        #expect(first.scenicScore == 5)
        // The longest row: 9.2 km of tertiary road scored 7 - the reason this route exists.
        let longest = try #require(table.rows.max { $0.meters < $1.meters })
        #expect(longest.wayId == 13346012)
        #expect(longest.highway == "tertiary")
        #expect(longest.scenicScore == 7)
        #expect(abs(longest.meters - 9164.0) < 1.0)
        // Metres from the geometry are within a per-cent of the distance GraphHopper reported for the
        // whole path, which is the check that the rows cover the route rather than part of it.
        let meters = table.rows.reduce(0.0) { $0 + $1.meters }
        #expect(abs(meters - 33068.9) / 33068.9 < 0.01)
        // Seconds sum to the ETA, to the last row.
        let seconds = table.rows.reduce(0.0) { $0 + $1.seconds }
        #expect(abs(seconds - 2253.369) < 0.001)
    }

    // MARK: - the handoff URL

    @Test("the handoff URL pins nine decision points along the recorded route")
    func theURLIsTheRecordedRoute() throws {
        let plan = try Self.plan()
        #expect(plan.waypoints.count == 9)
        let url = try AppleMapsDirections(source: plan.origin, destination: plan.destination,
                                          waypoints: plan.waypoints).url()
        #expect(url.absoluteString == "https://maps.apple.com/directions"
            + "?source=34.09440,-118.60130&destination=34.03650,-118.68700"
            + "&waypoint=34.08350,-118.60162&waypoint=34.07941,-118.60288&waypoint=34.06814,-118.61111"
            + "&waypoint=34.07507,-118.62613&waypoint=34.08375,-118.63666&waypoint=34.08111,-118.64574"
            + "&waypoint=34.07001,-118.65343&waypoint=34.08025,-118.70367&waypoint=34.06937,-118.70790"
            + "&mode=driving")
    }

    @Test("the pin cap ScenicKit picks by is the cap Handoff enforces")
    func theTwoWaypointCapsAgree() {
        // ScenicKit cannot import Handoff - the dependency runs the other way - so the two constants can
        // only be compared here. A plan that selected ten pins would be built, printed, and then refused
        // by `AppleMapsDirections.url()` at the last step.
        #expect(PlanWaypoints.maximum == AppleMapsDirections.maxWaypoints)
    }

    // MARK: - the guard, over real data

    @Test("T-0213's own pair is refused because the canyon has one road")
    func theSingleRoadPairIsRefused() throws {
        // Measured, not assumed: on this pair the recorded response is identical at every lambda the
        // bisection visits (T-0182's Log quotes all seven runs), so ONE evaluation is enough to show the
        // refusal, and only lambda 0 is recorded for it.
        let source = RecordedRouteSource(directory: Self.fixtures.appendingPathComponent("t0213-pair"))
        let planner = ScenicPlanner(source: source, maxEvaluations: 1)
        #expect(throws: PlanFailure.notActuallyDifferent(overlap: 1.0,
                                                         maximum: RouteDifference.maximumOverlap)) {
            try planner.plan(from: Coordinate(latitude: 34.0392, longitude: -118.5836),
                             to: Coordinate(latitude: 34.0944, longitude: -118.6019),
                             budget: Self.budget)
        }
    }

    @Test("an unrecorded lambda is refused rather than answered with a neighbour")
    func anUnrecordedLambdaIsRefused() throws {
        let source = RecordedRouteSource(directory: Self.fixtures.appendingPathComponent("t0213-pair"))
        #expect(throws: PlanFailure.noRecordedResponse(lambda: 4)) {
            _ = try source.scenic(from: Self.origin, to: Self.destination, lambda: 4)
        }
    }
}
