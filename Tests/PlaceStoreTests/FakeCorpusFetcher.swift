import Foundation
import PlaceStore

/// The app's URLSession download, replaced (T-0300 O5): writes `served` to the destination it is handed and, when
/// `fails` is set, then throws - a download that died part-way, leaving a partial file behind.
struct FakeCorpusFetcher: CorpusFetcher {
    let served: Data
    var fails = false

    func fetch(_ manifest: CorpusManifest, to destination: URL) async throws {
        try served.write(to: destination)
        if fails { throw CocoaError(.fileReadUnknown) }
    }
}
