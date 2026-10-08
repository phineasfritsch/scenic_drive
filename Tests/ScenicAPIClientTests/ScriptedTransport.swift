import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import ScenicAPIClient

/// A transport that answers by "METHOD /path" (T-0310): each key's replies in order, the last one repeated; a key
/// with no reply throws as URLSession does offline. Every request is recorded, whatever the answer.
actor ScriptedTransport: PlanTransport {
    private(set) var requests: [PlanHTTPRequest] = []
    private var replies: [String: [PlanHTTPReply]]

    init(_ replies: [String: [PlanHTTPReply]]) {
        self.replies = replies
    }

    func send(_ request: PlanHTTPRequest) async throws -> PlanHTTPReply {
        requests.append(request)
        let key = request.method + " " + request.url.path
        guard var queue = replies[key], let reply = queue.first else { throw URLError(.notConnectedToInternet) }
        if queue.count > 1 {
            queue.removeFirst()
            replies[key] = queue
        }
        return reply
    }
}
