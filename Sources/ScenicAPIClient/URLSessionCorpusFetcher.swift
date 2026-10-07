import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import PlaceStore

/// The app's `CorpusFetcher` (T-0300 O5, T-0305 R1-R3, R6): the publisher's manifest and the corpus file it names,
/// over URLSession, streamed to disk and resumable.
///
/// The corpus is the manifest's sibling `corpus-<version>.sqlite` (R1: the manifest carries no URL). It is streamed
/// into a resume file `corpus-<sha256>.part` beside the destination - keyed by the manifest's hash, so one corpus
/// never resumes into another's bytes - and renamed to the destination only when exactly `manifest.bytes` arrived.
/// PlaceStore's `CorpusUpdater.stage` then verifies the bytes and the hash; nothing here trusts the server further.
public struct URLSessionCorpusFetcher: CorpusFetcher {
    public let manifestURL: URL
    public let wifiOnly: Bool
    public let timeout: TimeInterval
    /// Applied to the session configuration after `configuration(wifiOnly:)`; a test registers a stub URLProtocol.
    private let configure: @Sendable (URLSessionConfiguration) -> Void
    /// (bytes on disk, the manifest's byte count), after every chunk written.
    private let onProgress: @Sendable (Int, Int) -> Void

    public init(manifestURL: URL, wifiOnly: Bool, timeout: TimeInterval = 60,
                configure: @escaping @Sendable (URLSessionConfiguration) -> Void = { _ in },
                onProgress: @escaping @Sendable (Int, Int) -> Void = { _, _ in }) {
        self.manifestURL = manifestURL
        self.wifiOnly = wifiOnly
        self.timeout = timeout
        self.configure = configure
        self.onProgress = onProgress
    }

    /// The shipping configuration: no cellular data when the user keeps Wi-Fi only on (the default, R6).
    public static func configuration(wifiOnly: Bool) -> URLSessionConfiguration {
        let configuration = URLSessionConfiguration.default
        configuration.allowsCellularAccess = !wifiOnly
        return configuration
    }

    /// Where the corpus a manifest names is served: the manifest's sibling `corpus-<version>.sqlite` (R1).
    public func corpusURL(for manifest: CorpusManifest) -> URL {
        manifestURL.deletingLastPathComponent().appendingPathComponent("corpus-\(manifest.version).sqlite")
    }

    /// The resume file for `manifest` beside `destination`.
    public func resumeFile(for manifest: CorpusManifest, beside destination: URL) -> URL {
        destination.deletingLastPathComponent().appendingPathComponent("corpus-\(manifest.sha256).part")
    }

    /// The manifest's bytes; a reply other than 200 is `CorpusFetchError.status`.
    public func fetchManifest() async throws -> Data {
        let session = session(delegate: nil)
        defer { session.finishTasksAndInvalidate() }
        let request = URLRequest(url: manifestURL, timeoutInterval: timeout)
        return try await withCheckedThrowingContinuation { continuation in
            session.dataTask(with: request) { data, response, error in
                if let error {
                    continuation.resume(throwing: CorpusFetchError.transport(code: (error as? URLError)?.code.rawValue ?? -1))
                    return
                }
                let status = (response as? HTTPURLResponse)?.statusCode ?? 0
                guard status == 200 else {
                    continuation.resume(throwing: CorpusFetchError.status(status))
                    return
                }
                continuation.resume(returning: data ?? Data())
            }.resume()
        }
    }

    /// Writes the corpus `manifest` names to `destination` (R3): resumes from the resume file when one holds part of
    /// it, sends no request when it holds all of it, and renames it to `destination` only at exactly
    /// `manifest.bytes`. A thrown `CorpusFetchError` leaves no file at `destination`.
    public func fetch(_ manifest: CorpusManifest, to destination: URL) async throws {
        let files = FileManager()
        let part = resumeFile(for: manifest, beside: destination)
        try? files.removeItem(at: destination)
        var have = ((try? files.attributesOfItem(atPath: part.path))?[.size] as? NSNumber)?.intValue ?? 0
        if have > manifest.bytes {
            try? files.removeItem(at: part)
            have = 0
        }
        if have < manifest.bytes {
            if !files.fileExists(atPath: part.path) {
                guard files.createFile(atPath: part.path, contents: nil) else {
                    throw CorpusFetchError.transport(code: URLError.Code.cannotCreateFile.rawValue)
                }
            }
            var request = URLRequest(url: corpusURL(for: manifest), timeoutInterval: timeout)
            if have > 0 {
                request.setValue("bytes=\(have)-", forHTTPHeaderField: "Range")
            }
            let delegate = CorpusDownloadDelegate(file: part, offset: have, expected: manifest.bytes,
                                                  onProgress: onProgress)
            let session = session(delegate: delegate)
            defer { session.finishTasksAndInvalidate() }
            do {
                have = try await delegate.run(request, in: session)
            } catch let error as CorpusFetchError {
                switch error {
                case .status, .longBody: try? files.removeItem(at: part)
                case .shortBody, .transport: break
                }
                throw error
            }
            guard have == manifest.bytes else {
                throw CorpusFetchError.shortBody(received: have, expected: manifest.bytes)
            }
        }
        try files.moveItem(at: part, to: destination)
        onProgress(have, manifest.bytes)
    }

    func session(delegate: (any URLSessionDelegate)?) -> URLSession {
        let configuration = Self.configuration(wifiOnly: wifiOnly)
        configure(configuration)
        return URLSession(configuration: configuration, delegate: delegate, delegateQueue: nil)
    }
}
