/// What a plan, trip or loop answer said about road closures (T-0341 R1): the state of the set it was planned around,
/// whether the Worker left some closures out of the request (`dropped`), and whether the returned path still crosses
/// a stored closure (`crosses`). HazardCopy.closureLines turns it into the driver's lines; `.clear` reads none.
public struct ClosuresHazard: Equatable, Sendable {
    public let state: ClosuresState
    public let dropped: Bool
    public let crosses: Bool

    public init(state: ClosuresState, dropped: Bool = false, crosses: Bool = false) {
        self.state = state
        self.dropped = dropped
        self.crosses = crosses
    }

    /// A fresh set, nothing left out, nothing crossed: the Worker sends no closures_hazard at all.
    public static let clear = ClosuresHazard(state: .fresh)
}
