import Foundation
import Testing
@testable import ScenicKit

/// T-0325 R2: a route and its router time runs cut into corridor edges, compared WHOLE (coordinates, edges, first
/// vertices) to a value written out per row; the cells are the reference table's (h3-py), never recomputed here.
@Suite("corridor routes from the router's time runs (T-0325)") struct CorridorRouteTests {
    /// Five Los Angeles reference points, each in its own resolution-8 cell.
    static let v = (0..<5).map { Coordinate(latitude: CorridorCellReference.rows[$0].latitude,
                                            longitude: CorridorCellReference.rows[$0].longitude) }
    static let c = (0..<5).map { CorridorCell(index: CorridorCellReference.rows[$0].res8) }
    static let runs = [CorridorTimeRun(from: 0, to: 1, milliseconds: 80_000),
                       CorridorTimeRun(from: 1, to: 2, milliseconds: 90_000),
                       CorridorTimeRun(from: 2, to: 3, milliseconds: 40_000),
                       CorridorTimeRun(from: 3, to: 4, milliseconds: 100_000)]

    static func run(_ from: Int, _ to: Int, _ ms: Int) -> CorridorTimeRun {
        CorridorTimeRun(from: from, to: to, milliseconds: ms)
    }

    static func edge(_ cell: CorridorCell, _ seconds: Double) -> CorridorEdge {
        CorridorEdge(cell: cell, freeFlowSeconds: seconds)
    }

    @Test("the five reference points are in five different cells")
    func fiveCells() {
        #expect(Set(Self.c).count == 5)
    }

    /// Each accepted row: the edges and first vertices written out. Each refused row: nil.
    @Test("runs tile the route edge for edge into corridor edges; every bound of the tiling refused")
    func tilingTable() {
        let (v, c) = (Self.v, Self.c)
        let north = Coordinate(latitude: 90, longitude: 0)
        let northCell = CorridorCell(index: 0x0880_3262_33bf_ffff)
        typealias Row = (String, [Coordinate], [CorridorTimeRun], [CorridorEdge], [Int])
        let accepted: [Row] = [
            ("one edge per run", v, Self.runs,
             [Self.edge(c[0], 80), Self.edge(c[1], 90), Self.edge(c[2], 40), Self.edge(c[3], 100)], [0, 1, 2, 3]),
            ("adjacent runs in one cell merge", [v[0], v[0], v[1], v[2]],
             [Self.run(0, 1, 1000), Self.run(1, 2, 2000), Self.run(2, 3, 3500)],
             [Self.edge(c[0], 3), Self.edge(c[1], 3.5)], [0, 2]),
            ("a cell met again later is a new edge", [v[0], v[1], v[0], v[1]],
             [Self.run(0, 1, 1000), Self.run(1, 2, 2000), Self.run(2, 3, 3000)],
             [Self.edge(c[0], 1), Self.edge(c[1], 2), Self.edge(c[0], 3)], [0, 1, 2]),
            ("a run over several vertices counts for its first vertex's cell", [v[0], v[1], v[2]],
             [Self.run(0, 2, 5001)], [Self.edge(c[0], 5.001)], [0]),
            ("a zero-millisecond run beside a timed one", [v[0], v[1], v[2]],
             [Self.run(0, 1, 0), Self.run(1, 2, 7)], [Self.edge(c[0], 0), Self.edge(c[1], 0.007)], [0, 1]),
            ("latitude 90 is a vertex", [north, v[0]], [Self.run(0, 1, 1000)], [Self.edge(northCell, 1)], [0]),
        ]
        for (name, route, runs, edges, firsts) in accepted {
            let built = CorridorRoute(route: route, timeRuns: runs)
            #expect(built?.coordinates == route, "\(name)")
            #expect(built?.edges == edges, "\(name)")
            #expect(built?.firstVertices == firsts, "\(name)")
        }
        let out = Coordinate(latitude: 90.0.nextUp, longitude: 0)
        let refused: [(String, [Coordinate], [CorridorTimeRun])] = [
            ("no runs", v, []),
            ("one vertex", [v[0]], [Self.run(0, 0, 1000)]),
            ("no vertices", [], []),
            ("the first run starts at 1", v, [Self.run(1, 4, 1000)]),
            ("a gap", v, [Self.run(0, 1, 1000), Self.run(2, 4, 1000)]),
            ("an overlap", v, [Self.run(0, 2, 1000), Self.run(1, 4, 1000)]),
            ("from == to", v, [Self.run(0, 0, 1000), Self.run(0, 4, 1000)]),
            ("to before from", v, [Self.run(0, 2, 1000), Self.run(2, 1, 1000), Self.run(1, 4, 1000)]),
            ("the last run one short", v, [Self.run(0, 3, 1000)]),
            ("the last run one long", v, [Self.run(0, 5, 1000)]),
            ("a negative time", v, [Self.run(0, 2, 1000), Self.run(2, 4, -1)]),
            ("every time zero", v, [Self.run(0, 2, 0), Self.run(2, 4, 0)]),
            ("a vertex one ulp past 90", [v[0], out], [Self.run(0, 1, 1000)]),
            ("a NaN vertex", [v[0], Coordinate(latitude: .nan, longitude: 0)], [Self.run(0, 1, 1000)]),
            ("a vertex one ulp past 180", [v[0], Coordinate(latitude: 0, longitude: 180.0.nextUp)],
             [Self.run(0, 1, 1000)]),
        ]
        for (name, route, runs) in refused {
            #expect(CorridorRoute(route: route, timeRuns: runs) == nil, "\(name)")
        }
    }

    @Test("a segment's edge is the last edge starting at or before it")
    func edgeOfSegment() {
        let route = CorridorRoute(route: [Self.v[0], Self.v[0], Self.v[1], Self.v[2], Self.v[3]],
                                  timeRuns: [Self.run(0, 1, 1), Self.run(1, 2, 1), Self.run(2, 3, 1),
                                             Self.run(3, 4, 1)])
        #expect(route?.firstVertices == [0, 2, 3])
        #expect((0..<4).map { route?.edge(containingSegment: $0) } == [0, 0, 1, 2])
    }
}
