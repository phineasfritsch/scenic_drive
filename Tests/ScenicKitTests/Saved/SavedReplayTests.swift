@testable import ScenicKit
import Testing

/// T-0306 R3: a replay is ONE plan through PlanSheet's one gate - the saved start at 2 dp, the corpus place nearest
/// the saved end (within `SavedReplay.reach` on each axis, inclusive), the saved budget clamped as the sheet clamps.
@Suite("SavedReplayTests")
struct SavedReplayTests {
    static let matador = PlanPlace(id: 42, name: "El Matador", coordinate: Coordinate(latitude: 34.04, longitude: -118.685))
    static let replay = SavedReplay(id: 1, start: Coordinate(latitude: 34.09, longitude: -118.6), destination: matador,
                                    budgetMinutes: 30)

    static func at(_ id: Int64, _ lat: Double, _ lon: Double) -> PlanPlace {
        PlanPlace(id: id, name: "P\(id)", coordinate: Coordinate(latitude: lat, longitude: lon))
    }

    @Test("the destination is found within 0.01 degrees on each axis, every bound inclusive, nothing past it")
    func reachBounds() {
        let origin = Coordinate(latitude: 0, longitude: 0)
        let r = SavedReplay.reach
        let rows: [(String, Double, Double, Bool)] = [
            ("north edge", r, 0, true), ("past north", r.nextUp, 0, false),
            ("south edge", -r, 0, true), ("past south", (-r).nextDown, 0, false),
            ("east edge", 0, r, true), ("past east", 0, r.nextUp, false),
            ("west edge", 0, -r, true), ("past west", 0, (-r).nextDown, false),
            ("corner", r, -r, true), ("NaN latitude", .nan, 0, false), ("NaN longitude", 0, .nan, false),
            ("infinite", .infinity, 0, false),
        ]
        #expect(r == 0.01)
        for (label, lat, lon, found) in rows {
            let place = Self.at(5, lat, lon)
            #expect(SavedReplay.nearest(to: origin, among: [place]) == (found ? place : nil), "\(label)")
        }
    }

    @Test("the nearest place wins, distance east-west scaled by the latitude, a tie to the lower id, none from none")
    func nearestWins() {
        let point = Coordinate(latitude: 60, longitude: 10)
        let east = Self.at(7, 60, 10.008)
        let north = Self.at(3, 60.005, 10)
        #expect(SavedReplay.nearest(to: point, among: [north, east]) == east)
        #expect(SavedReplay.nearest(to: point, among: [east, north]) == east)
        let zero = Coordinate(latitude: 0, longitude: 0)
        let twinA = Self.at(9, 0.005, 0)
        let twinB = Self.at(4, -0.005, 0)
        #expect(SavedReplay.nearest(to: zero, among: [twinA, twinB]) == twinB)
        #expect(SavedReplay.nearest(to: zero, among: [twinB, twinA]) == twinB)
        #expect(SavedReplay.nearest(to: point, among: []) == nil)
    }

    @Test("P-SAFE-03: a replay is one ticket through the sheet's gate - the start at 2 dp, the place, the budget")
    func replayTicket() {
        var sheet = PlanSheet(disclaimerAccepted: true)
        let ticket = sheet.replay(Self.replay)
        let want = PlanTicket(serial: 1, origin: Coordinate(latitude: 34.09, longitude: -118.6), place: 42,
                              budgetMinutes: 30)
        #expect(ticket == want)
        #expect(sheet.state == .planning(want))
        #expect(sheet.start == PlanPlace(id: 0, name: "Your saved start",
                                         coordinate: Coordinate(latitude: 34.09, longitude: -118.6)))
        #expect(sheet.destination == Self.matador)
        #expect(sheet.budgetMinutes == 30)
        #expect(sheet.replay(Self.replay) == nil, "a second replay while one is in flight")
        #expect(sheet.state == .planning(want))
    }

    @Test("P-SAFE-03: no ticket from a replay before the disclaimer is accepted; the drive waits, chosen")
    func replayGated() {
        var sheet = PlanSheet(disclaimerAccepted: false)
        #expect(sheet.replay(Self.replay) == nil)
        #expect(sheet.state == .chosen(Self.matador))
        sheet.setDisclaimerAccepted(true)
        #expect(sheet.startPlanning() == PlanTicket(serial: 1, origin: Coordinate(latitude: 34.09, longitude: -118.6),
                                                     place: 42, budgetMinutes: 30))
    }

    @Test("a replay's budget is clamped to 0...180 at every bound, and a start off 2 dp leaves at 2 dp")
    func replayClamp() {
        let rows: [(Int, Int)] = [(-1, 0), (0, 0), (180, 180), (181, 180), (500, 180)]
        for (saved, sent) in rows {
            var sheet = PlanSheet(disclaimerAccepted: true)
            let odd = SavedReplay(id: 1, start: Coordinate(latitude: 34.09312, longitude: -118.60071),
                                  destination: Self.matador, budgetMinutes: saved)
            #expect(sheet.replay(odd) == PlanTicket(serial: 1, origin: Coordinate(latitude: 34.09, longitude: -118.6),
                                                    place: 42, budgetMinutes: sent), "\(saved)")
        }
    }
}
