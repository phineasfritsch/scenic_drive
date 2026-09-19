import Foundation

/// Decides which basemap this device can actually render, and returns it as a `MapStyle` - never as a
/// bare URL.
///
/// **The resolution order, and why it is one type.** The LA archive is 63,520,949 bytes
/// (`services/tiles/work/la.pmtiles.json`: sha256 3b711c79…, region `la`, maxzoom 14) and is never
/// committed, so "is there a basemap" is a question with three answers and exactly one place that
/// asks it:
///
/// 1. **The app bundle.** `Tiles/la.pmtiles` if the folder kept its shape, `la.pmtiles` at the bundle
///    root otherwise - Xcode 26's buildable folders may flatten a synchronized folder's resources, and
///    checking both costs one lookup instead of depending on a behaviour this repository cannot run.
///    The folder is `apps/ios/ScenicDrive/Tiles/`, gitignored, filled by the owner before a device
///    build: `cp services/tiles/work/la.pmtiles apps/ios/ScenicDrive/Tiles/la.pmtiles`.
/// 2. **Application Support.** `tiles/la.pmtiles`, where M4's first-run download sheet will put it.
///    Nothing writes that path today; it is read now so M4 is a download and not a rewiring.
/// 3. **Neither** - `.maplibreDemoTiles`, which credits MapLibre and Natural Earth because that is
///    what it draws. This is the path on the ios-compile runner and on any phone before the copy in
///    step 1, and it is why no build anywhere depends on a 63 MB file being present.
///
/// **Why it returns a `MapStyle`.** A resolver that returned a URL would hand the caller half a fact,
/// and the other half - the credit - would be picked separately somewhere else; that is exactly how a
/// map ends up crediting OpenStreetMap and Protomaps for MapLibre's demo tiles. `MapStyle` carries
/// both halves in one `switch`, so the only thing a caller can do with this answer is render the tiles
/// it names under the credit it names.
public enum BasemapResolver {
    /// The archive's base name and extension, as `services/tiles/build-la.sh` writes them.
    public static let archiveName = "la"
    /// See `archiveName`.
    public static let archiveExtension = "pmtiles"
    /// The folder inside the app bundle that step 1 looks in first.
    public static let bundleSubdirectory = "Tiles"
    /// The path under Application Support that step 2 looks at. M4's download sheet writes here.
    public static let applicationSupportPath = "tiles/la.pmtiles"

    /// The basemap for Los Angeles: the Protomaps style if the archive is on this device, the demo
    /// basemap if it is not.
    ///
    /// Side effect, deliberately not hidden: on success this writes the materialised style document to
    /// the caches directory, because `MapStyle.protomapsLALight/.protomapsLADark` name that file as
    /// their `url`. Those cases are therefore only ever returned **after** the document exists.
    ///
    /// - Parameters:
    ///   - appearance: which generated style to render. Defaults to `.light` so the call site that
    ///     switches the walking skeleton over is one line (`FeatureScenicHome` is not this task's to
    ///     edit; the change is recorded for T-0178).
    ///   - bundle: the bundle to search. `.main` in the app; a parameter so the lookup is stateable.
    public static func losAngeles(appearance: MapAppearance = .light, bundle: Bundle = .main) -> MapStyle {
        guard let archiveURL = archiveURL(in: bundle) else {
            return .maplibreDemoTiles
        }
        guard ScenicStyleDocument.materialize(appearance: appearance, archiveURL: archiveURL) != nil else {
            return .maplibreDemoTiles
        }
        return appearance.protomapsStyle
    }

    /// Steps 1 and 2 of the order above: where `la.pmtiles` is on this device, or `nil`.
    ///
    /// The bundle lookups need no existence check - `Bundle.url(forResource:…)` returns `nil` for a
    /// resource that was not copied in. The Application Support path does need one, because building a
    /// URL under a directory says nothing about whether anything was ever downloaded to it.
    public static func archiveURL(in bundle: Bundle = .main) -> URL? {
        if let bundled = bundle.url(
            forResource: archiveName,
            withExtension: archiveExtension,
            subdirectory: bundleSubdirectory
        ) {
            return bundled
        }
        if let flattened = bundle.url(forResource: archiveName, withExtension: archiveExtension) {
            return flattened
        }
        let fileManager = FileManager.default
        guard let support = fileManager.urls(for: .applicationSupportDirectory, in: .userDomainMask).first else {
            return nil
        }
        let downloaded = support.appending(path: applicationSupportPath)
        // `percentEncoded: false`: `path(percentEncoded:)` is the URL's path as the filesystem spells
        // it, and a container directory with a space in it would otherwise be asked about under its
        // %20 name and answered "no".
        guard fileManager.fileExists(atPath: downloaded.path(percentEncoded: false)) else {
            return nil
        }
        return downloaded
    }
}
