import Foundation

/// Reads one Worker reply into a plan or a `PlanError` - the T-0251 R6 table, row for row.
///
/// Matched on the EXACT (status, body `error`) pair the Worker's plan.ts and index.ts emit. A known code at a
/// status the Worker never pairs it with is not trusted: it falls to the two closing rows, any 5xx ->
/// routingOffline (the Worker rethrew, or Cloudflare answered for it) and anything else -> unexpectedResponse.
enum PlanResponseReader {
    static func read(_ reply: PlanHTTPReply) -> Result<PlanResponse, PlanError> {
        if reply.status == 200 {
            guard let plan = try? JSONDecoder().decode(PlanResponse.self, from: reply.body) else {
                return .failure(.unexpectedResponse(status: 200))
            }
            return .success(plan)
        }
        let body = try? JSONDecoder().decode(PlanFailureBody.self, from: reply.body)
        return .failure(error(status: reply.status, body: body))
    }

    static func error(status: Int, body: PlanFailureBody?) -> PlanError {
        switch (status, body?.error) {
        case (400, "invalid_request"?):
            return .invalidRequest(detail: body?.detail ?? "")
        case (404, "unknown_place"?):
            return .unknownPlace
        case (422, "no_scenic_alternative"?):
            return .noScenicAlternative
        case (422, "nothing_pretty"?):
            guard let offer = body?.nothingPretty else { return .unexpectedResponse(status: status) }
            return .nothingPretty(offer)
        case (422, "region_unsupported"?):
            return .regionUnsupported
        case (429, "quota_exhausted"?):
            guard let text = body?.resetsAt, let resetsAt = instant(text) else {
                return .unexpectedResponse(status: status)
            }
            return .quotaExhausted(resetsAt: resetsAt)
        case (500, "ceiling_breached"?), (500, "no_recorded_lambda"?):
            return .planRefused(reason: body?.error ?? "")
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

    /// quota.ts's `nextReset` spells resets_at with `toISOString()`: `2026-10-06T00:00:00.000Z`.
    static func instant(_ text: String) -> Date? {
        let formatter = ISO8601DateFormatter()
        formatter.formatOptions = [.withInternetDateTime, .withFractionalSeconds]
        if let date = formatter.date(from: text) { return date }
        formatter.formatOptions = [.withInternetDateTime]
        return formatter.date(from: text)
    }
}
