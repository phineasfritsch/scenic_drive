import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0357 A5: `ConfigCache.refresh()` - the last good answer, else the bundled defaults (R4) - as a cross product over
/// what is stored and how the refresh fails.
@Suite("ConfigCacheTests")
struct ConfigCacheTests {
    /// (name, stored bytes, what they read as): rows are functions of the stored variant.
    static let stored: [(String, Data?, RemoteConfig)] = [
        ("nothing stored", nil, RemoteConfig.bundled),
        ("paused build 7", Data(#"{"min_app_build":7,"planning_paused":true}"#.utf8),
         RemoteConfig(minAppBuild: 7, planningPaused: true)),
        ("unpaused build 3", Data(#"{"min_app_build":3,"planning_paused":false}"#.utf8),
         RemoteConfig(minAppBuild: 3, planningPaused: false)),
        ("garbage", Data("nope".utf8), RemoteConfig.bundled),
        ("a stored build 0", Data(#"{"min_app_build":0,"planning_paused":true}"#.utf8), RemoteConfig.bundled),
    ]

    /// A fresh answer that differs from every stored one, so a fall-through to it is visible.
    static let fresh = RemoteConfig(minAppBuild: 9, planningPaused: true)

    /// (name, the reply - nil is no reply at all): each one refused.
    static let failures: [(String, PlanHTTPReply?)] = [
        ("no reply", nil),
        ("503 with a good body", PlanHTTPReply(status: 503, body: ConfigWireBody.of(fresh))),
        ("200 with min_app_build 0", PlanHTTPReply(status: 200, body: ConfigWireBody.text(min: "0", paused: "true"))),
    ]

    static func cache(_ storage: MemoryConfigStorage, _ reply: PlanHTTPReply?) -> ConfigCache {
        let transport = ScriptedTransport(reply.map { ["GET /config": [$0]] } ?? [:])
        return ConfigCache(client: ConfigClient(base: ConfigWireBody.base, transport: transport), storage: storage)
    }

    @Test("The bundled defaults are exactly the Worker's answer with no KV record and no kill")
    func bundled() async {
        #expect(RemoteConfig.bundled == RemoteConfig(minAppBuild: 1, planningPaused: false))
        let (answer, _) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200, body: ConfigWireBody.workerDefault))
        #expect(answer == RemoteConfig.bundled)
    }

    @Test("A refused answer or no reply is the last good answer, else the bundled defaults, and stores nothing")
    func fallsBack() async {
        for (name, bytes, expected) in Self.stored {
            for (failure, reply) in Self.failures {
                let storage = MemoryConfigStorage(bytes)
                let answer = await Self.cache(storage, reply).refresh()
                #expect(answer == expected, "\(name) / \(failure)")
                #expect(storage.load() == bytes, "\(name) / \(failure): the store was rewritten")
                #expect(storage.saves == 0, "\(name) / \(failure)")
            }
        }
        // Meta: the stored rows read as three different answers, so a row that ignored its store would show.
        #expect(Set(Self.stored.map { "\($0.2.minAppBuild)/\($0.2.planningPaused)" }).count == 3)
    }

    @Test("A good answer is the answer and is kept as the last good one")
    func keepsGood() async {
        for (name, bytes, _) in Self.stored {
            let storage = MemoryConfigStorage(bytes)
            let answer = await Self.cache(storage, PlanHTTPReply(status: 200, body: ConfigWireBody.of(Self.fresh))).refresh()
            #expect(answer == Self.fresh, "\(name)")
            #expect(storage.load() == Data(#"{"min_app_build":9,"planning_paused":true}"#.utf8), "\(name)")
            #expect(storage.saves == 1, "\(name)")
            let later = await Self.cache(storage, nil).refresh()
            #expect(later == Self.fresh, "\(name): the kept answer is read back")
        }
    }
}
