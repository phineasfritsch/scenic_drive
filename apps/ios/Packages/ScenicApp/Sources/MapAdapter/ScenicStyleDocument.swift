import Foundation

/// Turns an embedded style into the document the renderer actually loads.
///
/// The generated styles carry a placeholder where the archive belongs -
/// `"sources": { "protomaps": { "type": "vector", "url": "pmtiles://la.pmtiles" } }` - because the
/// generator cannot know the container path the archive will sit at on a phone.
/// `services/tiles/README.md` states the contract from the other side: *"`sources.protomaps.url` is
/// `pmtiles://la.pmtiles`; the app rewrites it to the on-device file URL."* This type is that rewrite,
/// and it is the only place in the app that knows the placeholder's text.
///
/// **The `pmtiles://` prefix is the renderer's, not ours.** MapLibre iOS has read PMTiles archives
/// natively since 6.10.0 (`platform/ios/CHANGELOG.md`, PR #2882); this package pins 6.31.0 exactly.
/// The SDK's `PMTiles.md` gives two forms - `pmtiles://https://` to stream a remote archive and
/// `pmtiles://file://` to read one off the device, including out of the app bundle - which is why the
/// substitution is the literal prefix followed by a file URL's `absoluteString` and nothing more
/// elaborate. No protocol has to be registered and no local tile server exists.
public enum ScenicStyleDocument {
    /// The exact text `make_styles.py` writes into `sources.protomaps.url`.
    ///
    /// A `static let` and not an inline string: `materialize` refuses when it is absent, and the pin
    /// that will guard this (P-ATTR-01, recorded for T-0197) greps an identifier, never a comment.
    public static let archivePlaceholder = "pmtiles://la.pmtiles"

    /// Where the materialised style for `appearance` lives on the device.
    ///
    /// Caches, not Application Support: this file is regenerated from data already in the binary every
    /// time the app resolves a basemap, so it is exactly what the caches directory is for and the
    /// system may delete it freely. `MapStyle.url` returns this for the two protomaps cases, so the
    /// path has one definition and the renderer and the writer cannot disagree about it.
    public static func documentURL(for appearance: MapAppearance) -> URL {
        directoryURL().appending(path: appearance.styleFileName)
    }

    /// The directory `documentURL(for:)` sits in.
    ///
    /// `urls(for:in:)` returns an empty array only in an environment with no caches directory at all;
    /// the temporary directory is the honest degradation there, and it keeps this function total so
    /// that `MapStyle.url` stays a plain non-failing property.
    static func directoryURL() -> URL {
        let caches = FileManager.default.urls(for: .cachesDirectory, in: .userDomainMask).first
        let base = caches ?? FileManager.default.temporaryDirectory
        return base.appending(path: "ScenicDrive/Styles", directoryHint: .isDirectory)
    }

    /// Writes the style for `appearance` with its source pointed at `archiveURL`.
    ///
    /// Returns the document URL, or `nil` when the document could not be produced - either because the
    /// embedded style no longer contains `archivePlaceholder` (the generated JSON changed shape and
    /// this copy was not regenerated) or because the write failed. **Both of those return `nil` rather
    /// than falling back to the unsubstituted style**, because the unsubstituted style still points at
    /// `pmtiles://la.pmtiles` - a relative archive name that resolves to nothing - and would render an
    /// empty map under the Protomaps credit. `BasemapResolver` turns a `nil` here into the demo
    /// basemap, which carries its own credit.
    ///
    /// - Parameters:
    ///   - appearance: which generated style to materialise.
    ///   - archiveURL: a **file** URL for `la.pmtiles` on this device.
    @discardableResult
    public static func materialize(appearance: MapAppearance, archiveURL: URL) -> URL? {
        let template = appearance.styleJSON
        guard template.contains(archivePlaceholder) else {
            return nil
        }
        let document = template.replacingOccurrences(
            of: archivePlaceholder,
            with: "pmtiles://" + archiveURL.absoluteString
        )
        let url = documentURL(for: appearance)
        let data = Data(document.utf8)
        // IDEMPOTENT: nothing is written when the file already IS this document. `BasemapResolver` is
        // called once per selection change and once per appearance change, and SwiftUI may re-run the
        // surrounding work more often than that, so the common case is re-materialising bytes that are
        // already on disk. Skipping it keeps the file the renderer may still be reading in place instead
        // of replacing it, and makes a resolve that changes nothing cost one read.
        if let existing = try? Data(contentsOf: url), existing == data {
            return url
        }
        do {
            try FileManager.default.createDirectory(
                at: url.deletingLastPathComponent(),
                withIntermediateDirectories: true
            )
            // Atomic: a half-written style is a parse error in the renderer, and the app would have no
            // way to tell that from a style that legitimately failed to load.
            try data.write(to: url, options: .atomic)
        } catch {
            return nil
        }
        return url
    }
}
