import Foundation

/// The /trip outcome table (T-0313 R3): every status and error code services/api/src/trip.ts answers, mapped to
/// one typed outcome. Pure; TripClient sends once and reads once - no retries.
enum TripReplyReader {
    static func read(_ reply: PlanHTTPReply) -> Result<TripResponse, TripError> {
        if reply.status == 200 {
            guard let trip = try? JSONDecoder().decode(TripResponse.self, from: reply.body) else {
                return .failure(.unexpectedResponse(status: 200))
            }
            return .success(trip)
        }
        let body = try? JSONDecoder().decode(PlanFailureBody.self, from: reply.body)
        return .failure(error(status: reply.status, body: body))
    }

    static func error(status: Int, body: PlanFailureBody?) -> TripError {
        switch (status, body?.error) {
        case (400, "invalid_request"?):
            return .invalidRequest(detail: body?.detail ?? "")
        case (404, "unknown_place"?):
            return .unknownPlace
        case (422, "region_unsupported"?):
            return .regionUnsupported
        case (422, "too_few_days"?):
            return .tooFewDays
        case (422, "ceiling_breached"?):
            return .ceilingBreached
        case (422, "nothing_pretty"?):
            guard let dull = body?.tripNothingPretty else { return .unexpectedResponse(status: status) }
            return .nothingPretty(dull)
        case (429, "quota_exhausted"?):
            guard let text = body?.resetsAt, let resetsAt = PlanResponseReader.instant(text) else {
                return .unexpectedResponse(status: status)
            }
            return .quotaExhausted(resetsAt: resetsAt)
        case (500, "no_recorded_lambda"?):
            return .planRefused(reason: "no_recorded_lambda")
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
