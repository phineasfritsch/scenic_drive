import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import PlaceStore
import ScenicAPIClient
import Testing

/// T-0305 R3/R6/R7: the shipping `URLSessionCorpusFetcher` over a scripted URLProtocol. The fetch table is the cross
/// product of the resume file left by an earlier attempt {absent, 0 bytes, partial, complete-but-unverified, longer
/// than the corpus} and the server's behaviour {honours Range, ignores Range, 404, short body, dropped connection,
/// long body, a 206 at the wrong byte}; each row's outcome, the requests made, and the whole directory (destination
/// and resume file) are computed by `expected(_:_:)` from the row and compared by FULL equality.
@Suite(.serialized)
struct URLSessionCorpusFetcherTests {
    enum Prefix: CaseIterable { case absent, empty, partial, complete, over }
    enum Server: CaseIterable { case honours, ignoresRange, missing, short, drop, long, wrongRange, unwritable }
    enum Outcome: Equatable { case fetched, failed(CorpusFetchError) }

    struct Result: Equatable {
        let outcome: Outcome
        let requests: [StubCorpusURLProtocol.Seen]
        let destination: Data?
        let part: Data?
        let lastProgress: [Int]?
        /// The stub's `unplayed()`: a refusal cancels its task on every platform, so the rest of the script never plays.
        let unplayed: [Int]
    }

    final class Progress: @unchecked Sendable {
        private let lock = NSLock()
        private var last: [Int]?
        func record(_ got: Int, _ total: Int) { lock.lock(); last = [got, total]; lock.unlock() }
        func value() -> [Int]? { lock.lock(); defer { lock.unlock() }; return last }
    }

    static let size = 4096
    static let payload = Data((0..<size).map { UInt8(($0 * 7 + 3) % 256) })
    static let manifest = CorpusManifest(version: "20261007T000000Z", schemaVersion: 3, minAppBuild: 1,
                                         sha256: String(repeating: "0a", count: 32), bytes: size)
    static let manifestURL = URL(string: "https://corpus.example.test/la/manifest.json")!
    static let corpusURL = URL(string: "https://corpus.example.test/la/corpus-20261007T000000Z.sqlite")!
    static let partialBytes = 1000

    static func start(_ prefix: Prefix) -> Int? {
        switch prefix {
        case .absent, .empty, .over: return 0
        case .partial: return partialBytes
        case .complete: return nil
        }
    }

    static func offset(_ range: String?) -> Int {
        guard let range, range.hasPrefix("bytes="), range.hasSuffix("-") else { return 0 }
        return Int(range.dropFirst(6).dropLast()) ?? 0
    }

    static func script(_ server: Server) -> (StubCorpusURLProtocol.Seen) -> [StubCorpusURLProtocol.Step] {
        { seen in
            let at = offset(seen.range)
            let head: StubCorpusURLProtocol.Step = at > 0
                ? .respond(206, ["Content-Range": "bytes \(at)-\(size - 1)/\(size)"]) : .respond(200, [:])
            let rest = payload.subdata(in: at..<size)
            let third = rest.count / 3
            let chunks: [StubCorpusURLProtocol.Step] = [.data(rest.prefix(third)), .data(rest.dropFirst(third).prefix(third)),
                                                        .data(rest.dropFirst(2 * third))]
            switch server {
            case .honours: return [head] + chunks + [.finish]
            case .unwritable: return [head, .awaitCancel] + chunks + [.finish]
            case .ignoresRange: return [.respond(200, [:]), .data(payload), .finish]
            case .missing: return [.respond(404, [:]), .awaitCancel, .data(Data("not found".utf8)), .finish]
            case .short: return [head, .data(payload.subdata(in: at..<(size - 10))), .finish]
            case .drop: return [head, .data(payload.subdata(in: at..<(at + 100))), .fail(.networkConnectionLost)]
            case .long: return [head] + chunks + [.data(Data([0])), .awaitCancel, .finish]
            case .wrongRange:
                // No Range sent: a 206 from byte 0. A Range sent: a 206 from a byte that is not the one asked for.
                let from = at == 0 ? 0 : 7
                return [.respond(206, ["Content-Range": "bytes \(from)-\(size - 1)/\(size)"]), .awaitCancel,
                        .data(payload.subdata(in: from..<size)), .finish]
            }
        }
    }

