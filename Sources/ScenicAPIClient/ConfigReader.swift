import Foundation
import ScenicKit

/// The one reader of /config answers (T-0357 R2): a reply is a RemoteConfig only when its status is 200 and its body
/// is a JSON object whose `min_app_build` is an integer in 1...RemoteConfig.maxAppBuild and whose `planning_paused`
/// is a boolean. Anything else refuses the WHOLE answer - nil, never a crash. The three feature flags read per field
/// (T-0364 R1, ConfigWire.flag): a garbled flag is its default and never refuses the answer.
enum ConfigReader {
    static func read(_ reply: PlanHTTPReply) -> RemoteConfig? {
        guard reply.status == 200 else { return nil }
        return decode(reply.body)
    }

    /// The fields of `body`, or nil. The cache's stored bytes are read back through here too (R4).
    static func decode(_ body: Data) -> RemoteConfig? {
        guard let wire = try? JSONDecoder().decode(ConfigWire.self, from: body),
              (1...RemoteConfig.maxAppBuild).contains(wire.minAppBuild) else { return nil }
        return RemoteConfig(minAppBuild: wire.minAppBuild, planningPaused: wire.planningPaused,
                            featureLoop: wire.featureLoop, featureTrip: wire.featureTrip,
                            featureSurprise: wire.featureSurprise)
    }

    /// `config` as the five-field object the cache keeps, keys sorted (T-0364 R2).
    static func encode(_ config: RemoteConfig) -> Data {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        // An Int and four Bools: this encoder cannot throw on them.
        return (try? encoder.encode(ConfigWire(minAppBuild: config.minAppBuild, planningPaused: config.planningPaused,
                                               featureLoop: config.featureLoop, featureTrip: config.featureTrip,
                                               featureSurprise: config.featureSurprise))) ?? Data()
    }
}
