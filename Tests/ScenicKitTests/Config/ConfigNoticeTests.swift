import Foundation
import ScenicKit
import Testing

/// T-0364 A6-A7 (R3-R5): every degrade's notice on every screen as a literal table, and the loop and trip gates.
@Suite("ConfigNoticeTests")
struct ConfigNoticeTests {
    static let update = "This version can't plan drives anymore. Update Scenic Drive from the App Store to keep planning."
    static let resting = "Planning is resting for a moment. Try again in a little while."

    /// (degrade, screen, the notice): every case x every screen, written out.
    static let table: [(ConfigDegrade, ConfigScreen, String?)] = [
        (.clear, .plan, nil), (.clear, .loop, nil), (.clear, .trip, nil),
        (.updateRequired, .plan, update), (.updateRequired, .loop, update), (.updateRequired, .trip, update),
        (.planningPaused, .plan, "Planning is paused right now. Surprise Me on the home screen still works."),
        (.planningPaused, .loop, resting), (.planningPaused, .trip, resting),
        (.pausedSurpriseOff, .plan, "Planning is paused right now. Try again in a little while."),
        (.pausedSurpriseOff, .loop, resting), (.pausedSurpriseOff, .trip, resting),
        (.featureOff, .plan, "Planning is switched off for now. Try again later."),
        (.featureOff, .loop, "Loops are switched off for now. You can still plan a drive."),
        (.featureOff, .trip, "Road trips are switched off for now. You can still plan a drive."),
    ]

    @Test("Each degrade's notice on each screen is exactly its row")
    func notices() {
        #expect(ConfigDegrade.allCases == [.clear, .planningPaused, .updateRequired, .pausedSurpriseOff, .featureOff])
        #expect(ConfigScreen.allCases == [.plan, .loop, .trip])
        #expect(Self.table.count == ConfigDegrade.allCases.count * ConfigScreen.allCases.count)
        for (degrade, screen, line) in Self.table {
            #expect(degrade.notice(on: screen) == line, "\(degrade) on \(screen)")
        }
        // The loop and trip pauses are their own typed copy, by reference too.
        #expect(ConfigDegrade.planningPaused.notice(on: .loop) == LoopFailure.planningPaused.line)
        #expect(ConfigDegrade.planningPaused.notice(on: .trip) == TripFailure.planningPaused.line)
        for (degrade, screen, _) in Self.table where degrade == .pausedSurpriseOff || screen != .plan {
            #expect(degrade.notice(on: screen)?.contains("Surprise") != true, "\(degrade) on \(screen)")
        }
    }

    static let start = PlanPlace(id: 7, name: "Santa Monica Pier",
                                 coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let destination = PlanPlace(id: 42, name: "Topanga Lookout",
                                       coordinate: Coordinate(latitude: 34.09312, longitude: -118.60071))

    @Test("Under a degrade the loop and trip gates issue no ticket; clear, one; clearing reopens")
    func gates() {
        for degrade in ConfigDegrade.allCases {
            var loop = LoopSheet(disclaimerAccepted: true)
            loop.search("")
            loop.choose(Self.start)
            loop.setDegrade(degrade)
            #expect(loop.degrade == degrade)
            var trip = TripSheet(disclaimerAccepted: true)
            trip.search("", for: .start)
            trip.choose(Self.start)
            trip.search("", for: .destination)
            trip.choose(Self.destination)
            trip.setDegrade(degrade)
            #expect(trip.degrade == degrade)
            let loopTicket = loop.startPlanning()
            let tripTicket = trip.startPlanning()
            if degrade == .clear {
                #expect(loopTicket?.start == Coordinate(latitude: 34.01, longitude: -118.5))
                #expect(tripTicket != nil)
            } else {
                #expect(loopTicket == nil, "\(degrade)")
                #expect(tripTicket == nil, "\(degrade)")
                loop.setDegrade(.clear)
                trip.setDegrade(.clear)
                #expect(loop.startPlanning() != nil, "\(degrade) then clear")
                #expect(trip.startPlanning() != nil, "\(degrade) then clear")
            }
        }
    }
}
