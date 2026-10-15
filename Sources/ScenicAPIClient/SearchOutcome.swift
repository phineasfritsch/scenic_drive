import Foundation

/// Every answer one `SearchClient.search` call can have (T-0359 R7): one case per Worker status the route answers,
/// the one the device decides on its own (`refusedOnDevice`) and the one where no reply came (`offline`). Nothing is
/// retried.
public enum SearchOutcome: Equatable, Sendable {
    /// 200 with a readable {results}: at most `SearchReplyReader.limit` rows, in the Worker's order.
    case results([SearchResult])
    /// The query or the bias would be refused by the Worker: no request was made.
    case refusedOnDevice
    /// 400 invalid_request.
    case invalidRequest
    /// 401 session_rejected.
    case unauthorized
    /// 405 - POST only.
    case methodRefused
    /// 429 quota_exhausted: the day's searches are spent.
    case quotaExhausted
    /// 503 planning_paused: the kill switch or the month's ceiling.
    case paused
    /// 503 search_unavailable: the Worker has no search box bound.
    case unavailable
    /// 502 search_failed: the search box did not answer, or answered something the Worker would not pass on.
    case failed
    /// A 200 whose body is not a readable {results}.
    case unreadable
    /// Any other status, or a 429/502/503 whose error is not the one the route sends.
    case unexpected(Int)
    /// No HTTP reply arrived at all.
    case offline
}
