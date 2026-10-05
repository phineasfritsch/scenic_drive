import Foundation

/// The one seam between `PlanClient` and the network (T-0251 R4). Production is `URLSessionPlanTransport`;
/// tests and app previews use `CountingPlanTransport`, which counts what would have gone on the wire.
/// A transport throws only when no HTTP reply arrived at all; every reply, whatever its status, is returned.
public protocol PlanTransport: Sendable {
    func send(_ request: PlanHTTPRequest) async throws -> PlanHTTPReply
}
