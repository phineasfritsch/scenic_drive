import ScenicKit
import Testing

/// T-0368 acceptance 2: SurpriseGate.of reads /config's feature_surprise and nothing else (R3), over the cross product
/// of every field the app reads, and the home's line is typed whole (R2).
@Suite("SurpriseGateTests")
struct SurpriseGateTests {
    /// planning_paused x feature_loop x feature_trip x feature_surprise x min_app_build {1, max}: 32 configs.
    static let configs: [RemoteConfig] = {
        var all: [RemoteConfig] = []
        for paused in [false, true] {
            for loop in [false, true] {
                for trip in [false, true] {
                    for surprise in [false, true] {
                        for build in [1, RemoteConfig.maxAppBuild] {
                            all.append(RemoteConfig(minAppBuild: build, planningPaused: paused, featureLoop: loop,
                                                    featureTrip: trip, featureSurprise: surprise))
                        }
                    }
                }
            }
        }
        return all
    }()

    @Test("the gate is feature_surprise alone, over all 32 configs")
    func gateIsTheFlag() {
        #expect(Self.configs.count == 32)
        for config in Self.configs {
            let typed: SurpriseGate = config.featureSurprise ? .on : .off
            #expect(SurpriseGate.of(config) == typed, "\(config)")
        }
        // Meta: both answers occur, so a constant gate would show.
        #expect(Set(Self.configs.map(SurpriseGate.of)) == [.on, .off])
    }

    @Test("the home's line: none while on, the typed switched-off line while off")
    func homeLine() {
        #expect(SurpriseGate.on.homeLine == nil)
        #expect(SurpriseGate.off.homeLine == "Surprise Me is switched off for now. You can still plan a drive.")
        #expect(SurpriseGate.offLine == "Surprise Me is switched off for now. You can still plan a drive.")
        #expect(SurpriseGate.allCases == [.on, .off])
    }

    @Test("the bundled answer leaves Surprise Me on")
    func bundledIsOn() {
        #expect(SurpriseGate.of(RemoteConfig.bundled) == .on)
    }
}
