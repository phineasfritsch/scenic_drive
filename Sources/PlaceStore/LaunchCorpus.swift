import Foundation

/// Which corpus file the app opens (T-0305 R4; T-0270 F7: a downloaded corpus is preferred over the bundled
/// fallback). The app calls `choose(updater:fallback:)` ONCE, at a cold launch, before any PlaceStore is opened; every
/// feature that opens a corpus then asks `url(fallback:)` instead of reading its bundle directly.
public enum LaunchCorpus {
    /// The bundled fallback corpus's resource name (T-0270), `corpus-fallback.sqlite` at the bundle root or in Corpus/.
    public static let fallbackName = "corpus-fallback"

    private static let lock = NSLock()
    /// The active slot chosen by the last `choose`, nil when no downloaded corpus exists. Written once per launch under
    /// `lock`, before any reader runs.
    nonisolated(unsafe) private static var downloaded: URL?

    /// The bundled fallback corpus in `bundle`, nil when the bundle carries none.
    public static func bundledFallback(in bundle: Bundle) -> URL? {
        bundle.url(forResource: fallbackName, withExtension: "sqlite")
            ?? bundle.url(forResource: fallbackName, withExtension: "sqlite", subdirectory: "Corpus")
    }

    /// Runs `updater.openForLaunch(isColdLaunch: true)` - activating a verified pending download, or undoing a bad
    /// one - then records and returns the corpus to open: the active slot when that file exists, else `fallback`.
    public static func choose(updater: CorpusUpdater, fallback: URL?) -> CorpusLaunch {
        let activation = updater.openForLaunch(isColdLaunch: true)
        let active = updater.slots.active
        let chosen: URL? = updater.slots.exists(active) ? active : nil
        lock.lock()
        downloaded = chosen
        lock.unlock()
        return CorpusLaunch(activation: activation, corpus: chosen ?? fallback)
    }

    /// The corpus a feature opens: the downloaded corpus `choose` chose this launch, else `fallback`.
    public static func url(fallback: URL?) -> URL? {
        lock.lock()
        defer { lock.unlock() }
        return downloaded ?? fallback
    }
}
