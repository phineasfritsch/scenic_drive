import Foundation
import Observation
import PlaceStore
import ScenicAPIClient

/// The app's corpus download (T-0305 R1-R6), in PlanAdapter because it is the only apps/ios importer of
/// ScenicAPIClient (T-0294 R1) and the shell imports no root module.
///
/// `launch(wifiOnlyKey:)` runs once, from the shell's `init()`, before any feature opens a PlaceStore: it activates a
/// verified pending download through `LaunchCorpus.choose` (T-0300 O7) and records which corpus the features open - the
/// active download, else the bundled fallback. `start()` fetches the manifest from UserDefaults `corpus.manifest.url`
/// (R1: absent or not https - nothing is ever sent), decides, and stages the download; it is used from the NEXT cold
/// launch. Wi-Fi only is read from Settings' key when the download starts (R6), absent = on.
@MainActor
@Observable
public final class LiveCorpus {
    public static let manifestURLKey = "corpus.manifest.url"

    public enum Phase: Equatable, Sendable { case idle, checking, downloading, ready, upToDate, unavailable, failed }

    public private(set) var phase: Phase = .idle
    /// 0...1 while downloading.
    public private(set) var fraction: Double = 0
    /// A manifest URL is configured and no downloaded corpus is active: the first-run sheet offers the download.
    public let offersDownload: Bool

    private let directory: URL?
    private let manifestURL: URL?
    private let wifiOnlyKey: String

    init(directory: URL?, manifestURL: URL?, wifiOnlyKey: String, offersDownload: Bool) {
        self.directory = directory
        self.manifestURL = manifestURL
        self.wifiOnlyKey = wifiOnlyKey
        self.offersDownload = offersDownload
    }

    public static func launch(wifiOnlyKey: String) -> LiveCorpus {
        let defaults = UserDefaults.standard
        let manifestURL = defaults.string(forKey: manifestURLKey).flatMap(URL.init(string:)).flatMap {
            $0.scheme == "https" ? $0 : nil
        }
        let directory = try? FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                     appropriateFor: nil, create: true)
            .appendingPathComponent("Corpus", isDirectory: true)
        var hasDownload = false
        if let directory {
            try? FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            let launched = LaunchCorpus.choose(updater: CorpusUpdater(directory: directory, drives: DriveSessionLock()),
                                             fallback: LaunchCorpus.bundledFallback(in: .main))
            hasDownload = launched.corpus == CorpusSlots(directory: directory).active
        }
        return LiveCorpus(directory: directory, manifestURL: manifestURL, wifiOnlyKey: wifiOnlyKey,
                          offersDownload: manifestURL != nil && directory != nil && !hasDownload)
    }

    /// One line for the sheet.
    public var statusText: String {
        switch phase {
        case .idle: return "Download the places for your region so search and Surprise Me know every overlook."
        case .checking: return "Checking for the latest places…"
        case .downloading: return "Downloading places… \(Int((fraction * 100).rounded(.down)))%"
        case .ready: return "Downloaded. The new places arrive the next time Scenic Drive starts."
        case .upToDate: return "Your places are up to date."
        case .unavailable: return "No places download fits this version of the app yet."
        case .failed: return "The download stopped. It resumes where it left off when you try again."
        }
    }

    public var isWorking: Bool { phase == .checking || phase == .downloading }

    /// Fetches the manifest and, when it says so, downloads and verifies the corpus into the pending slot.
    public func start() {
        guard !isWorking, let directory, let manifestURL else { return }
        let wifiOnly = UserDefaults.standard.object(forKey: wifiOnlyKey) as? Bool ?? true
        let fetcher = URLSessionCorpusFetcher(manifestURL: manifestURL, wifiOnly: wifiOnly,
                                              onProgress: { [weak self] got, total in
            Task { @MainActor in self?.fraction = total > 0 ? Double(got) / Double(total) : 0 }
        })
        let updater = CorpusUpdater(directory: directory, drives: DriveSessionLock())
        let active = updater.slots.active
        let activeVersion = FileManager.default.fileExists(atPath: active.path)
            ? (try? PlaceStore(path: active.path).meta().corpusVersion) : nil
        let build = Int(Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String ?? "") ?? 0
        phase = .checking
        fraction = 0
        Task { @MainActor in
            do {
                let json = try await fetcher.fetchManifest()
                switch try CorpusUpdater.decide(manifestJSON: json, appBuild: build, activeVersion: activeVersion) {
                case .download(let manifest):
                    phase = .downloading
                    try await updater.stage(manifest, fetcher: fetcher)
                    phase = .ready
                case .upToDate:
                    phase = .upToDate
                case .refusedSchemaVersion, .refusedAppBuild:
                    phase = .unavailable
                }
            } catch {
                phase = .failed
            }
        }
    }
}
