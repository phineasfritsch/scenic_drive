import Foundation
import ScenicKit

/// The text `ops/route-autopsy` prints after its ROUTER line: the plan's own headline lines, the lambda
/// trace, the RouteScore terms and one row per table row with its GATE, M, E and score (T-0327).
///
/// Every number is ScenicKit's - the plan and its table from `ScenicPlanner`, the gate from `Gates.decide`,
/// M and E from `SegmentScore.axes(for:)`, the way's score from `SegmentScore.score(for:)`, the route's from
/// `RouteScore(edges:)`. Nothing here weighs, gates or bisects; it formats. Plain text, one fact per line,
/// so it diffs against a golden and pastes into a task Log.
struct AutopsyReport {

    let plan: ScenicPlan
    let steps: [TracingRouteSource.Step]
    let terms: AutopsyTerms?

    /// The router's 0..10 encoded `scenic_score` back to ScoredEdge's 0..1 - ScoredEdge.swift's own rule.
    static let encodedScoreScale = 10.0

    func lines() -> [String] {
        // PLAN, LAMBDA, ETA, OVERLAP: the plan's own words, so the two tools cannot disagree about them.
        var lines = Array(plan.report().prefix(4))
        lines.append("TRACE steps=\(steps.count) ceiling=\(ScenicPlan.clock(plan.ceiling))")
        lines.append(Self.pad("TRY", 6) + Self.pad("N", 4) + Self.pad("LAMBDA", 11) + Self.pad("SECONDS", 13)
            + "FITS")
        for (index, step) in steps.enumerated() {
            lines.append(Self.pad("STEP", 6) + Self.pad(String(index + 1), 4)
                + Self.pad(LambdaCustomModel.multiplier(step.lambda), 11)
                + Self.pad(ScenicPlan.fixed(step.duration, 3), 13)
                + (step.duration <= plan.ceiling ? "yes" : "no"))
        }
        lines.append(routeScoreLine())
        let carried = plan.table.rows.filter { row in row.wayId.flatMap { terms?.ways[$0] } != nil }.count
        lines.append("TERMS source=\(terms?.source ?? "none (--terms not given)") rows-with-terms=\(carried) of "
            + "\(plan.table.rows.count)")
        lines.append("EDGES rows=\(plan.table.rows.count) columns=way,highway,scenic_score,gate,M,E,score,metres,"
            + "seconds")
        lines.append(Self.row(["WAY", "HIGHWAY", "SCENIC", "GATE", "M", "E", "SCORE", "METRES", "SECONDS"]))
        for row in plan.table.rows {
            lines.append(Self.row([row.wayId.map(String.init) ?? "-", row.highway ?? "-",
                                   row.scenicScore.map(String.init) ?? "-"]
                + cells(for: row.wayId.flatMap { terms?.ways[$0] })
                + [ScenicPlan.fixed(row.meters, 1), ScenicPlan.fixed(row.seconds, 1)]))
        }
        return lines
    }

    /// GATE, M, E, score for one way: `-` four times when the terms file does not carry it, and `invalid`
    /// in the three numeric cells when `SegmentScore.score(for:)` refuses its terms (never a clamped number).
    func cells(for way: AutopsyTerms.Way?) -> [String] {
        guard let way else { return ["-", "-", "-", "-"] }
        let gate: String
        switch Gates.decide(way.tags) {
        case .allowed: gate = "allowed"
        case let .refused(reason): gate = "refused:\(reason.rawValue)"
        }
        guard let score = SegmentScore.score(for: way.terms) else { return [gate, "invalid", "invalid", "invalid"] }
        let axes = SegmentScore.axes(for: way.terms)
        return [gate, ScenicPlan.fixed(axes.drive, 3), ScenicPlan.fixed(axes.scenery, 3), ScenicPlan.fixed(score, 3)]
    }

    /// RouteScore over the chosen route as the router scored it, by metres. Rows with no score are left
    /// out and their metres printed, so an unscored stretch cannot pass for a dull one.
    func routeScoreLine() -> String {
        var edges: [ScoredEdge] = []
        var unscored = 0.0
        for row in plan.table.rows where row.meters > 0 {
            if let score = row.scenicScore {
                edges.append(ScoredEdge(length: row.meters, score: Double(score) / Self.encodedScoreScale))
            } else {
                unscored += row.meters
            }
        }
        let tail = " unscored=\(ScenicPlan.fixed(unscored, 1))m"
        guard let route = RouteScore(edges: edges) else { return "ROUTESCORE none" + tail }
        return "ROUTESCORE value=\(ScenicPlan.fixed(route.value, 3)) mean=\(ScenicPlan.fixed(route.mean, 3)) "
            + "p90=\(ScenicPlan.fixed(route.p90, 3)) dud=\(ScenicPlan.fixed(route.dudFraction, 3)) "
            + "episodes=\(route.episodeCount) honest-failure=\(route.isHonestFailure) "
            + "scored=\(ScenicPlan.fixed(route.totalLength, 1))m" + tail
    }

    static let widths = [12, 16, 7, 23, 7, 7, 7, 11]

    static func row(_ cells: [String]) -> String {
        var line = ""
        for (index, cell) in cells.enumerated() {
            line += index < widths.count ? pad(cell, widths[index]) : cell
        }
        return line
    }

    static func pad(_ text: String, _ width: Int) -> String {
        text.count >= width ? text + " " : text + String(repeating: " ", count: width - text.count)
    }
}
