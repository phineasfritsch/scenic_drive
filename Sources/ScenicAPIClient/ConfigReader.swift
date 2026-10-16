import Foundation
import ScenicKit

/// The one reader of /config answers (T-0357 R2): a reply is a RemoteConfig only when its status is 200 and its body
/// is a JSON object whose `min_app_build` is an integer in 1...RemoteConfig.maxAppBuild and whose `planning_paused`
/// is a boolean. Anything else refuses the WHOLE answer - nil, never a partial overlay and never a crash.
enum ConfigReader {
    static func read(_ reply: PlanHTTPReply) -> RemoteConfig? {
        guard reply.status == 200 else { return nil }
        return decode(reply.body)
    }

    /// The two fields of `body`, or nil. The cache's stored bytes are read back through here too (R4).
    static func decode(_ body: Data) -> RemoteConfig? {
        guard let wire = try? JSONDecoder().decode(ConfigWire.self, from: body),
              (1...RemoteConfig.maxAppBuild).contains(wire.minAppBuild) else { return nil }
        return RemoteConfig(minAppBuild: wire.minAppBuild, planningPaused: wire.planningPaused)
    }

    /// `config` as the two-field object the cache keeps, keys sorted.
    static func encode(_ config: RemoteConfig) -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        // An Int and a Bool: this encoder cannot throw on them.
        return (try? encoder.encode(ConfigWire(minAppBuild: config.minAppBuild,
                                               planningPaused: config.planningPaused))) ?? Data()
    }
}
