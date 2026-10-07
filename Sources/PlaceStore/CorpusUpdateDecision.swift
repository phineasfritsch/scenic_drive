/// What `CorpusUpdater.decide` says to do with a manifest (T-0300 O2).
public enum CorpusUpdateDecision: Equatable, Sendable {
    /// Download this corpus and stage it.
    case download(CorpusManifest)
    /// The manifest names the corpus already active: no download.
    case upToDate(version: String)
    /// The manifest's schema is not the one this reader parses.
    case refusedSchemaVersion(manifest: Int, reader: Int)
    /// The manifest needs a newer app build than this one.
    case refusedAppBuild(minAppBuild: Int, build: Int)
}
