import Foundation

/// One route on the menu, measured: how much longer than the fastest it takes, how far it is, and how much
/// of it is fun.
///
/// ## Fun, and what is ranked on
///
/// Fun metres are the metres of the route's `PlanTable` rows scored `scenic_score >= 6` (`funScore`) - the
/// same table `ops/plan` prints, so the menu and the plan cannot disagree about which road is which. The
/// menu RANKS on fun metres only (T-0239 R4, the owner's default): fun share and the mean score are shown so
/// a person can see that T4's Latigo route has the most fun km at a lower share, and are never compared.
///
/// ## The extra minutes are a ceiling, not a rounding
///
/// `extraTenths` is (duration - fastest) in tenths of a minute rounded UP, in integer milliseconds. The
/// number printed is a promise - "+16.6 min" - and CLAUDE.md's invariant is that the budget is a ceiling,
/// so the printed figure may over-state the extra time and never under-state it: rounding 1_020_063 ms
/// (17.0011 min) to the nearest tenth would print +17.0 for a route that takes longer than that.
public struct MenuRow: Sendable, Equatable {

    /// A stretch is fun at this scenic score and above.
    public static let funScore = 6
    /// A road is named on a row when the route covers at least this many metres of it in total.
    public static let roadMinimumMeters = 300.0

    public let path: RoutePath
    public let table: PlanTable
    /// Tenths of a minute over the fastest, rounded UP.
    public let extraTenths: Int
    public let funMeters: Double
    public let tableMeters: Double
    /// Metre-weighted mean scenic score over the rows that carry one; nil when none does.
    public let meanScore: Double?
    public let roads: [String]

    public init(path: RoutePath, fastestMilliseconds: Int) {
        let table = PlanTable(path: path)
        self.path = path
        self.table = table
        self.extraTenths = Self.tenthsOfAMinute(path.durationMilliseconds - fastestMilliseconds)
        var fun = 0.0, total = 0.0, scored = 0.0, weighted = 0.0
        for row in table.rows {
            total += row.meters
            guard let score = row.scenicScore else { continue }
            scored += row.meters
            weighted += row.meters * Double(score)
            if score >= Self.funScore { fun += row.meters }
        }
        self.funMeters = fun
        self.tableMeters = total
        self.meanScore = scored > 0 ? weighted / scored : nil
        self.roads = Self.roads(of: path)
    }

    /// The displayed extra minutes, e.g. 16.6.
    public var extraMinutes: Double { Double(extraTenths) / 10 }

    public var funShare: Double { tableMeters > 0 ? funMeters / tableMeters : 0 }

    /// Milliseconds -> tenths of a minute, rounded UP. 6_000 ms is a tenth of a minute.
    static func tenthsOfAMinute(_ milliseconds: Int) -> Int {
        milliseconds <= 0 ? 0 : (milliseconds + 5_999) / 6_000
    }

    /// Named roads the route covers `roadMinimumMeters` of, in order of first appearance, from the
    /// `street_name` detail the recorder asked the graph for.
    static func roads(of path: RoutePath) -> [String] {
        var order: [String] = []
        var meters: [String: Double] = [:]
        for run in path.details["street_name"] ?? [] {
            guard let name = run.value.text, !name.isEmpty else { continue }
            if meters[name] == nil { order.append(name) }
            meters[name, default: 0] += PlanTable.length(of: path.coordinates, from: run.from, to: run.to)
        }
        return order.filter { (meters[$0] ?? 0) >= Self.roadMinimumMeters }
    }

    /// `ROW 2 extra=+16.6min eta=34m53s km=35.37 fun_km=19.7 fun_share=56% mean=4.77 roads=...`
    public func line(_ index: Int) -> String {
        let mean = meanScore.map { ScenicPlan.fixed($0, 2) } ?? "-"
        return "ROW \(index) extra=+\(ScenicPlan.fixed(extraMinutes, 1))min "
            + "eta=\(ScenicPlan.clock(path.duration)) km=\(ScenicPlan.fixed(path.distanceMeters / 1_000, 2)) "
            + "fun_km=\(ScenicPlan.fixed(funMeters / 1_000, 1)) "
            + "fun_share=\(ScenicPlan.fixed(funShare * 100, 0))% mean=\(mean) "
            + "roads=\(roads.joined(separator: ", "))"
    }
}
