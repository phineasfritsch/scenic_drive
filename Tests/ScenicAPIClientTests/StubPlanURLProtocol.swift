import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import ScenicAPIClient

/// A URLProtocol that stands in for the network UNDER URLSessionPlanTransport: it captures every URLRequest the
/// production transport handed its session, as a PlanHTTPRequest, and answers one canned reply.
///
/// Registered only on a session the test builds (`session(answering:)`), never globally. On Darwin the body reaches
/// a URLProtocol as `httpBodyStream`, on swift-corelibs-foundation as `httpBody`; both are read. Header names are
/// lowercased (HTTP field names are case-insensitive; corelibs canonicalizes them).
final class StubPlanURLProtocol: URLProtocol {
    private static let lock = NSLock()
    nonisolated(unsafe) private static var captured: [PlanHTTPRequest] = []
    nonisolated(unsafe) private static var timeouts: [TimeInterval] = []
    nonisolated(unsafe) private static var reply = PlanHTTPReply(status: 599, body: Data())

    /// A fresh session whose only protocol is this stub, answering `reply`; the capture list is emptied.
    static func session(answering reply: PlanHTTPReply) -> URLSession {
        lock.lock()
        captured = []
        timeouts = []
        self.reply = reply
        lock.unlock()
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubPlanURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    /// Every request the stub saw since `session(answering:)`, and the timeout each carried.
    static func seen() -> (requests: [PlanHTTPRequest], timeouts: [TimeInterval]) {
        lock.lock()
        defer { lock.unlock() }
        return (captured, timeouts)
    }

    override class func canInit(with request: URLRequest) -> Bool { true }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let request = self.request
        let body = request.httpBody ?? Self.drain(request.httpBodyStream)
        // Header names are case-insensitive and swift-corelibs-foundation hands them on as "Content-Type"; they
        // are compared lowercased. uniqueKeysWithValues traps if two spellings of one name were both set.
        let headers = Dictionary(uniqueKeysWithValues: (request.allHTTPHeaderFields ?? [:]).map {
            ($0.key.lowercased(), $0.value)
        })
        let seen = PlanHTTPRequest(url: request.url!, method: request.httpMethod ?? "", headers: headers, body: body)
        Self.lock.lock()
        Self.captured.append(seen)
        Self.timeouts.append(request.timeoutInterval)
        let reply = Self.reply
        Self.lock.unlock()
        let response = HTTPURLResponse(url: request.url!, statusCode: reply.status, httpVersion: "HTTP/1.1",
                                       headerFields: ["content-type": "application/json"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: reply.body)
        client?.urlProtocolDidFinishLoading(self)
    }

    override func stopLoading() {}

    private static func drain(_ stream: InputStream?) -> Data {
        guard let stream else { return Data() }
        stream.open()
        defer { stream.close() }
        var data = Data()
        var buffer = [UInt8](repeating: 0, count: 4096)
        while stream.hasBytesAvailable {
            let read = stream.read(&buffer, maxLength: buffer.count)
            if read <= 0 { break }
            data.append(buffer, count: read)
        }
        return data
    }
}
