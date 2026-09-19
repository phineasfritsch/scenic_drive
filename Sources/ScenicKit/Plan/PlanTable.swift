import Foundation

/// The per-edge term table the plan's M3 exit asks `ops/plan` to print.
///
/// ## What a row is, and what it can say today
///
/// A row is a maximal stretch of the route over which the way id, the road class and the scenic score all
/// stay the same. The route's point list is cut at every boundary any of those three path details
/// declares, and neighbouring intervals carrying the same three values are merged, so one row is one road
/// under one score rather than one GraphHopper edge - which is what a person reading a plan wants and what
/// the plan's "per-edge term table" means on a graph with contraction disabled.
///
/// The columns are the columns the served graph can answer (T-0213's window encodes `scenic_score` and
/// `osm_way_id`; `road_class` is GraphHopper's own): way id, highway, scenic score, metres, seconds. The
/// SCORING TERMS - the E/M/GATE breakdown of `SegmentTerms` - are not in the graph at all, so this table
/// does not print a column for them. A column of blanks reads as "the terms are zero" and that would be a
/// table lying about the engine.
///
/// Seconds are apportioned by metres from the path's own total, and the header says so. GraphHopper can
/// report a `time` path detail, the window's graph was not routed with one, and inventing per-row speeds
/// from a profile we did not run is worse than dividing the one duration we measured.
public struct PlanTable: Sendable, Equatable {

    public struct Row: Sendable, Equatable {
        public let wayId: Int?
        public let highway: String?
        public let scenicScore: Int?
        public let fromIndex: Int
        public let toIndex: Int
        public let meters: Double
        public let seconds: TimeInterval

        public init(wayId: Int?, highway: String?, scenicScore: Int?,
                    fromIndex: Int, toIndex: Int, meters: Double, seconds: TimeInterval) {
            self.wayId = wayId
            self.highway = highway
            self.scenicScore = scenicScore
            self.fromIndex = fromIndex
            self.toIndex = toIndex
            self.meters = meters
            self.seconds = seconds
        }
    }

    /// The three details this table reads, in column order.
    public static let wayIdDetail = "osm_way_id"
    public static let highwayDetail = "road_class"
    public static let scenicScoreDetail = "scenic_score"

    public let rows: [Row]

    public init(rows: [Row]) { self.rows = rows }

    public init(path: RoutePath) {
        self.rows = PlanTable.rows(of: path)
    }

    static func rows(of path: RoutePath) -> [Row] {
        let points = path.coordinates
        guard points.count >= 2 else { return [] }
        let wayIds = path.details[wayIdDetail] ?? []
        let highways = path.details[highwayDetail] ?? []
        let scores = path.details[scenicScoreDetail] ?? []

        var cuts: Set<Int> = [0, points.count - 1]
        for run in wayIds + highways + scores {
            cuts.insert(min(max(run.from, 0), points.count - 1))
            cuts.insert(min(max(run.to, 0), points.count - 1))
        }
        let bounds = cuts.sorted()

        var merged: [Row] = []
        for index in 0..<(bounds.count - 1) {
            let from = bounds[index]
            let to = bounds[index + 1]
            let wayId = value(of: wayIds, covering: from).flatMap(\.number).map(Int.init)
            let highway = value(of: highways, covering: from)?.text
            let score = value(of: scores, covering: from).flatMap(\.number).map(Int.init)
            let meters = length(of: points, from: from, to: to)
            if var last = merged.last, last.wayId == wayId, last.highway == highway,
               last.scenicScore == score {
                last = Row(wayId: wayId, highway: highway, scenicScore: score,
                           fromIndex: last.fromIndex, toIndex: to,
                           meters: last.meters + meters, seconds: 0)
                merged[merged.count - 1] = last
            } else {
                merged.append(Row(wayId: wayId, highway: highway, scenicScore: score,
                                  fromIndex: from, toIndex: to, meters: meters, seconds: 0))
            }
        }
        return apportion(merged, over: path.duration)
    }

    /// The run covering the segment that STARTS at `index`, i.e. the run whose `[from, to)` contains it.
    ///
    /// Half-open on purpose: GraphHopper's runs share an index (`[0, 3]` then `[3, 7]`), so a closed test
    /// matches two runs at every boundary and the second one silently wins or loses depending on the array
    /// order. The first point of a run is the one that names it.
    static func value(of runs: [RoutePath.DetailRun], covering index: Int) -> RoutePath.Value? {
        for run in runs where run.from <= index && index < run.to { return run.value }
        return nil
    }

    static func length(of points: [Coordinate], from: Int, to: Int) -> Double {
        guard from < to, to < points.count else { return 0 }
        var meters = 0.0
        for index in from..<to {
            meters += Geo.distanceMeters(points[index], points[index + 1])
        }
        return meters
    }

    /// Seconds per row, apportioned by metres. The total is preserved to the last row so the column sums to
    /// the ETA the header prints: a table whose rows add up to a different number than the headline is the
    /// kind of detail a driver notices and stops trusting the whole screen over.
    static func apportion(_ rows: [Row], over duration: TimeInterval) -> [Row] {
        let total = rows.reduce(0.0) { $0 + $1.meters }
        guard total > 0 else { return rows }
        var apportioned: [Row] = []
        var spent = 0.0
        for (index, row) in rows.enumerated() {
            let seconds = index == rows.count - 1 ? duration - spent : duration * row.meters / total
            spent += seconds
            apportioned.append(Row(wayId: row.wayId, highway: row.highway, scenicScore: row.scenicScore,
                                   fromIndex: row.fromIndex, toIndex: row.toIndex,
                                   meters: row.meters, seconds: seconds))
        }
        return apportioned
    }
}
