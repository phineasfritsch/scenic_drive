import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
@testable import Telemetry

/// A URLProtocol that stands in for the network UNDER URLSessionTelemetryTransport (T-0355 round 1, B1): it captures
/// every URLRequest the production transport handed its session, as a TelemetryRequest, and answers one canned
/// status.
///
/// Registered only on a session the test builds (`session(answering:)`), never globally. On Darwin the body reaches
/// a URLProtocol as `httpBodyStream`, on swift-corelibs-foundation as `httpBody`; both are read. Header names are
/// lowercased (HTTP field names are case-insensitive; corelibs canonicalizes them).
final class StubTelemetryURLProtocol: URLProtocol {
    private static let lock = NSLock()
    nonisolated(unsafe) private static var captured: [TelemetryRequest] = []
    nonisolated(unsafe) private static var status = 599

    /// A fresh session whose only protocol is this stub, answering `status`; the capture list is emptied.
    static func session(answering status: Int) -> URLSession {
        lock.lock()
        captured = []
        self.status = status
        lock.unlock()
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubTelemetryURLProtocol.self]
        return URLSession(configuration: configuration)
    }

    /// Every request the stub saw since `session(answering:)`.
    static func seen() -> [TelemetryRequest] {
        lock.lock()
        defer { lock.unlock() }
        return captured
    }

    override class func canInit(with request: URLRequest) -> Bool { true }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let request = self.request
        let body = request.httpBody ?? Self.drain(request.httpBodyStream)
        // uniqueKeysWithValues traps if two spellings of one name were both set.
        let headers = Dictionary(uniqueKeysWithValues: (request.allHTTPHeaderFields ?? [:]).map {
            ($0.key.lowercased(), $0.value)
        })
        let seen = TelemetryRequest(url: request.url!, method: request.httpMethod ?? "", headers: headers, body: body)
        Self.lock.lock()
        Self.captured.append(seen)
        let status = Self.status
        Self.lock.unlock()
        let response = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: "HTTP/1.1",
                                       headerFields: ["content-type": "application/json"])!
        client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
        client?.urlProtocol(self, didLoad: Data("{}".utf8))
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
