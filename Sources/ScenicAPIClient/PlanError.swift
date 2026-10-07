import Foundation

/// Every way a plan can fail, as the app sees it - the plan's closed `PlanError` enum (plan :146), widened by
/// exactly the cases the shipped Worker's responses need (T-0251 R6). `PlanResponseReader` holds the mapping
/// from (HTTP status, body `error`) to a case; the Log's R6 table is its specification.
public enum PlanError: Error, Equatable, Sendable {
    /// 429 `quota_exhausted`: today's plans are spent; planning returns at `resetsAt` (UTC midnight).
    case quotaExhausted(resetsAt: Date)
    /// 503 `planning_paused`: the kill switch or the upstream spend ceiling.
    case planningPaused
    /// The Worker or its router cannot be reached: 503 `planning_unavailable`, any other 5xx, or no reply at all.
    case routingOffline
    /// 502 `no_route`: no route within the ceiling, or the router refused.
    case noRoute
    /// 422 `region_unsupported`: the origin is outside every served region's bbox (T-0293, servedRegion.ts).
    case regionUnsupported
    /// Plan cases no current Worker response produces (no /attest refusal, no drive yet).
    case attestUnsupported
    case offlineDuringDrive
    /// 422 `no_scenic_alternative`: the best scenic route is the fastest route under another name.
    case noScenicAlternative
    /// 404 `unknown_place`: the server's corpus does not know the destination id.
    case unknownPlace
    /// 500 `ceiling_breached` / `no_recorded_lambda`: the server's own safety net refused its result.
    case planRefused(reason: String)
    /// 400 `invalid_request`: the Worker's whitelist refused the body; `detail` is its sentence.
    case invalidRequest(detail: String)
    /// The client refused to send (T-0251 R3); no request was made.
    case refusedOnDevice(PlanRefusal)
    /// Any reply the table does not name: a client/server disagreement about the protocol, not a user state.
    case unexpectedResponse(status: Int)
}
