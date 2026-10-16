import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0364 A2-A4 (R1, R2): the three feature flags decode per field through the shipping ConfigClient - the JSON
/// boolean when it is one, else the Worker's DEFAULT (true) for that flag alone - and the cache keeps all five fields.
@Suite("ConfigFlagTests")
struct ConfigFlagTests {
    enum Flag: CaseIterable { case loop, trip, surprise }

    /// Two answers that differ in every field, so a row that ignored its variant would show.
    static let variants = [
        RemoteConfig(minAppBuild: 7, planningPaused: true, featureLoop: false, featureTrip: false, featureSurprise: false),
        RemoteConfig(minAppBuild: 3, planningPaused: false, featureLoop: true, featureTrip: true, featureSurprise: true),
    ]

    /// (the flag's raw JSON text - nil leaves the key out, the flag it reads as - nil is the Worker's default).
    static let values: [(String?, Bool?)] = [
        ("true", true), ("false", false), (nil, nil), ("null", nil), ("0", nil), ("1", nil), (#""true""#, nil),
        (#""false""#, nil), ("1.5", nil), ("[]", nil), ("{}", nil),
    ]

    /// The Worker's DEFAULTS for the flags (services/api/src/config.ts), written out here, never read off the app.
    static let workerDefault = true

    /// The body with `flag` set to `value` and every other field the variant's.
    static func body(_ flag: Flag, _ value: String?, over v: RemoteConfig) -> Data {
        let rest = ConfigWireBody.rest(loop: flag == .loop ? value : String(v.featureLoop),
                                       trip: flag == .trip ? value : String(v.featureTrip),
                                       surprise: flag == .surprise ? value : String(v.featureSurprise))
        return ConfigWireBody.text(min: String(v.minAppBuild), paused: String(v.planningPaused), rest: rest)
    }

    /// The answer recomputed field by field: the variant with `flag` replaced by what it reads as.
    static func expected(_ flag: Flag, _ read: Bool?, over v: RemoteConfig) -> RemoteConfig {
        let value = read ?? workerDefault
        return RemoteConfig(minAppBuild: v.minAppBuild, planningPaused: v.planningPaused,
                            featureLoop: flag == .loop ? value : v.featureLoop,
                            featureTrip: flag == .trip ? value : v.featureTrip,
                            featureSurprise: flag == .surprise ? value : v.featureSurprise)
    }

    @Test("Each feature flag reads per field: its boolean, else the Worker's default, every other field kept")
    func perField() async {
        var seen = 0
        for variant in Self.variants {
            for flag in Flag.allCases {
                for (value, read) in Self.values {
                    let reply = PlanHTTPReply(status: 200, body: Self.body(flag, value, over: variant))
                    let (answer, requests) = await ConfigWireBody.fetch(reply)
                    #expect(answer == Self.expected(flag, read, over: variant),
                            "\(flag) \(String(describing: value)) over \(variant)")
                    #expect(requests.count == 1)
                    seen += 1
                }
            }
        }
        #expect(seen == 66)
    }

    @Test("A garbled or missing flag never discards a valid pause or build")
    func keepsThePause() async {
        for flag in Flag.allCases {
            for (value, read) in Self.values where read == nil {
                let (answer, _) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200,
                                                                           body: Self.body(flag, value, over: Self.variants[0])))
                #expect(answer?.planningPaused == true, "\(flag) \(String(describing: value))")
                #expect(answer?.minAppBuild == 7, "\(flag) \(String(describing: value))")
            }
        }
    }

    @Test("Every flag row is a function of the variant")
    func rowsReadTheVariant() {
        for flag in Flag.allCases {
            for (value, read) in Self.values {
                #expect(Self.body(flag, value, over: Self.variants[0]) != Self.body(flag, value, over: Self.variants[1]))
                #expect(Self.expected(flag, read, over: Self.variants[0])
                        != Self.expected(flag, read, over: Self.variants[1]))
                // The flag's own value differs too wherever a default is read: variant 0 holds false, the default true.
                if read == nil {
                    #expect(Self.expected(flag, read, over: Self.variants[0]) != Self.variants[0], "\(flag)")
                }
            }
        }
    }

    @Test("The bundled defaults carry every flag at the Worker's default")
    func bundled() {
        #expect(RemoteConfig.bundled == RemoteConfig(minAppBuild: 1, planningPaused: false, featureLoop: true,
                                                     featureTrip: true, featureSurprise: true))
    }

    static let keptOff = Data(
        #"{"feature_loop":false,"feature_surprise":false,"feature_trip":false,"min_app_build":7,"planning_paused":true}"#.utf8)

    @Test("The cache keeps all five fields, and kept bytes from a two-field build read with the flags at default")
    func cacheKeepsFlags() async {
        let off = Self.variants[0]
        let storage = MemoryConfigStorage(nil)
        let good = ScriptedTransport(["GET /config": [PlanHTTPReply(status: 200, body: ConfigWireBody.of(off))]])
        let answer = await ConfigCache(client: ConfigClient(base: ConfigWireBody.base, transport: good),
                                       storage: storage).refresh()
        #expect(answer == off)
        #expect(storage.load() == Self.keptOff)
        let failures: [(String, PlanHTTPReply?)] = [
            ("no reply", nil), ("503", PlanHTTPReply(status: 503, body: ConfigWireBody.of(Self.variants[1]))),
            ("malformed", PlanHTTPReply(status: 200, body: ConfigWireBody.text(min: "0", paused: "false"))),
        ]
        for (name, reply) in failures {
            let transport = ScriptedTransport(reply.map { ["GET /config": [$0]] } ?? [:])
            let later = await ConfigCache(client: ConfigClient(base: ConfigWireBody.base, transport: transport),
                                          storage: storage).refresh()
            #expect(later == off, "\(name): the kept flags read back")
            #expect(storage.load() == Self.keptOff, "\(name)")
        }
        let legacy = MemoryConfigStorage(Data(#"{"min_app_build":7,"planning_paused":true}"#.utf8))
        let kept = await ConfigCache(client: ConfigClient(base: ConfigWireBody.base, transport: ScriptedTransport([:])),
                                     storage: legacy).refresh()
        #expect(kept == RemoteConfig(minAppBuild: 7, planningPaused: true, featureLoop: true, featureTrip: true,
                                     featureSurprise: true))
    }
}
