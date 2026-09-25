import Foundation

/// Where routes come from.
///
/// One method for the fastest route and one for a scenic route at a lambda, because they are two different
/// profiles on the server (`car_fast` and `car_scenic`) and only the second carries a per-request custom
/// model. Folding them into one call with an optional lambda would let a caller ask for the fastest route
/// through the scenic profile, which is a different question with the same answer only when lambda is
/// exactly 0 - and "only when" is how the lambda-0 stub the meta-tests refuse gets written.
///
/// Synchronous and throwing. A plan is at most twelve sequential requests to one box, each about 100 ms,
/// and the caller is a command-line program that has nothing else to do while it waits; async here would
/// buy nothing and would push `LambdaSearch`'s injected `measure` closure into an async signature it does
/// not need.
public protocol RouteSource {
    /// A one-line description of where routes came from, printed in the report so a pasted run says what
    /// answered it - a live router or a recording.
    var describedSource: String { get }

    /// The fastest route under the safety gates alone: the plan's `T_fast`, and the value lambda 0 must
    /// reproduce.
    func fastest(from origin: Coordinate, to destination: Coordinate) throws -> RoutePath

    /// The scenic route at `lambda`, which the source sends as the per-request custom model.
    func scenic(from origin: Coordinate, to destination: Coordinate, lambda: Double) throws -> RoutePath
}
