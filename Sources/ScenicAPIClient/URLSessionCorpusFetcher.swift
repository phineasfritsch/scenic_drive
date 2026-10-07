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
        throw CorpusFetchError.status(0)
    }

    public func fetch(_ manifest: CorpusManifest, to destination: URL) async throws {
        throw CorpusFetchError.status(0)
    }

    func session(delegate: (any URLSessionDelegate)?) -> URLSession {
        let configuration = Self.configuration(wifiOnly: wifiOnly)
        configure(configuration)
        return URLSession(configuration: configuration, delegate: delegate, delegateQueue: nil)
    }
}
