import Foundation
import ScenicKit

/// The remote config with a memory (T-0357 R4): a refresh is the fresh answer, kept as the last good one; a refused
/// answer or no reply is the kept answer, else RemoteConfig.bundled. A refusal never rewrites what is kept, and kept
/// bytes that do not read are as if absent.
public struct ConfigCache: Sendable {
    let client: ConfigClient
    let storage: any ConfigStorage

    public init(client: ConfigClient, storage: any ConfigStorage) {
        self.client = client
        self.storage = storage
    }

    public func refresh() async -> RemoteConfig {
        guard let fresh = await client.fetch() else { return kept }
        storage.save(ConfigReader.encode(fresh))
        return fresh
    }

    /// The last good answer, else the bundled defaults.
    private var kept: RemoteConfig {
        storage.load().flatMap(ConfigReader.decode) ?? RemoteConfig.bundled
    }
}
