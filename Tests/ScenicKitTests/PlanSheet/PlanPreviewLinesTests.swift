import Foundation
import ScenicKit
import Testing

/// T-0396: the preview sheet's hero number, why line and distance, each by exact equality.
@Suite struct PlanPreviewLinesTests {
    /// A two-point line due north from the equator whose haversine length is `miles`.
    private static func line(miles: Double) -> [Coordinate] {
        let degrees = miles * PlanPreview.metersPerMile / Geo.earthRadiusMeters * 180 / .pi
        return [Coordinate(latitude: 0, longitude: 0), Coordinate(latitude: degrees, longitude: 0)]
    }

    private static func preview(route: [Coordinate] = [], eta: Double = 3300, fastest: Double = 2100) -> PlanPreview {
        PlanPreview(route: route, etaSeconds: eta, fastestEtaSeconds: fastest, etaIsEstimate: true, hazards: [])
    }

    @Test("the why line says the minutes over fastest, or about as quick")
    func whyLine() {
        #expect(Self.preview().whyLine == "+20 min over fastest")
        #expect(Self.preview(eta: 1229, fastest: 1213.65).whyLine == "About as quick as the fastest way")
        #expect(Self.preview(eta: 1000, fastest: 1300).whyLine == "About as quick as the fastest way")
        #expect(Self.preview(eta: 1300, fastest: 1000).whyLine == "+5 min over fastest")
    }

    @Test("the hero number is the rounded minutes")
    func etaHero() {
        #expect(Self.preview().etaHero == "55 min")
        #expect(Self.preview(eta: 89).etaHero == "1 min")
        #expect(Self.preview(eta: 29).etaHero == "0 min")
    }

    @Test("the distance is the drawn line's miles: tenths under 10, whole from 10, nothing without a line")
    func distanceLabel() {
        #expect(Self.preview().distanceLabel == nil)
        #expect(Self.preview(route: [Coordinate(latitude: 34, longitude: -118)]).distanceLabel == nil)
        #expect(Self.preview(route: Self.line(miles: 0)).distanceLabel == "(0.0 mi)")
        #expect(Self.preview(route: Self.line(miles: 2.7)).distanceLabel == "(2.7 mi)")
        #expect(Self.preview(route: Self.line(miles: 9.94)).distanceLabel == "(9.9 mi)")
        #expect(Self.preview(route: Self.line(miles: 9.96)).distanceLabel == "(10 mi)")
        #expect(Self.preview(route: Self.line(miles: 15.4)).distanceLabel == "(15 mi)")
        #expect(Self.preview(route: Self.line(miles: 15.6)).distanceLabel == "(16 mi)")
    }

    @Test("the distance sums every leg of the line, not its ends")
    func distanceSumsLegs() {
        let out = Self.line(miles: 3)
        let back = [out[1], out[0]]
        let preview = Self.preview(route: out + back)
        #expect(preview.distanceLabel == "(6.0 mi)")
        #expect(abs(preview.routeMeters - 6 * PlanPreview.metersPerMile) < 0.01)
        #expect(PlanPreview.metersPerMile == 1609.344)
    }
}
