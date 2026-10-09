/// A planned route cut into the corridor edges the learner keeps and retime reads (T-0325 R2).
///
/// The router's `details=time` runs tile the route edge for edge; consecutive runs whose FIRST vertex lies in the
/// same H3-8 cell are one corridor edge, its free-flow seconds their summed milliseconds / 1000. A run longer than a
/// cell counts wholly for the cell it starts in. The free-flow times are the router's, never a length split (R2).
public struct CorridorRoute: Equatable, Sendable {
    /// The route's vertices, as the plan drew them.
    public let coordinates: [Coordinate]
    /// The corridor edges, in route order.
    public let edges: [CorridorEdge]
    /// The vertex each edge starts at; edge g covers segments firstVertices[g] up to the next edge's first vertex.
    public let firstVertices: [Int]

    /// nil unless the route has two vertices or more, every one a cell, and the runs tile 0...count - 1 edge for
    /// edge - the first from vertex 0, each from the previous one's end, each to past its from, the last to the
    /// last vertex - with no time below zero and some time above it.
    public init?(route: [Coordinate], timeRuns: [CorridorTimeRun]) {
        guard route.count >= 2, !timeRuns.isEmpty else { return nil }
        var at = 0
        for run in timeRuns {
            guard run.from == at, run.to > run.from, run.milliseconds >= 0 else { return nil }
            at = run.to
        }
        guard at == route.count - 1, timeRuns.contains(where: { $0.milliseconds > 0 }) else { return nil }
        var cells: [CorridorCell] = []
        for vertex in route {
            guard let cell = CorridorCell.containing(latitudeDegrees: vertex.latitude,
                                                     longitudeDegrees: vertex.longitude) else { return nil }
            cells.append(cell)
        }
        var grouped: [(cell: CorridorCell, milliseconds: Int, first: Int)] = []
        for run in timeRuns {
            let cell = cells[run.from]
            if let last = grouped.last, last.cell == cell {
                grouped[grouped.count - 1].milliseconds += run.milliseconds
            } else {
                grouped.append((cell, run.milliseconds, run.from))
            }
        }
        coordinates = route
        edges = grouped.map { CorridorEdge(cell: $0.cell, freeFlowSeconds: Double($0.milliseconds) / 1000) }
        firstVertices = grouped.map(\.first)
    }

    /// The edge a driver on `segment` (the segment from that vertex to the next) is in.
    public func edge(containingSegment segment: Int) -> Int {
        firstVertices.lastIndex { $0 <= segment } ?? 0
    }
}
