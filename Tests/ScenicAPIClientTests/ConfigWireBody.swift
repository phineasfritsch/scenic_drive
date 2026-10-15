import Foundation
import ScenicAPIClient
import ScenicKit

/// The Worker's /config answer as T-0357's Log measured it (services/api/src/config.ts, no KV record, no kill), with
/// the two fields the app reads replaceable by any JSON text - or left out (nil) - and the rest of the answer
/// replaceable too, so a test can plant exactly one malformed value in an otherwise real answer.
enum ConfigWireBody {
    static let base = URL(string: "https://scenic-api.test")!
    static let url = URL(string: "https://scenic-api.test/config")!

    /// Every key the Worker sends after the two the app reads, verbatim from the measured default answer.
    static let rest = #""supported_regions":["la"],"feature_loop":true,"feature_trip":true,"feature_surprise":true,"#
        + #""quota":{"anon":{"plan":3,"loop":1,"surprise":3,"trip":1},"free":{"plan":10,"loop":1,"surprise":3,"#
        + #""trip":1},"paid":{"plan":200,"loop":200,"surprise":200,"trip":200}},"config_warnings":[]"#

    /// The measured default answer, byte for byte.
    static let workerDefault = Data((#"{"min_app_build":1,"planning_paused":false,"# + rest + "}").utf8)

    /// The answer with `min` and `paused` as raw JSON text (nil leaves the key out) and `rest` after them.
    static func text(min: String?, paused: String?, rest: String = ConfigWireBody.rest) -> Data {
        var parts: [String] = []
        if let min { parts.append(#""min_app_build":"# + min) }
        if let paused { parts.append(#""planning_paused":"# + paused) }
        if !rest.isEmpty { parts.append(rest) }
        return Data(("{" + parts.joined(separator: ",") + "}").utf8)
    }

    /// A well-formed answer carrying `config`.
    static func of(_ config: RemoteConfig, rest: String = ConfigWireBody.rest) -> Data {
        text(min: String(config.minAppBuild), paused: String(config.planningPaused), rest: rest)
    }

    /// One fetch through the shipping client over a transport answering `reply` (nil: no reply at all), with the
    /// requests it sent.
    static func fetch(_ reply: PlanHTTPReply?) async -> (RemoteConfig?, [PlanHTTPRequest]) {
        let transport = ScriptedTransport(reply.map { ["GET /config": [$0]] } ?? [:])
        let answer = await ConfigClient(base: base, transport: transport).fetch()
        return (answer, await transport.requests)
    }
}
