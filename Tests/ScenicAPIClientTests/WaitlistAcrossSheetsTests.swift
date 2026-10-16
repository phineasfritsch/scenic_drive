import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0365 A1(d), R3/R4: the plan, loop and trip sheets each join the waitlist from their own `waitlistStart` through
/// the app's ONE WaitlistClient and its one WaitlistMemory, so a cell joined from any sheet is joined once per
/// install - the second sheet answers alreadyJoined and sends nothing. Every pair of sheets, in both orders and with
/// itself; the whole request compared to its recomputation (WaitlistClientTests.request).
@Suite("WaitlistAcrossSheetsTests") struct WaitlistAcrossSheetsTests {
    enum Sheet: String, CaseIterable, Sendable { case plan, loop, trip }

    static let pier = PlanPlace(id: 7, name: "Santa Monica Pier",
                                coordinate: Coordinate(latitude: 34.00862, longitude: -118.49853))
    static let ojai = PlanPlace(id: 9, name: "Ojai", coordinate: Coordinate(latitude: 34.448, longitude: -119.243))
    static let zuma = PlanPlace(id: 42, name: "Zuma", coordinate: Coordinate(latitude: 34.015, longitude: -118.822))

    /// `sheet` failed with its regionUnsupported from `place`, and the start it hands "Count this area".
    static func waitlistStart(_ sheet: Sheet, from place: PlanPlace) -> Coordinate? {
        switch sheet {
        case .plan:
            var plan = PlanSheet(disclaimerAccepted: true)
            plan.search("q", for: .start)
            plan.choose(place)
            plan.search("z", for: .destination)
            plan.choose(zuma)
            if let ticket = plan.startPlanning() { plan.finish(ticket, with: .failure(.regionUnsupported)) }
            return plan.waitlistStart
        case .loop:
            var loop = LoopSheet(disclaimerAccepted: true)
            loop.search("q")
            loop.choose(place)
            if let ticket = loop.startPlanning() { loop.finish(ticket, with: .failure(.regionUnsupported)) }
            return loop.waitlistStart
        case .trip:
            var trip = TripSheet(disclaimerAccepted: true)
            trip.search("q", for: .start)
            trip.choose(place)
            trip.search("z", for: .destination)
            trip.choose(zuma)
            if let ticket = trip.startPlanning() { trip.finish(ticket, with: .failure(.regionUnsupported)) }
            return trip.waitlistStart
        }
    }

    @Test("a cell joined from one sheet is alreadyJoined from every other with zero requests",
          arguments: Sheet.allCases, Sheet.allCases)
    func crossSheet(_ first: Sheet, _ second: Sheet) async throws {
        let fake = WaitlistClientTests.reply(200, #"{"waitlisted":true}"#)
        let memory = MemoryWaitlist()
        let cells = RecordingCellOf(WaitlistClientTests.cell)
        let client = WaitlistClientTests.client(fake, cells: cells, memory: memory)
        let firstStart = try #require(Self.waitlistStart(first, from: Self.pier))
        let secondStart = try #require(Self.waitlistStart(second, from: Self.pier))
        #expect(await client.joinWaitlist(near: firstStart) == .joined)
        #expect(await fake.requests == [WaitlistClientTests.request(WaitlistClientTests.cell)])
        #expect(await client.joinWaitlist(near: secondStart) == .alreadyJoined)
        #expect(await fake.requests == [WaitlistClientTests.request(WaitlistClientTests.cell)])
        #expect(memory.remembered == [WaitlistClientTests.cell])
        #expect(cells.asked == [[34.01, -118.5], [34.01, -118.5]])
    }

    @Test("another start's cell is still sent from every other sheet: the memory is per cell, not per tap",
          arguments: Sheet.allCases, Sheet.allCases)
    func otherCellSends(_ first: Sheet, _ second: Sheet) async throws {
        let fake = WaitlistClientTests.reply(200, #"{"waitlisted":true}"#)
        let memory = MemoryWaitlist()
        let cells = RecordingCellOf(answer: { latitude, _ in
            latitude == 34.01 ? WaitlistClientTests.cell : WaitlistClientTests.other
        })
        let client = WaitlistClientTests.client(fake, cells: cells, memory: memory)
        let firstStart = try #require(Self.waitlistStart(first, from: Self.pier))
        let secondStart = try #require(Self.waitlistStart(second, from: Self.ojai))
        #expect(await client.joinWaitlist(near: firstStart) == .joined)
        #expect(await client.joinWaitlist(near: secondStart) == .joined)
        #expect(await fake.requests == [WaitlistClientTests.request(WaitlistClientTests.cell),
                                        WaitlistClientTests.request(WaitlistClientTests.other)])
        #expect(memory.remembered == [WaitlistClientTests.cell, WaitlistClientTests.other])
        #expect(cells.asked == [[34.01, -118.5], [34.45, -119.24]])
    }
}