    /// The ruling (R3), stated apart from the fetcher.
    static func expected(_ prefix: Prefix, _ server: Server) -> Result {
        guard let at = start(prefix) else {
            return Result(outcome: .fetched, requests: [], destination: payload, part: nil, lastProgress: [size, size],
                          unplayed: [])
        }
        let request = StubCorpusURLProtocol.Seen(url: corpusURL, range: at > 0 ? "bytes=\(at)-" : nil)
        // The refusal cancels the task where the script awaits it, so every step after that mark is never played.
        let steps = script(server)(request)
        let mark = steps.firstIndex { if case .awaitCancel = $0 { return true } else { return false } }
        let unplayed = mark.map { [steps.count - $0 - 1] } ?? []
        func failed(_ error: CorpusFetchError, part: Data?) -> Result {
            Result(outcome: .failed(error), requests: [request], destination: nil, part: part, lastProgress: nil,
                   unplayed: unplayed)
        }
        switch server {
        case .honours, .ignoresRange:
            return Result(outcome: .fetched, requests: [request], destination: payload, part: nil,
                          lastProgress: [size, size], unplayed: unplayed)
        case .missing: return failed(.status(404), part: nil)
        case .short: return failed(.shortBody(received: size - 10, expected: size), part: payload.prefix(size - 10))
        case .drop: return failed(.transport(code: URLError.Code.networkConnectionLost.rawValue),
                                  part: payload.prefix(at + 100))
        case .long: return failed(.longBody(expected: size), part: nil)
        case .wrongRange: return failed(.status(206), part: nil)
        case .unwritable: return failed(.transport(code: URLError.Code.cannotWriteToFile.rawValue), part: nil)
        }
    }

    static func run(_ prefix: Prefix, _ server: Server) async throws -> Result {
        let directory = FileManager().temporaryDirectory
            .appendingPathComponent("t0305-fetch-\(UUID().uuidString)", isDirectory: true)
        defer { try? FileManager().removeItem(at: directory) }
        let destination = CorpusSlots(directory: directory).staging
        try FileManager().createDirectory(at: destination.deletingLastPathComponent(), withIntermediateDirectories: true)
        let progress = Progress()
        let fetcher = URLSessionCorpusFetcher(manifestURL: manifestURL, wifiOnly: true,
                                              configure: { $0.protocolClasses = [StubCorpusURLProtocol.self] },
                                              onProgress: { progress.record($0, $1) })
        let part = fetcher.resumeFile(for: manifest, beside: destination)
        switch prefix {
        case .absent: break
        case .empty: try Data().write(to: part)
        case .partial: try payload.prefix(partialBytes).write(to: part)
        case .complete: try payload.write(to: part)
        case .over: try (payload + Data([9])).write(to: part)
        }
        let steps = script(server)
        // `unwritable`: the resume file is gone by the time the response arrives, so the delegate cannot open it.
        StubCorpusURLProtocol.reset { seen in
            if server == .unwritable { try? FileManager().removeItem(at: part) }
            return steps(seen)
        }
        var outcome = Outcome.fetched
        do {
            try await fetcher.fetch(manifest, to: destination)
        } catch let error as CorpusFetchError {
            outcome = .failed(error)
        }
        return Result(outcome: outcome, requests: StubCorpusURLProtocol.requests(),
                      destination: try? Data(contentsOf: destination), part: try? Data(contentsOf: part),
                      lastProgress: outcome == .fetched ? progress.value() : nil,
                      unplayed: StubCorpusURLProtocol.unplayed())
    }

    @Test func fetchTableOverEveryResumeFileAndServer() async throws {
        for prefix in Prefix.allCases {
            for server in Server.allCases {
                let got = try await Self.run(prefix, server)
                #expect(got == Self.expected(prefix, server), "\(prefix) x \(server)")
            }
        }
    }

    /// No row ignores the resume file: every server's expectation differs between no resume file and a partial one.
    @Test func noFetchRowIgnoresTheResumeFile() {
        for server in Server.allCases {
            #expect(Self.expected(.absent, server) != Self.expected(.partial, server), "\(server)")
            #expect(Self.expected(.partial, server) != Self.expected(.complete, server), "\(server)")
        }
    }

