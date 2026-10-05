import Foundation

/// The road-trip day splitter (T-0249): A -> B over N days on a +40% scenic budget, a forward pass over the
/// route's edges under a max drive and max distance per day, 2-4 corridor stops a day, an overnight town per
/// boundary. Pure: it reads a recorded route and a list of places and fetches nothing.
public enum RoadTrip {
    public enum Outcome: Sendable, Equatable {
        case plan([RoadTripDay])
        /// The route's seconds exceed fastest + budget: the budget is a ceiling, never a plan over it.
        case overBudget(routeSeconds: Int, ceilingSeconds: Int)
        /// The limits cannot carry the route to B in `days` days; the pass stopped at `reachedVertex`.
        case tooFewDays(days: Int, reachedVertex: Int)
    }

    public static let budgetPercent = 40
    public static let corridorMeters = 5_000.0
    public static let maxStopsPerDay = 4
    public static let overnightRadiusMeters = 15_000.0

    /// The road trip's extra-time budget: 40% of the fastest, rounded DOWN (the ceiling's safe side).
    public static func budgetSeconds(fastestSeconds: Int) -> Int {
        fastestSeconds * budgetPercent / 100
    }

    /// The whole day plan (T-0249 R3-R6): the budget ceiling first, then the forward pass, then each day's
    /// stops and overnight.
    public static func plan(edges: [RoadTripEdge], places: [RoadTripPlace], fastestSeconds: Int,
                            limits: RoadTripLimits) -> Outcome {
        let total = edges.reduce(0) { $0 + $1.seconds }
        let ceiling = fastestSeconds + budgetSeconds(fastestSeconds: fastestSeconds)
        guard total <= ceiling else {
            return .overBudget(routeSeconds: total, ceilingSeconds: ceiling)
        }
        guard !edges.isEmpty else { return .plan([]) }
        guard limits.days >= 1 else { return .tooFewDays(days: limits.days, reachedVertex: 0) }
        let spans = forwardPass(edges: edges, total: total, limits: limits)
        let reached = spans.last?.end ?? 0
        guard reached == edges.count else {
            return .tooFewDays(days: limits.days, reachedVertex: reached)
        }
        let vertices = [edges[0].start] + edges.map(\.end)
        let corridor = corridorStops(places: places, vertices: vertices)
        let lodgings = places.filter { $0.kind == .lodging }
        return .plan(spans.enumerated().map { index, span in
            let last = index == spans.count - 1
            return RoadTripDay(day: index + 1, startVertex: span.start, endVertex: span.end,
                               seconds: span.seconds, meters: span.meters,
                               stops: stops(corridor: corridor, from: span.start, to: span.end),
                               overnight: last ? nil : overnight(at: vertices[span.end], lodgings: lodgings))
        })
    }

    /// One day's edges [start, end) with their summed seconds and metres.
    struct Span {
        let start: Int
        let end: Int
        let seconds: Int
        let meters: Int
    }

    /// R4: day d keeps driving until it holds an edge AND has reached its even share of the trip (cumulative
    /// seconds * N >= d * total), and never past either limit (both inclusive). A day that cannot take its
    /// first edge ends the pass; so does running out of edges - no day is invented.
    static func forwardPass(edges: [RoadTripEdge], total: Int, limits: RoadTripLimits) -> [Span] {
        var spans: [Span] = []
        var index = 0, cumulative = 0
        for day in 1...limits.days {
            guard index < edges.count else { break }
            let start = index
            var seconds = 0, meters = 0
            while index < edges.count {
                let edge = edges[index]
                if index > start && cumulative * limits.days >= day * total { break }
                if seconds + edge.seconds > limits.maxDriveSeconds || meters + edge.meters > limits.maxMeters {
                    break
                }
                seconds += edge.seconds
                meters += edge.meters
                cumulative += edge.seconds
                index += 1
            }
            guard index > start else { break }
            spans.append(Span(start: start, end: index, seconds: seconds, meters: meters))
        }
        return spans
    }

    /// A corridor stop: its nearest vertex (ties -> the lower index) lies within `corridorMeters` (R5).
    struct CorridorStop {
        let place: RoadTripPlace
        let vertex: Int
    }

    static func corridorStops(places: [RoadTripPlace], vertices: [Coordinate]) -> [CorridorStop] {
        places.filter { $0.kind == .stop }.compactMap { place in
            var best = 0, bestMeters = Double.infinity
            for (i, vertex) in vertices.enumerated() {
                let meters = Geo.distanceMeters(place.coordinate, vertex)
                if meters < bestMeters {
                    best = i
                    bestMeters = meters
                }
            }
            return bestMeters <= corridorMeters ? CorridorStop(place: place, vertex: best) : nil
        }
    }

    /// R5: the day owns vertices (start, end], day 1 also vertex 0. The top `maxStopsPerDay` by score (ties
    /// -> lower vertex, then name), listed in route order (vertex, then name).
    static func stops(corridor: [CorridorStop], from start: Int, to end: Int) -> [String] {
        let first = start == 0 ? 0 : start + 1
        let owned = corridor.filter { $0.vertex >= first && $0.vertex <= end }
        let ranked = owned.sorted { a, b in
            if a.place.score != b.place.score { return a.place.score > b.place.score }
            if a.vertex != b.vertex { return a.vertex < b.vertex }
            return a.place.name < b.place.name
        }
        let kept = ranked.prefix(maxStopsPerDay).sorted { a, b in
            a.vertex != b.vertex ? a.vertex < b.vertex : a.place.name < b.place.name
        }
        return kept.map(\.place.name)
    }

    /// R6: the nearest lodging within `overnightRadiusMeters` of the boundary (ties -> name), or said absent.
    static func overnight(at boundary: Coordinate, lodgings: [RoadTripPlace]) -> RoadTripDay.Overnight {
        var best: (name: String, meters: Double)?
        for lodging in lodgings {
            let meters: Double = Geo.distanceMeters(lodging.coordinate, boundary)
            guard meters <= overnightRadiusMeters else { continue }
            if let held = best, held.meters < meters || (held.meters == meters && held.name < lodging.name) {
                continue
            }
            best = (lodging.name, meters)
        }
        guard let best else { return .noLodging }
        return .lodging(name: best.name, meters: Int(best.meters.rounded()))
    }
}
