import Foundation

/// The download, as the seam between PlaceStore and the app (T-0300 O5): the app implements it with URLSession;
/// PlaceStore owns the decision, the verify and the renames, and never trusts what this wrote.
public protocol CorpusFetcher: Sendable {
    /// Writes the corpus `manifest` names to `destination`, replacing anything there.
    func fetch(_ manifest: CorpusManifest, to destination: URL) async throws
}
