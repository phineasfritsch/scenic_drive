import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0357 A2-A4: GET /config through the shipping `ConfigClient.fetch()` - the request, whole-answer equality over
/// every field and bound, and the decode-failure table (R1-R3).
@Suite("ConfigClientTests")
struct ConfigClientTests {
    static let max = 2_147_483_647

    /// The two variants every failure row is a function of: each field differs between them.
    static let variants = [RemoteConfig(minAppBuild: 7, planningPaused: true),
                           RemoteConfig(minAppBuild: 3, planningPaused: false)]

    /// (name, status, min_app_build, planning_paused) as raw JSON text: "$" is the variant's own value, nil leaves the
    /// key out. Every row must be refused - fetch() is nil - and every row is a function of the variant.
    static let refused: [(String, Int, String?, String?)] = [
        ("min_app_build 0", 200, "0", "$"),
        ("min_app_build -1", 200, "-1", "$"),
        ("min_app_build 2147483648", 200, "2147483648", "$"),
        ("min_app_build 1.5", 200, "1.5", "$"),
        ("min_app_build 1e20", 200, "1e20", "$"),
        ("min_app_build a string", 200, "\"7\"", "$"),
        ("min_app_build a bool", 200, "true", "$"),
        ("min_app_build null", 200, "null", "$"),
        ("min_app_build missing", 200, nil, "$"),
        ("planning_paused a string", 200, "$", "\"true\""),
        ("planning_paused 1", 200, "$", "1"),
        ("planning_paused 0", 200, "$", "0"),
        ("planning_paused null", 200, "$", "null"),
        ("planning_paused missing", 200, "$", nil),
        ("status 201", 201, "$", "$"),
        ("status 204", 204, "$", "$"),
        ("status 304", 304, "$", "$"),
        ("status 404", 404, "$", "$"),
        ("status 500", 500, "$", "$"),
        ("status 503", 503, "$", "$"),
    ]
    /// (name, the whole body): bodies that cannot carry a config at all, so they ignore the variant by construction.
    static let notObjects: [(String, String)] = [
        ("an array", "[]"), ("a string", "\"x\""), ("a number", "7"), ("null", "null"), ("empty", ""),
        ("not JSON", "{min_app_build:1"),
    ]

    /// A refused row's body over `variant`.
    static func body(min: String?, paused: String?, over variant: RemoteConfig) -> Data {
        let minText: String? = min.map { $0 == "$" ? String(variant.minAppBuild) : $0 }
        let pausedText: String? = paused.map { $0 == "$" ? String(variant.planningPaused) : $0 }
        return ConfigWireBody.text(min: minText, paused: pausedText)
    }

    @Test("GET /config is exactly the base's /config with no headers and no body, sent once")
    func request() async {
        let (answer, requests) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200, body: ConfigWireBody.workerDefault))
        #expect(requests == [PlanHTTPRequest(url: ConfigWireBody.url, method: "GET", headers: [:], body: Data())])
        #expect(answer == RemoteConfig(minAppBuild: 1, planningPaused: false))
    }

    @Test("No reply at all is no answer, after exactly one request")
    func offline() async {
        let (answer, requests) = await ConfigWireBody.fetch(nil)
        #expect(answer == nil)
        #expect(requests.count == 1)
    }

    @Test("Every in-bounds answer reads as exactly the config it carries")
    func inBounds() async {
        for min in [1, 2, 41, Self.max - 1, Self.max] {
            for paused in [false, true] {
                let config = RemoteConfig(minAppBuild: min, planningPaused: paused)
                let (answer, requests) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200, body: ConfigWireBody.of(config)))
                #expect(answer == config, "min \(min) paused \(paused)")
                #expect(requests.count == 1)
            }
        }
    }

    @Test("Keys the app does not read never change the answer")
    func unreadKeys() async {
        let rests = ["", ConfigWireBody.rest + #","kill":true"#,
                     #""supported_regions":7,"feature_loop":"x","feature_trip":null,"quota":null,"config_warnings":{}"#]
        for config in Self.variants {
            for rest in rests {
                let (answer, _) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200, body: ConfigWireBody.of(config, rest: rest)))
                #expect(answer == config, "rest \(rest)")
            }
        }
    }

    @Test("Every out-of-bounds, mistyped or missing field, non-object body and non-200 status refuses the whole answer")
    func refusedRows() async {
        for config in Self.variants {
            let (control, _) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200, body: ConfigWireBody.of(config)))
            #expect(control == config, "the variant itself is a good answer")
            for (name, status, min, paused) in Self.refused {
                let body = Self.body(min: min, paused: paused, over: config)
                let (answer, requests) = await ConfigWireBody.fetch(PlanHTTPReply(status: status, body: body))
                #expect(answer == nil, "\(name) over \(config)")
                #expect(requests.count == 1, "\(name): exactly one request, never a retry")
            }
            for (name, text) in Self.notObjects {
                let (answer, requests) = await ConfigWireBody.fetch(PlanHTTPReply(status: 200, body: Data(text.utf8)))
                #expect(answer == nil, "\(name)")
                #expect(requests.count == 1, "\(name)")
            }
        }
    }

    @Test("Every refusal row that can carry a config is a function of the variant")
    func rowsReadTheVariant() {
        for (name, _, min, paused) in Self.refused {
            let first = Self.body(min: min, paused: paused, over: Self.variants[0])
            let second = Self.body(min: min, paused: paused, over: Self.variants[1])
            #expect(first != second, "\(name) ignores the variant")
        }
    }
}
