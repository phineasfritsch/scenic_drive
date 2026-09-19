import Foundation

/// A plan that has already been checked: the ETA is inside the ceiling and the route is not the fastest
/// route wearing a lambda. Nothing constructs one of these except `ScenicPlanner.plan`, which is the point
/// - a value that exists is a plan whose invariants held when it was made.
public struct ScenicPlan: Sendable, Equatable {
    public let origin: Coordinate
    public let destination: Coordinate
    public let budget: TimeInterval
    public let fastestDuration: TimeInterval
    public let outcome: BudgetOutcome
    public let distanceMeters: Double
    public let table: PlanTable
    public let waypoints: [Coordinate]
    public let overlapWithFastest: Double

    public init(origin: Coordinate, destination: Coordinate, budget: TimeInterval,
                fastestDuration: TimeInterval, outcome: BudgetOutcome, distanceMeters: Double,
                table: PlanTable, waypoints: [Coordinate], overlapWithFastest: Double) {
        self.origin = origin
        self.destination = destination
        self.budget = budget
        self.fastestDuration = fastestDuration
        self.outcome = outcome
        self.distanceMeters = distanceMeters
        self.table = table
        self.waypoints = waypoints
        self.overlapWithFastest = overlapWithFastest
    }

    /// `fastest + budget`, computed here from the two measured inputs rather than read back out of
    /// `outcome`, for the reason LambdaSearchTests states about its own headline assertion: a bound taken
    /// from the thing under test is not a bound.
    public var ceiling: TimeInterval { fastestDuration + budget }

    /// The report `ops/plan` prints, minus the handoff URL - which is built in Handoff, and ScenicKit does
    /// not know that a URL to a third-party maps app exists.
    ///
    /// Plain text, one fact per line, no colour and no box drawing: this is read in a terminal, pasted into
    /// a task log, and diffed against the next run.
    public func report() -> [String] {
        var lines = [
            "PLAN origin=\(Self.point(origin)) destination=\(Self.point(destination)) "
                + "budget=\(Self.clock(budget))",
            "LAMBDA \(Self.fixed(outcome.lambda, 2)) evaluations=\(outcome.evaluations) "
                + "used-budget=\(outcome.usedBudget) monotonicity-violated=\(outcome.monotonicityViolated)",
            "ETA fastest=\(Self.clock(fastestDuration)) returned=\(Self.clock(outcome.duration)) "
                + "ceiling=\(Self.clock(ceiling)) distance=\(Self.fixed(distanceMeters, 1))m",
            "OVERLAP jaccard=\(Self.fixed(overlapWithFastest, 3)) "
                + "required<\(Self.fixed(RouteDifference.maximumOverlap, 3))",
            "TABLE rows=\(table.rows.count) columns=way,highway,scenic_score,metres,seconds "
                + "(seconds apportioned by metres; the scoring terms are not in the graph)",
        ]
        lines.append(Self.row("WAY", "HIGHWAY", "SCORE", "METRES", "SECONDS"))
        for row in table.rows {
            lines.append(Self.row(
                row.wayId.map(String.init) ?? "-",
                row.highway ?? "-",
                row.scenicScore.map(String.init) ?? "-",
                Self.fixed(row.meters, 1),
                Self.fixed(row.seconds, 1)
            ))
        }
        lines.append("WAYPOINTS \(waypoints.count) of max \(PlanWaypoints.maximum)")
        return lines
    }

    static func row(_ way: String, _ highway: String, _ score: String,
                    _ meters: String, _ seconds: String) -> String {
        pad(way, 12) + pad(highway, 16) + pad(score, 7) + pad(meters, 11) + seconds
    }

    static func pad(_ text: String, _ width: Int) -> String {
        text.count >= width ? text + " " : text + String(repeating: " ", count: width - text.count)
    }

    /// `34.03920,-118.58360` at five decimals - the precision the Apple Maps handoff uses, so the line that
    /// says where the plan started and the URL that reproduces it agree.
    static func point(_ coordinate: Coordinate) -> String {
        "\(fixed(coordinate.latitude, 5)),\(fixed(coordinate.longitude, 5))"
    }

    /// `12m34s`, or `1h02m34s` past an hour. Integer arithmetic, no formatter, no locale - the same reason
    /// AppleMapsDirections spells its own decimals out by hand.
    public static func clock(_ seconds: TimeInterval) -> String {
        let whole = Int(seconds.rounded())
        let hours = whole / 3600
        let minutes = (whole % 3600) / 60
        let remainder = whole % 60
        let mm = minutes < 10 ? "0\(minutes)" : String(minutes)
        let ss = remainder < 10 ? "0\(remainder)" : String(remainder)
        return hours > 0 ? "\(hours)h\(mm)m\(ss)s" : "\(minutes)m\(ss)s"
    }

    /// `value` at exactly `decimals` places, built from integers so no locale can put a comma in it.
    public static func fixed(_ value: Double, _ decimals: Int) -> String {
        guard value.isFinite else { return "\(value)" }
        let scale = (0..<decimals).reduce(1) { acc, _ in acc * 10 }
        let scaled = (value * Double(scale)).rounded()
        let sign = scaled < 0 ? "-" : ""
        let magnitude = Int(abs(scaled))
        if decimals == 0 { return sign + String(magnitude) }
        var digits = String(magnitude % scale)
        while digits.count < decimals { digits = "0" + digits }
        return sign + String(magnitude / scale) + "." + digits
    }
}
