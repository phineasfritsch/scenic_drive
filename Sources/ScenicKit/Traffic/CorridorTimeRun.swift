/// One GraphHopper `details=time` run over a planned route (T-0325 R2): the edge from vertex `from` to vertex `to`
/// and its free-flow time in whole milliseconds, as the router answers it. CorridorRoute reads a route's runs.
public struct CorridorTimeRun: Equatable, Sendable {
    public let from: Int
    public let to: Int
    public let milliseconds: Int

    public init(from: Int, to: Int, milliseconds: Int) {
        self.from = from
        self.to = to
        self.milliseconds = milliseconds
    }
}
