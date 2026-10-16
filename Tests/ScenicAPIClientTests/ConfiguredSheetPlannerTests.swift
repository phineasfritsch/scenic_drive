import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0364 A5 (R3): the degrade of each of the plan sheet's three screens, through the shipping planners the app
/// composes (ConfiguredPlanner, ConfiguredLoopPlanner, ConfiguredTripPlanner), over every pause x flag x build answer.
@Suite("ConfiguredSheetPlannerTests")
struct ConfiguredSheetPlannerTests {
    /// (min_app_build, our build): below, equal, and an unknown build under a higher minimum.
    static let builds: [(Int, Int?)] = [(1, 1), (2, 1), (2, nil)]

    /// Every answer: planning_paused x feature_loop x feature_trip x feature_surprise x the build pairs.
    static var answers: [(RemoteConfig, Int?)] {
        var out: [(RemoteConfig, Int?)] = []
        for paused in [false, true] {
            for loop in [false, true] {
                for trip in [false, true] {
                    for surprise in [false, true] {
                        for (min, build) in builds {
                            out.append((RemoteConfig(minAppBuild: min, planningPaused: paused, featureLoop: loop,
                                                     featureTrip: trip, featureSurprise: surprise), build))
                        }
                    }
                }
            }
        }
        return out
    }

    /// The degrade recomputed here from R3, independent of ConfigDegrade.of.
    static func expected(_ c: RemoteConfig, build: Int?, on screen: ConfigScreen) -> ConfigDegrade {
        if let build, c.minAppBuild > build { return .updateRequired }
        if c.planningPaused { return screen == .plan && !c.featureSurprise ? .pausedSurpriseOff : .planningPaused }
        if (screen == .loop && !c.featureLoop) || (screen == .trip && !c.featureTrip) { return .featureOff }
        return .clear
    }

    static func cache(_ transport: ScriptedTransport) -> ConfigCache {
        ConfigCache(client: ConfigClient(base: ConfigWireBody.base, transport: transport), storage: MemoryConfigStorage(nil))
    }

    static func loopPlanner(_ transport: ScriptedTransport, _ build: Int?) -> ConfiguredLoopPlanner {
        ConfiguredLoopPlanner(planner: ClientLoopPlanner(client: LoopClient(base: ConfigWireBody.base, transport: transport,
                                                                            installID: PlanWire.install,
                                                                            accountToken: nil, session: nil)),
                              cache: cache(transport), appBuild: build)
    }

    static func tripPlanner(_ transport: ScriptedTransport, _ build: Int?) -> ConfiguredTripPlanner {
        ConfiguredTripPlanner(planner: ClientTripPlanner(client: TripClient(base: ConfigWireBody.base, transport: transport,
                                                                            installID: PlanWire.install,
                                                                            accountToken: nil, session: nil)),
                              cache: cache(transport), appBuild: build)
    }

    static func planPlanner(_ transport: ScriptedTransport, _ build: Int?) -> ConfiguredPlanner {
        ConfiguredPlanner(planner: ClientPlanner(client: PlanClient(base: ConfigWireBody.base, transport: transport,
                                                                    installID: PlanWire.install, accountToken: nil,
                                                                    session: nil)),
                          cache: cache(transport), appBuild: build)
    }

    /// One screen's degrade through its shipping planner, as the sheet asks it (the protocol), and the requests sent.
    static func degrade(_ config: RemoteConfig, _ build: Int?, on screen: ConfigScreen) async -> (ConfigDegrade, [URL]) {
        let transport = ScriptedTransport(["GET /config": [PlanHTTPReply(status: 200, body: ConfigWireBody.of(config))]])
        let degrade: ConfigDegrade
        switch screen {
        case .plan: degrade = await (planPlanner(transport, build) as any RoutePlanning).degrade()
        case .loop: degrade = await (loopPlanner(transport, build) as any LoopPlanning).degrade()
        case .trip: degrade = await (tripPlanner(transport, build) as any TripPlanning).degrade()
        }
        return (degrade, await transport.requests.map(\.url))
    }

    @Test("Each screen's degrade is the table's row for every pause, flag and build, after one GET /config")
    func table() async {
        var counts: [ConfigDegrade: Int] = [:]
        for (config, build) in Self.answers {
            for screen in ConfigScreen.allCases {
                let (degrade, urls) = await Self.degrade(config, build, on: screen)
                let expected = Self.expected(config, build: build, on: screen)
                #expect(degrade == expected, "\(screen) \(config) build \(String(describing: build))")
                #expect(urls == [ConfigWireBody.url], "\(screen): exactly one GET /config")
                counts[expected, default: 0] += 1
            }
        }
        // The table reaches every degrade, in the counts R3 gives: 48 answers x 3 screens.
        #expect(counts == [.updateRequired: 48, .planningPaused: 40, .pausedSurpriseOff: 8, .featureOff: 16, .clear: 32])
    }

    static let pausedReply = PlanHTTPReply(status: 503, body: Data(#"{"error":"planning_paused"}"#.utf8))

    @Test("The configured loop and trip planners plan as the client ones, and the bare clients never degrade")
    func plans() async {
        let start = PlanPlace(id: 7, name: "Topanga", coordinate: Coordinate(latitude: 34.09, longitude: -118.6))
        let end = PlanPlace(id: 42, name: "Zuma", coordinate: Coordinate(latitude: 34.02, longitude: -118.83))
        var loop = LoopSheet(disclaimerAccepted: true)
        loop.search("")
        loop.choose(start)
        var trip = TripSheet(disclaimerAccepted: true)
        trip.search("", for: .start)
        trip.choose(start)
        trip.search("", for: .destination)
        trip.choose(end)
        guard let loopTicket = loop.startPlanning(), let tripTicket = trip.startPlanning() else {
            Issue.record("a gate issued no ticket")
            return
        }
        let loopTransport = ScriptedTransport(["POST /loop": [Self.pausedReply]])
        let loopPlanner = Self.loopPlanner(loopTransport, 1)
        #expect(await loopPlanner.plan(loopTicket) == .failure(.planningPaused))
        #expect(await loopTransport.requests.map(\.method) == ["POST"])
        #expect(await loopPlanner.planner.degrade() == .clear)
        let tripTransport = ScriptedTransport(["POST /trip": [Self.pausedReply]])
        let tripPlanner = Self.tripPlanner(tripTransport, 1)
        #expect(await tripPlanner.plan(tripTicket) == .failure(.planningPaused))
        #expect(await tripTransport.requests.map(\.method) == ["POST"])
        #expect(await tripPlanner.planner.degrade() == .clear)
    }
}
