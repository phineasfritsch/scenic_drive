import Foundation
import Testing
@testable import ScenicKit

@Suite("Solar math")
struct SolarMathTests {
    let sanFrancisco = Coordinate(latitude: 37.7749, longitude: -122.4194)
    let utqiagvik = Coordinate(latitude: 71.2906, longitude: -156.7886)

    func t(_ iso: String) -> Double {
        let d = CivilDate(iso: iso)!
        return SolarMath.julianCentury(julianDay: d.julianDayAtMidnightUTC + 0.5)
    }

    @Test("declination is +23.4° at the June solstice and ~0° at the equinox")
    func declination() {
        #expect(abs(SolarMath.declination(t("2026-06-21")) - 23.44) < 0.05)
        #expect(abs(SolarMath.declination(t("2026-12-21")) + 23.44) < 0.05)
        #expect(abs(SolarMath.declination(t("2026-03-20"))) < 0.5)
    }

    @Test("equation of time peaks near +16 min in early November and −14 min in mid February")
    func equationOfTime() {
        #expect(SolarMath.equationOfTime(t("2026-11-03")) > 15.5)
        #expect(SolarMath.equationOfTime(t("2026-02-11")) < -13.5)
    }

    @Test("Julian day of J2000.0 and of a known date")
    func julianDay() {
        #expect(CivilDate(year: 2000, month: 1, day: 1).julianDayAtMidnightUTC == 2_451_544.5)
        #expect(CivilDate(year: 2026, month: 9, day: 7).julianDayAtMidnightUTC == 2_461_290.5)
    }

    @Test("polar night and midnight sun return nil, not a fake time")
    func polar() {
        let winter = SolarEvents.compute(on: CivilDate(iso: "2026-12-21")!, at: utqiagvik)
        #expect(winter.sunrise == nil && winter.sunset == nil)
        let summer = SolarEvents.compute(on: CivilDate(iso: "2026-06-21")!, at: utqiagvik)
        #expect(summer.sunrise == nil && summer.sunset == nil)
        #expect(summer.civilDusk == nil, "no civil twilight either under the midnight sun")
    }

    @Test("elevation at solar noon equals 90° − |latitude − declination|")
    func noonElevation() {
        let ev = SolarEvents.compute(on: CivilDate(iso: "2026-06-21")!, at: sanFrancisco)
        let expected = 90 - abs(sanFrancisco.latitude - SolarMath.declination(t("2026-06-21")))
        #expect(abs(SolarMath.elevation(at: ev.solarNoon, coordinate: sanFrancisco) - expected) < 0.2)
    }

    @Test("evening golden hour ends after sunset and starts before it; sun is at +6° at its start")
    func goldenHour() {
        let ev = SolarEvents.compute(on: CivilDate(iso: "2026-09-22")!, at: sanFrancisco)
        let gh = try! #require(ev.goldenHourEvening)
        let sunset = try! #require(ev.sunset)
        #expect(gh.lowerBound < sunset && sunset < gh.upperBound)
        #expect(abs(SolarMath.elevation(at: gh.lowerBound, coordinate: sanFrancisco) - 6) < 0.3)
        #expect(abs(SolarMath.elevation(at: gh.upperBound, coordinate: sanFrancisco) + 4) < 0.3)
        #expect(gh.upperBound.timeIntervalSince(gh.lowerBound) > 40 * 60 && gh.upperBound.timeIntervalSince(gh.lowerBound) < 90 * 60)
    }

    @Test("CivilDate parses ISO and rejects junk")
    func civilDate() {
        #expect(CivilDate(iso: "2026-06-21") == CivilDate(year: 2026, month: 6, day: 21))
        #expect(CivilDate(iso: "2026-13-01") == nil)
        #expect(CivilDate(iso: "yesterday") == nil)
    }
}
