/// The state of the closures set a route was planned around (T-0341 R1): the Worker's closures_hazard.state
/// (services/api/src/closuresStore.ts). Anything the app cannot read as one of these is `unavailable`.
public enum ClosuresState: Equatable, Sendable {
    /// The set was current: no state line.
    case fresh
    /// The last good set, older than the Worker's freshness bound.
    case stale
    /// No set at all: the route was planned without closures.
    case unavailable
}
