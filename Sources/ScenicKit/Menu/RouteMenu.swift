import Foundation

/// The time-versus-fun menu for one trip: "how much more would I have to drive to have a fun drive".
///
/// ## What it is computed from
///
/// Recorded paths only (T-0239 R1-R3): car_fast's best path, plus every path GraphHopper's
/// `alternative_route` returned on car_fast and on car_scenic at each rung of `ladder`. Two paths whose OSM
/// way-id sets overlap by `sameRouteOverlap` or more (Jaccard, `RouteDifference.overlap`) are one route,
/// and the quicker one stands for it.
///
/// ## The frontier (R4)
///
/// The distinct routes are walked in duration order. The quickest is always row 0 - "the fastest" - and it
/// is also the reference every row's extra minutes are measured from: the quickest duration in the whole
/// pool, which in both recordings is fastest.json and which can only make the ceiling stricter if it is not.
/// A slower route becomes a row when it is inside the cap AND adds at least `funStepMeters` of fun over the
/// most fun of every quicker row. So each row answers "for this many more minutes, this much more fun", and
/// a slower route that is no more fun than a quicker one is never offered.
///
/// ## The cap is a ceiling
///
/// `capMinutes` is the "within reason" of the owner's question; a caller may lower it (`ops/plan --menu
/// --max N`) and never raise it. A route slower than fastest + cap is not measured, not deduplicated
/// against, and not shown.
public struct RouteMenu: Sendable, Equatable {

    public static let capMinutes = 45.0
    public static let funStepMeters = 2_000.0
    public static let sameRouteOverlap = 0.9
    public static let ladder: [Double] = [0, 2, 4, 6, 8]

    public let fastestMilliseconds: Int
    public let maxMinutes: Double
    public let candidateCount: Int
    /// Distinct routes inside the cap - the population the frontier ranges over.
    public let distinctCount: Int
    public let rows: [MenuRow]

    public init(fastest: RoutePath, candidates: [RoutePath], maxMinutes: Double = RouteMenu.capMinutes) {
        let pool = [fastest] + candidates
        let quickest = pool.map(\.durationMilliseconds).min() ?? fastest.durationMilliseconds
        let minutes = min(maxMinutes, Self.capMinutes)
        let limit = quickest + Int((minutes * 60_000).rounded(.down))
        let distinct = Self.distinct(pool.filter { $0.durationMilliseconds <= limit })
        self.fastestMilliseconds = quickest
        self.maxMinutes = minutes
        self.candidateCount = pool.count
        self.distinctCount = distinct.count
        self.rows = Self.frontier(distinct.map { MenuRow(path: $0, fastestMilliseconds: quickest) })
    }

    /// Duration order (recording order on a tie), each path dropped when a quicker kept one is the same
    /// route.
    static func distinct(_ paths: [RoutePath]) -> [RoutePath] {
        let ordered = paths.enumerated().sorted { left, right in
            left.element.durationMilliseconds == right.element.durationMilliseconds
                ? left.offset < right.offset
                : left.element.durationMilliseconds < right.element.durationMilliseconds
        }
        var kept: [(path: RoutePath, ways: Set<Int>)] = []
        for (_, path) in ordered {
            let ways = RouteDifference.wayIds(of: path)
            if kept.contains(where: { RouteDifference.overlap($0.ways, ways) >= Self.sameRouteOverlap }) {
                continue
            }
            kept.append((path, ways))
        }
        return kept.map(\.path)
    }

    /// `routes` in duration order; row 0 is the quickest, and every later row adds `funStepMeters`.
    static func frontier(_ routes: [MenuRow]) -> [MenuRow] {
        var rows: [MenuRow] = []
        for route in routes {
            guard let best = rows.map(\.funMeters).max() else {
                rows.append(route)
                continue
            }
            if route.funMeters >= best + Self.funStepMeters {
                rows.append(route)
            }
        }
        return rows
    }

    /// The header line `ops/plan --menu` prints above the rows.
    public func header() -> String {
        "MENU fastest=\(ScenicPlan.clock(Double(fastestMilliseconds) / 1_000)) "
            + "cap=+\(ScenicPlan.fixed(maxMinutes, 1))min candidates=\(candidateCount) "
            + "distinct=\(distinctCount) rows=\(rows.count) "
            + "(fun = scenic_score >= \(MenuRow.funScore); each row adds >= "
            + "\(ScenicPlan.fixed(Self.funStepMeters / 1_000, 1)) fun km over every quicker row; "
            + "extra minutes rounded up; free-flow, no traffic)"
    }
}
