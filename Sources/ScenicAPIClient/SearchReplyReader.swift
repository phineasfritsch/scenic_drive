import Foundation
import ScenicKit

/// T-0359 R7: every /search reply -> exactly one `SearchOutcome`, by status, then by body where the status alone does
/// not decide. The results are read FAIL-CLOSED: a wrong type, an empty label, a coordinate out of range or more rows
/// than the Worker ever sends makes the whole answer unreadable - a half-read answer is not shown.
enum SearchReplyReader {
    /// The Worker's SEARCH_LIMIT.
    static let limit = 8

    private struct Answer: Decodable {
        struct Row: Decodable {
            let label: String
            let lat: Double
            let lon: Double
        }

        let results: [Row]
    }

    private struct Failure: Decodable {
        let error: String
    }

    static func read(_ reply: PlanHTTPReply) -> SearchOutcome {
        switch reply.status {
        case 200: return results(reply.body)
        case 400: return .invalidRequest
        case 401: return .unauthorized
        case 405: return .methodRefused
        case 429: return error(reply.body) == "quota_exhausted" ? .quotaExhausted : .unexpected(429)
        case 502: return error(reply.body) == "search_failed" ? .failed : .unexpected(502)
        case 503:
            switch error(reply.body) {
            case "planning_paused": return .paused
            case "search_unavailable": return .unavailable
            default: return .unexpected(503)
            }
        default: return .unexpected(reply.status)
        }
    }

    private static func error(_ body: Data) -> String? {
        (try? JSONDecoder().decode(Failure.self, from: body))?.error
    }

    private static func results(_ body: Data) -> SearchOutcome {
        guard let answer = try? JSONDecoder().decode(Answer.self, from: body), answer.results.count <= limit else {
            return .unreadable
        }
        var rows: [SearchResult] = []
        for row in answer.results {
            guard !row.label.trimmingCharacters(in: .whitespacesAndNewlines).isEmpty,
                  row.lat.isFinite, row.lat >= -90, row.lat <= 90,
                  row.lon.isFinite, row.lon >= -180, row.lon <= 180 else { return .unreadable }
            rows.append(SearchResult(label: row.label, coordinate: Coordinate(latitude: row.lat, longitude: row.lon)))
        }
        return .results(rows)
    }
}
