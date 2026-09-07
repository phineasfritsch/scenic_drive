import Foundation
import Testing
@testable import ScenicKit

/// Pin P-SAFE-05. Every instant comes from the US Naval Observatory (see Tests/Fixtures/solar/fetch_oracle.py),
/// not from our own output, so this suite can actually contradict the code. If it goes red after a refactor of
/// the solar math, every golden-hour card and the after-dark hazard flag have silently moved and nothing else
/// in the app would notice.
///
/// A nil fixture field means USNO reported no such phenomenon that day (midnight sun / polar night); the model
/// must return nil too, never a fabricated time.
@Suite("Solar fixtures (USNO oracle)")
struct SolarFixtureTests {
    static func parse(_ iso: String) -> Date {
        let f = ISO8601DateFormatter()
        f.formatOptions = [.withInternetDateTime]
        guard let d = f.date(from: iso) else { fatalError("bad fixture instant \(iso)") }
        return d
    }

    static func events(_ fx: SolarFixture) -> SolarEvents {
        SolarEvents.compute(on: CivilDate(iso: fx.date)!, at: Coordinate(latitude: fx.latitude, longitude: fx.longitude))
    }

    /// Compares one computed instant against the oracle, honouring nil-means-nil in both directions.
    static func check(_ got: Date?, _ want: String?, _ label: String) {
        switch (got, want) {
        case (nil, nil):
            break
        case let (got?, want?):
            let err = abs(got.timeIntervalSince(parse(want)))
            #expect(err <= solarFixtureToleranceSeconds, "\(label): off by \(Int(err)) s (got \(got), oracle \(want))")
        case (nil, .some(let want)):
            Issue.record("\(label): model returned nil but the oracle has \(want)")
        case (.some(let got), nil):
            Issue.record("\(label): model returned \(got) but the oracle reports no such event that day")
        }
    }

    @Test("the oracle covers at least 20 site-days across latitudes 21N to 65N")
    func fixtureCoverage() {
        #expect(solarFixtures.count >= 20)
        #expect(solarFixtures.contains { $0.latitude > 60 }, "need a high-latitude case")
        #expect(solarFixtures.contains { $0.latitude < 25 }, "need a low-latitude case")
    }

    @Test("sunrise matches USNO", arguments: solarFixtures)
    func sunrise(fx: SolarFixture) { Self.check(Self.events(fx).sunrise, fx.sunrise, "\(fx.name) sunrise") }

    @Test("sunset matches USNO", arguments: solarFixtures)
    func sunset(fx: SolarFixture) { Self.check(Self.events(fx).sunset, fx.sunset, "\(fx.name) sunset") }

    @Test("civil dawn matches USNO", arguments: solarFixtures)
    func civilDawn(fx: SolarFixture) { Self.check(Self.events(fx).civilDawn, fx.civilBegin, "\(fx.name) civil dawn") }

    @Test("civil dusk matches USNO", arguments: solarFixtures)
    func civilDusk(fx: SolarFixture) { Self.check(Self.events(fx).civilDusk, fx.civilEnd, "\(fx.name) civil dusk") }

    @Test("worst-case error across every fixture instant is within tolerance")
    func worstCase() {
        var worst: (String, TimeInterval) = ("none", 0)
        var compared = 0
        for fx in solarFixtures {
            let ev = Self.events(fx)
            let pairs: [(String, Date?, String?)] = [
                ("sunrise", ev.sunrise, fx.sunrise), ("sunset", ev.sunset, fx.sunset),
                ("dawn", ev.civilDawn, fx.civilBegin), ("dusk", ev.civilDusk, fx.civilEnd),
            ]
            for (what, got, want) in pairs {
                guard let got, let want else { continue }
                compared += 1
                let err = abs(got.timeIntervalSince(Self.parse(want)))
                if err > worst.1 { worst = ("\(fx.name) \(what)", err) }
            }
        }
        print("solar: compared \(compared) instants, worst \(Int(worst.1)) s at \(worst.0)")
        #expect(compared >= 80, "the oracle should give us plenty to compare")
        #expect(worst.1 <= solarFixtureToleranceSeconds, "worst: \(worst.0) = \(Int(worst.1)) s")
    }
}
