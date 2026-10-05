import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// The production transport: one `URLSession` data task per request.
///
/// A completion handler bridged by a checked continuation rather than `URLSession.data(for:)`, because the
/// async API's availability differs between Darwin and swift-corelibs-foundation and this target builds on
/// both (the CLI's GraphHopperRouteSource uses the same data-task shape). It throws only when no HTTP reply
/// arrived; any status, 5xx included, is returned for `PlanResponseReader` to map.
public struct URLSessionPlanTransport: PlanTransport {
    public let timeout: TimeInterval
    /// The session every request goes through: `.shared` in the app; a test hands in one whose configuration
    /// registers a stub URLProtocol, so it reads the URLRequest this transport built (T-0251 pre-review MC).
    public let session: URLSession

    public init(timeout: TimeInterval = 30, session: URLSession = .shared) {
        self.timeout = timeout
        self.session = session
    }

    public func send(_ request: PlanHTTPRequest) async throws -> PlanHTTPReply {
        var urlRequest = URLRequest(url: request.url, timeoutInterval: timeout)
        urlRequest.httpMethod = request.method
        for (field, value) in request.headers {
            urlRequest.setValue(value, forHTTPHeaderField: field)
        }
        urlRequest.httpBody = request.body
        let built = urlRequest
        return try await withCheckedThrowingContinuation { continuation in
            let task = session.dataTask(with: built) { data, response, error in
                if let error {
                    continuation.resume(throwing: error)
                    return
                }
                guard let http = response as? HTTPURLResponse else {
                    continuation.resume(throwing: URLError(.badServerResponse))
                    return
                }
                continuation.resume(returning: PlanHTTPReply(status: http.statusCode, body: data ?? Data()))
            }
            task.resume()
        }
    }
}
