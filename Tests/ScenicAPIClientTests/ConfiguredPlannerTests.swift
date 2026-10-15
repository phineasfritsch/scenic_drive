import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0357 A7 (R7): the live planner's degrade is ConfigDegrade.of(the cache's refreshed answer, our build), and its
/// plan is the ClientPlanner's.
@Suite("ConfiguredPlannerTests")
struct ConfiguredPlannerTests {
    /// A ticket from the shipping gate (PlanTicket's init is internal to ScenicKit).
    static var ticket: PlanTicket? {
        var sheet = PlanSheet(disclaimerAccepted: true)
        sheet.search("", for: .start)
        sheet.choose(PlanPlace(id: 7, name: "Santa Monica", coordinate: Coordinate(latitude: 34.02, longitude: -118.49)))
        sheet.search("", for: .destination)
        sheet.choose(PlanPlace(id: 42, name: "Topanga", coordinate: Coordinate(latitude: 34.09, longitude: -118.6)))
        return sheet.startPlanning()
    }

    static func planner(_ replies: [String: [PlanHTTPReply]], stored: Data? = nil,
                        appBuild: Int?) -> (ConfiguredPlanner, ScriptedTransport) {
        let transport = ScriptedTransport(replies)
        let client = PlanClient(base: ConfigWireBody.base, transport: transport, installID: PlanWire.install, accountToken: nil,
                                session: nil)
        let cache = ConfigCache(client: ConfigClient(base: ConfigWireBody.base, transport: transport),
                                storage: MemoryConfigStorage(stored))
        return (ConfiguredPlanner(planner: ClientPlanner(client: client), cache: cache, appBuild: appBuild), transport)
    }

    static func config(_ min: Int, _ paused: Bool) -> [String: [PlanHTTPReply]] {
        ["GET /config": [PlanHTTPReply(status: 200, body: ConfigWireBody.of(RemoteConfig(minAppBuild: min,
                                                                                         planningPaused: paused)))]]
    }

    static let pausedStore = Data(#"{"min_app_build":1,"planning_paused":true}"#.utf8)

    /// (name, replies, stored, our build, the degrade).
    static let rows: [(String, [String: [PlanHTTPReply]], Data?, Int?, ConfigDegrade)] = [
        ("paused, build 1 of 1", config(1, true), nil, 1, .planningPaused),
        ("unpaused, build 1 of 1", config(1, false), nil, 1, .clear),
        ("unpaused, build 2 above our 1", config(2, false), nil, 1, .updateRequired),
        ("paused, build 2 above our 1", config(2, true), nil, 1, .updateRequired),
        ("unpaused, build 2 and our build unknown", config(2, false), nil, nil, .clear),
        ("paused, build 2 and our build unknown", config(2, true), nil, nil, .planningPaused),
        ("no reply, nothing stored", [:], nil, 1, .clear),
        ("no reply, a stored pause", [:], pausedStore, 1, .planningPaused),
        ("a fresh unpause over a stored pause", config(1, false), pausedStore, 1, .clear),
    ]

    @Test("The live planner's degrade is the degrade of the refreshed answer against our build")
    func degrade() async {
        for (name, replies, stored, build, expected) in Self.rows {
            let (planner, transport) = Self.planner(replies, stored: stored, appBuild: build)
            #expect(await planner.degrade() == expected, "\(name)")
            #expect(await transport.requests.map(\.url) == [ConfigWireBody.url], "\(name): one GET /config")
        }
    }

    @Test("The live planner's plan is the client planner's, and the client planner itself never degrades")
    func plan() async {
        let replies = ["POST /plan": [PlanHTTPReply(status: 422, body: Data(#"{"error":"region_unsupported"}"#.utf8))]]
        let (planner, transport) = Self.planner(replies, appBuild: 1)
        guard let ticket = Self.ticket else {
            Issue.record("the gate issued no ticket")
            return
        }
        #expect(await planner.plan(ticket) == .failure(.regionUnsupported))
        #expect(await transport.requests.map(\.method) == ["POST"])
        #expect(await planner.planner.degrade() == .clear)
    }
}
