import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// A scripted network UNDER URLSessionCorpusFetcher (T-0305 R7): it records every request's URL and Range header and
/// plays the steps `script` returns for it - a status with headers, body chunks, then a clean finish or a failure.
/// Registered only on the configuration the test hands the fetcher, never globally.
final class StubCorpusURLProtocol: URLProtocol {
    enum Step {
        case respond(Int, [String: String])
        case data(Data)
        case fail(URLError.Code)
        case finish
    }

    struct Seen: Equatable {
        let url: URL
        let range: String?
    }

    private static let lock = NSLock()
    nonisolated(unsafe) private static var seen: [Seen] = []
    nonisolated(unsafe) private static var script: (Seen) -> [Step] = { _ in [] }

    /// Empties the record and installs `script`.
    static func reset(_ script: @escaping (Seen) -> [Step]) {
        lock.lock()
        seen = []
        self.script = script
        lock.unlock()
    }

    static func requests() -> [Seen] {
        lock.lock()
        defer { lock.unlock() }
        return seen
    }

    override class func canInit(with request: URLRequest) -> Bool { true }

    override class func canonicalRequest(for request: URLRequest) -> URLRequest { request }

    override func startLoading() {
        let range = (request.allHTTPHeaderFields ?? [:]).first { $0.key.lowercased() == "range" }?.value
        let one = Seen(url: request.url!, range: range)
        Self.lock.lock()
        Self.seen.append(one)
        let steps = Self.script(one)
        Self.lock.unlock()
        for step in steps {
            switch step {
            case .respond(let status, let headers):
                let response = HTTPURLResponse(url: request.url!, statusCode: status, httpVersion: "HTTP/1.1",
                                               headerFields: headers)!
                client?.urlProtocol(self, didReceive: response, cacheStoragePolicy: .notAllowed)
            case .data(let data):
                client?.urlProtocol(self, didLoad: data)
            case .fail(let code):
                client?.urlProtocol(self, didFailWithError: URLError(code))
                return
            case .finish:
                client?.urlProtocolDidFinishLoading(self)
                return
            }
        }
    }

    override func stopLoading() {}
}
