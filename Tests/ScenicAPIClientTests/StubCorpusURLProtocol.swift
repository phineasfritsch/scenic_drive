import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif

/// A scripted network UNDER URLSessionCorpusFetcher (T-0305 R7): it records every request's URL and Range header and
/// plays the steps `script` returns for it - a status with headers, body chunks, then a clean finish or a failure.
/// Registered only on the configuration the test hands the fetcher, never globally.
///
/// It honours cancellation the way URLSession's own loader does: it plays the steps on a queue of its own, never on
/// the loader's thread `startLoading()` runs on, and after every step that is not the last it waits up to
/// `pause` for `stopLoading()`, and once stopped it delivers nothing more, so a delegate's `dataTask.cancel()` is the
/// task's last event and the task completes with `URLError.cancelled` (-999), never with the scripted finish. The
/// session reports the cancellation itself; a second report from here would complete the task twice.
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

    /// How long the stub gives the delegate to cancel after each step before it plays the next one.
    static let pause: DispatchTimeInterval = .milliseconds(100)

    private static let lock = NSLock()
    nonisolated(unsafe) private static var seen: [Seen] = []
    nonisolated(unsafe) private static var script: (Seen) -> [Step] = { _ in [] }

    private let stopped = DispatchSemaphore(value: 0)
    private let stopLock = NSLock()
    private var cancelled = false

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

    /// True once `stopLoading()` has run.
    var isStopped: Bool {
        stopLock.lock()
        defer { stopLock.unlock() }
        return cancelled
    }

    override func startLoading() {
        let range = (request.allHTTPHeaderFields ?? [:]).first { $0.key.lowercased() == "range" }?.value
        let one = Seen(url: request.url!, range: range)
        Self.lock.lock()
        Self.seen.append(one)
        let steps = Self.script(one)
        Self.lock.unlock()
        nonisolated(unsafe) let stub = self
        DispatchQueue.global().async { stub.play(steps) }
    }

    /// Plays `steps` off the loader's own thread, so a cancel the delegate issues meanwhile reaches `stopLoading()`.
    private func play(_ steps: [Step]) {
        for (index, step) in steps.enumerated() {
            guard !isStopped else { return }
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
            if index < steps.count - 1, stopped.wait(timeout: .now() + Self.pause) == .success {
                return
            }
        }
    }

    override func stopLoading() {
        stopLock.lock()
        let first = !cancelled
        cancelled = true
        stopLock.unlock()
        if first { stopped.signal() }
    }
}