    @Test func wifiOnlyRefusesCellularAndTheNamesAreRuled() {
        #expect(URLSessionCorpusFetcher.configuration(wifiOnly: true).allowsCellularAccess == false)
        #expect(URLSessionCorpusFetcher.configuration(wifiOnly: false).allowsCellularAccess == true)
        let fetcher = URLSessionCorpusFetcher(manifestURL: Self.manifestURL, wifiOnly: true)
        #expect(fetcher.corpusURL(for: Self.manifest) == Self.corpusURL)
        #expect(fetcher.resumeFile(for: Self.manifest, beside: URL(fileURLWithPath: "/c/tmp/corpus-staging.sqlite"))
            == URL(fileURLWithPath: "/c/tmp/corpus-\(String(repeating: "0a", count: 32)).part"))
    }

    @Test func manifestFetchReturnsTheBodyOrATypedError() async throws {
        let fetcher = URLSessionCorpusFetcher(manifestURL: Self.manifestURL, wifiOnly: false,
                                              configure: { $0.protocolClasses = [StubCorpusURLProtocol.self] })
        let body = Data("{\"version\":\"x\"}".utf8)
        let replies: [([StubCorpusURLProtocol.Step], Swift.Result<Data, CorpusFetchError>)] = [
            ([.respond(200, [:]), .data(body), .finish], .success(body)),
            ([.respond(503, [:]), .data(body), .finish], .failure(.status(503))),
            ([.fail(.notConnectedToInternet)], .failure(.transport(code: URLError.Code.notConnectedToInternet.rawValue))),
        ]
        for (steps, want) in replies {
            StubCorpusURLProtocol.reset { _ in steps }
            let got: Swift.Result<Data, CorpusFetchError>
            do { got = .success(try await fetcher.fetchManifest()) } catch let error as CorpusFetchError { got = .failure(error) }
            #expect(got == want)
            #expect(StubCorpusURLProtocol.requests() == [StubCorpusURLProtocol.Seen(url: Self.manifestURL, range: nil)])
        }
    }

    /// Records what a plain URLSession reports to a delegate that cancels its task on the first body chunk.
    final class CancelOnFirstData: NSObject, URLSessionDataDelegate, @unchecked Sendable {
        private let lock = NSLock()
        private var chunks = 0
        private var continuation: CheckedContinuation<(Int, (any Error)?), Never>?

        func run(_ request: URLRequest, in session: URLSession) async -> (Int, (any Error)?) {
            await withCheckedContinuation { continuation in
                lock.lock(); self.continuation = continuation; lock.unlock()
                session.dataTask(with: request).resume()
            }
        }

        func urlSession(_ session: URLSession, dataTask: URLSessionDataTask, didReceive data: Data) {
            lock.lock(); chunks += 1; lock.unlock()
            dataTask.cancel()
        }

        func urlSession(_ session: URLSession, task: URLSessionTask, didCompleteWithError error: (any Error)?) {
            lock.lock()
            let continuation = self.continuation
            self.continuation = nil
            let seen = chunks
            lock.unlock()
            continuation?.resume(returning: (seen, error))
        }
    }

    /// The stub models cancellation as URLSession does: a task cancelled mid-body gets no further chunk and no clean
    /// finish, and completes with URLError.cancelled (-999).
    @Test func stubCompletesACancelledTaskWithURLErrorCancelled() async {
        let configuration = URLSessionConfiguration.ephemeral
        configuration.protocolClasses = [StubCorpusURLProtocol.self]
        let delegate = CancelOnFirstData()
        let session = URLSession(configuration: configuration, delegate: delegate, delegateQueue: nil)
        defer { session.invalidateAndCancel() }
        StubCorpusURLProtocol.reset { _ in
            [.respond(200, [:]), .data(Data([1])), .awaitCancel, .data(Data([2])), .data(Data([3])), .finish]
        }
        let (chunks, error) = await delegate.run(URLRequest(url: Self.corpusURL), in: session)
        #expect(chunks == 1)
        #expect((error as? URLError)?.code == .cancelled)
        #expect(StubCorpusURLProtocol.requests() == [StubCorpusURLProtocol.Seen(url: Self.corpusURL, range: nil)])
        #expect(StubCorpusURLProtocol.unplayed() == [3])
    }
}
