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
            /// T-0362 R1: absent is nil; present, it must be a string - null or any other type fails the decode.
            let place: String?

            enum CodingKeys: String, CodingKey { case label, lat, lon, place }

            init(from decoder: any Decoder) throws {
                let row = try decoder.container(keyedBy: CodingKeys.self)
                label = try row.decode(String.self, forKey: .label)
                lat = try row.decode(Double.self, forKey: .lat)
                lon = try row.decode(Double.self, forKey: .lon)
                place = row.contains(.place) ? try row.decode(String.self, forKey: .place) : nil
            }
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

    /// The deepest searched place id the Worker's isSearchPlaceId accepts: -(2^53 - 1).
    static let deepestPlace: Int64 = -9_007_199_254_740_991

    /// T-0362 R1: the Worker's spelling exactly - the decimal form of an Int64 in [deepestPlace, -1], so "-0", "-01",
    /// "+1", padding and anything outside the range are not ids.
    static func placeID(_ text: String) -> Int64? {
        guard let value = Int64(text), value >= deepestPlace, value <= -1, String(value) == text else { return nil }
        return value
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
            var place: Int64?
            if let text = row.place {
                guard let id = placeID(text) else { return .unreadable }
                place = id
            }
            rows.append(SearchResult(label: row.label, coordinate: Coordinate(latitude: row.lat, longitude: row.lon),
                                     place: place))
        }
        return .results(rows)
    }
}
