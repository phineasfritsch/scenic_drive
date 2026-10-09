import Foundation

/// The /loop outcome table (T-0314 R2): every status and error code services/api/src/loop.ts answers, mapped to one
/// typed outcome. Pure; LoopClient sends once and reads once - no retries.
enum LoopReplyReader {
    static func read(_ reply: PlanHTTPReply) -> Result<LoopResponse, LoopError> {
        if reply.status == 200 {
            guard let loop = try? JSONDecoder().decode(LoopResponse.self, from: reply.body) else {
                return .failure(.unexpectedResponse(status: 200))
            }
            return .success(loop)
        }
        let body = try? JSONDecoder().decode(PlanFailureBody.self, from: reply.body)
        return .failure(error(status: reply.status, body: body))
    }

    static func error(status: Int, body: PlanFailureBody?) -> LoopError {
        switch (status, body?.error) {
        case (400, "invalid_request"?):
            return .invalidRequest(detail: body?.detail ?? "")
        case (422, "region_unsupported"?):
            return .regionUnsupported
        case (422, "no_clean_loop"?):
            return .noCleanLoop
        case (422, "nothing_pretty"?):
            guard let dull = body?.loopNothingPretty else { return .unexpectedResponse(status: status) }
            return .nothingPretty(dull)
        case (429, "quota_exhausted"?):
            guard let text = body?.resetsAt, let resetsAt = PlanResponseReader.instant(text) else {
                return .unexpectedResponse(status: status)
            }
            return .quotaExhausted(resetsAt: resetsAt)
        case (502, "no_route"?):
            return .noRoute
        case (503, "planning_paused"?):
            return .planningPaused
        case (503, "planning_unavailable"?):
            return .routingOffline
        case (500...599, _):
            return .routingOffline
        default:
            return .unexpectedResponse(status: status)
        }
    }
}
