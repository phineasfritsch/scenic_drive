import Foundation
import ScenicKit

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
    /// 422 `nothing_pretty` (T-0332): the route the server would ship scores below RouteScore's 0.45, so it is not
    /// shown; the answer carries the plan's two offers (more time, all back roads).
    case nothingPretty(NothingPrettyOffer)
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

    /// The plan sheet's payload-free case for this error (T-0294 R1): one for one, by an exhaustive switch.
    public var failure: PlanSheetFailure {
        switch self {
        case .quotaExhausted: return .quotaExhausted
        case .planningPaused: return .planningPaused
        case .routingOffline: return .routingOffline
        case .noRoute: return .noRoute
        case .regionUnsupported: return .regionUnsupported
        case .attestUnsupported: return .attestUnsupported
        case .offlineDuringDrive: return .offlineDuringDrive
        case .noScenicAlternative: return .noScenicAlternative
        case .nothingPretty: return .nothingPretty
        case .unknownPlace: return .unknownPlace
        case .planRefused: return .planRefused
        case .invalidRequest: return .invalidRequest
        case .refusedOnDevice: return .refusedOnDevice
        case .unexpectedResponse: return .unexpectedResponse
        }
    }
}
