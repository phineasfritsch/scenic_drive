import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// The plan's "counting fake" (plan :161, P-COST-04): a transport that answers one canned reply and records
/// every request it was handed, how many, and the most that were in flight at once.
///
/// It lives in Sources, not Tests, so that app-level tests can assert "one plan, one request" against the same
/// fake. Built with `offline()` it throws as URLSession does when no reply arrives.
public actor CountingPlanTransport: PlanTransport {
    public private(set) var requests: [PlanHTTPRequest] = []
    public private(set) var peakInFlight = 0
    private var inFlight = 0
    private let reply: PlanHTTPReply?

    public init(reply: PlanHTTPReply) {
        self.reply = reply
    }

    private init(noReply: Void) {
        self.reply = nil
    }

    /// A transport through which no reply ever arrives.
    public static func offline() -> CountingPlanTransport {
        CountingPlanTransport(noReply: ())
    }

    /// Requests handed to this transport - for one plan, the requests that plan made.
    public var count: Int { requests.count }

    public func send(_ request: PlanHTTPRequest) async throws -> PlanHTTPReply {
        requests.append(request)
        inFlight += 1
        peakInFlight = max(peakInFlight, inFlight)
        await Task.yield()
        inFlight -= 1
        guard let reply else { throw URLError(.notConnectedToInternet) }
        return reply
    }
}
