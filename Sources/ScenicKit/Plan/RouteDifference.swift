import Foundation

/// How much of a route is the fastest route.
///
/// The meta-test this exists for is the plan's: *a solver that answers lambda 0 must fail "actually
/// different"*. Lambda 0 IS the fastest route by construction, so its overlap with the fastest edge set is
/// 1.0, and the requirement `overlap < maximumOverlap` refuses it. Nothing else in the pipeline can catch
/// that: the duration is feasible, the ceiling holds, the lambda is in range, and the route is the one the
/// user was already going to drive.
///
/// The measure is the Jaccard index over OSM WAY IDS - |A intersection B| / |A union B| - rather than over
/// geometry points or GraphHopper edge ids. Way ids survive a re-import; edge ids do not (they are
/// positions in a built graph and move whenever the graph is rebuilt), and two runs over the same road
/// produce different point counts at different snapping tolerances while naming the same ways.
public enum RouteDifference {

    /// The most of itself a scenic route may share with the fastest one.
    ///
    /// 0.6 is the plan's number, read as the requirement it states: `Jaccard(edge-set, fastest) < 0.6`. It
    /// is a product threshold, not a mathematical one - a drive that is 60% the same road is the same drive
    /// - and it lives here, once, so the meta-test and the CLI cannot disagree about it.
    public static let maximumOverlap = 0.6

    /// Jaccard index of two way-id sets. 1.0 is "the same ways", 0.0 is "no way in common".
    ///
    /// Two EMPTY sets score 1.0 rather than 0. A union of nothing is not a difference, and answering "these
    /// routes could not be more different" about two routes we know nothing about is the vacuous green this
    /// repository keeps finding: an empty `details` map would otherwise let every route pass the
    /// actually-different guard.
    public static func overlap(_ a: Set<Int>, _ b: Set<Int>) -> Double {
        let union = a.union(b)
        if union.isEmpty { return 1.0 }
        return Double(a.intersection(b).count) / Double(union.count)
    }

    /// The way ids a routed path ran over, from its `osm_way_id` path detail.
    ///
    /// Empty when the detail is absent, which is a graph that was not built with `osm_way_id` in
    /// `graph.encoded_values`; the empty-set rule above turns that into "not different", i.e. a refusal,
    /// rather than into a pass nobody measured.
    public static func wayIds(of path: RoutePath, detail: String = "osm_way_id") -> Set<Int> {
        var ids: Set<Int> = []
        for run in path.details[detail] ?? [] {
            if let value = run.value.number { ids.insert(Int(value)) }
        }
        return ids
    }

    /// True when `path` is different enough from `fastest` to be offered as a scenic alternative.
    public static func isActuallyDifferent(_ path: RoutePath, from fastest: RoutePath) -> Bool {
        overlap(wayIds(of: path), wayIds(of: fastest)) < maximumOverlap
    }
}
