/// One edge of a planned route as the traffic provider re-times it: the corridor cell it runs through and the
/// router's free-flow seconds for it (plan, Problem A step 5: per-edge `details=time`).
public struct CorridorEdge: Equatable, Sendable {
    public let cell: CorridorCell
    public let freeFlowSeconds: Double

    public init(cell: CorridorCell, freeFlowSeconds: Double) {
        self.cell = cell
        self.freeFlowSeconds = freeFlowSeconds
    }
}
