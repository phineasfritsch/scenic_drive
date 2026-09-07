import Testing
@testable import ScenicKit

@Suite("Geo")
struct GeoTests {
    let sanFrancisco = Coordinate(latitude: 37.7749, longitude: -122.4194)
    let oakland = Coordinate(latitude: 37.8044, longitude: -122.2712)

    @Test("haversine SF→Oakland is ~13.4 km")
    func haversineKnownDistance() {
        let d = Geo.distanceMeters(sanFrancisco, oakland)
        #expect(d > 13_300 && d < 13_550, "got \(d)")
    }

    @Test("distance is symmetric and zero for identical points")
    func symmetry() {
        #expect(Geo.distanceMeters(sanFrancisco, oakland) == Geo.distanceMeters(oakland, sanFrancisco))
        #expect(Geo.distanceMeters(sanFrancisco, sanFrancisco) == 0)
    }

    @Test("bearing due north is 0°, due east is 90°")
    func bearings() {
        let north = Coordinate(latitude: sanFrancisco.latitude + 0.1, longitude: sanFrancisco.longitude)
        let east = Coordinate(latitude: sanFrancisco.latitude, longitude: sanFrancisco.longitude + 0.1)
        #expect(abs(Geo.initialBearingDegrees(from: sanFrancisco, to: north)) < 0.01)
        #expect(abs(Geo.initialBearingDegrees(from: sanFrancisco, to: east) - 90) < 0.1)
    }
}
