import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0360 acceptance A1 (R2-R4): every case drives `WaitlistClient.joinWaitlist(near:)`, the entry point the app's
/// WaitlistRoutePlanner calls, over CountingPlanTransport. The whole request is compared to its recomputation; every
/// Worker answer is one WaitlistAnswer after exactly one request; every bound of the start is sent at the bound or
/// refused with zero requests; the cell is computed from the 2-dp start; a cell is joined once per install.
@Suite("WaitlistClientTests") struct WaitlistClientTests {
    static let cell = "85283473fffffff"
    static let other = "850dab63fffffff"
    static let device = "6F9619FF-8B86-D011-B42D-00C04FC964FF"
    static let waitlistURL = URL(string: "https://scenic-api.test/waitlist")!
    static let la = Coordinate(latitude: 34.0212, longitude: -118.4912)

    static func client(_ fake: CountingPlanTransport, cells: RecordingCellOf = RecordingCellOf(cell),
                       memory: MemoryWaitlist = MemoryWaitlist()) -> WaitlistClient {
        WaitlistClient(base: URL(string: "https://scenic-api.test")!, transport: fake,
                       installID: FixedInstallID(device), memory: memory,
                       cellOf: { cells.cell($0, $1) })
    }

    static func reply(_ status: Int, _ body: String) -> CountingPlanTransport {
        CountingPlanTransport(reply: PlanHTTPReply(status: status, body: Data(body.utf8)))
    }

    /// The one request R2 allows for `cell`, recomputed here.
    static func request(_ cell: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: waitlistURL, method: "POST",
                        headers: ["content-type": "application/json",
                                  "x-scenic-device": device.lowercased()],
                        body: Data("{\"cell\":\"\(cell)\"}".utf8))
    }

    @Test("POST /waitlist is exactly the content type, the device and {cell}",
          arguments: [(34.0212, -118.4912, cell), (-33.8651, 151.2093, other), (90.0, 180.0, "09af09af09af09a")])
    func wholeRequest(_ latitude: Double, _ longitude: Double, _ cell: String) async {
        let fake = Self.reply(200, #"{"waitlisted":true}"#)
        let memory = MemoryWaitlist()
        let answer = await Self.client(fake, cells: RecordingCellOf(cell), memory: memory)
            .joinWaitlist(near: Coordinate(latitude: latitude, longitude: longitude))
        #expect(await fake.requests == [Self.request(cell)])
        #expect(answer == .joined)
        #expect(memory.remembered == [cell])
    }

    @Test("Every Worker answer is one WaitlistAnswer after exactly one request, remembered only when joined",
          arguments: [
              (200, #"{"waitlisted":true}"#, WaitlistAnswer.joined),
              (200, #"{"waitlisted":false}"#, .failed),
              (200, "{}", .failed),
              (200, "not json", .failed),
              (400, #"{"error":"invalid_request","detail":"the body must be exactly {cell}"}"#, .failed),
              (404, #"{"error":"not found"}"#, .failed),
              (405, #"{"error":"POST only"}"#, .failed),
              (429, "{}", .failed),
              (500, "", .failed),
              (502, "", .failed),
              (503, #"{"error":"waitlist_unavailable"}"#, .unavailable),
          ])
    func everyAnswer(_ status: Int, _ body: String, _ expected: WaitlistAnswer) async {
        let fake = Self.reply(status, body)
        let memory = MemoryWaitlist()
        let answer = await Self.client(fake, memory: memory).joinWaitlist(near: Self.la)
        #expect(answer == expected)
        #expect(await fake.requests == [Self.request(Self.cell)])
        #expect(memory.remembered == (expected == .joined ? [Self.cell] : []))
    }

    @Test("No reply at all is offline, after exactly one request, and nothing is remembered")
    func offline() async {
        let fake = CountingPlanTransport.offline()
        let memory = MemoryWaitlist()
        let answer = await Self.client(fake, memory: memory).joinWaitlist(near: Self.la)
        #expect(answer == .offline)
        #expect(await fake.requests == [Self.request(Self.cell)])
        #expect(memory.remembered.isEmpty)
    }

    /// (latitude, longitude, the point cellOf must receive - nil: refused on the device with zero requests).
    static let bounds: [(Double, Double, [Double]?)] = [
        (-90, 0, [-90, 0]), (90, 0, [90, 0]), (0, -180, [0, -180]), (0, 180, [0, 180]),
        (-90, -180, [-90, -180]), (90, 180, [90, 180]),
        ((-90.0).nextDown, 0, nil), ((90.0).nextUp, 0, nil), (0, (-180.0).nextDown, nil), (0, (180.0).nextUp, nil),
        (-90.004, 0, nil), (90.004, 0, nil), (0, -180.004, nil), (0, 180.004, nil),
        (.nan, 0, nil), (0, .nan, nil), (.infinity, 0, nil), (-.infinity, 0, nil), (0, .infinity, nil),
        (0, -.infinity, nil),
    ]

    @Test("Every bound of the start: exact bounds reach cellOf, anything outside is refused with zero requests",
          arguments: bounds.indices)
    func everyBound(_ row: Int) async {
        let (latitude, longitude, sent) = Self.bounds[row]
        let fake = Self.reply(200, #"{"waitlisted":true}"#)
        let cells = RecordingCellOf(Self.cell)
        let answer = await Self.client(fake, cells: cells)
            .joinWaitlist(near: Coordinate(latitude: latitude, longitude: longitude))
        if let sent {
            #expect(cells.asked == [sent], "row \(row)")
            #expect(await fake.requests == [Self.request(Self.cell)], "row \(row)")
            #expect(answer == .joined, "row \(row)")
        } else {
            #expect(cells.asked.isEmpty, "row \(row)")
            #expect(await fake.count == 0, "row \(row)")
            #expect(answer == .refusedOnDevice, "row \(row)")
        }
    }

    @Test("The cell is computed from the start at two decimals, half away from zero",
          arguments: [
              (34.0212, -118.4912, [34.02, -118.49]), (34.0249, -118.4951, [34.02, -118.50]),
              (-33.8651, 151.2093, [-33.87, 151.21]), (34.125, -118.375, [34.13, -118.38]),
              (0.004, -0.004, [0.0, 0.0]), (89.996, 179.996, [90.0, 180.0]), (12.0, -7.5, [12.0, -7.5]),
          ])
    func twoDecimals(_ latitude: Double, _ longitude: Double, _ sent: [Double]) async {
        let fake = Self.reply(200, #"{"waitlisted":true}"#)
        let cells = RecordingCellOf(Self.cell)
        _ = await Self.client(fake, cells: cells).joinWaitlist(near: Coordinate(latitude: latitude, longitude: longitude))
        #expect(cells.asked == [sent])
        #expect(await fake.count == 1)
    }

    @Test("A cell the Worker would refuse on its first test is refused on the device and nothing is sent",
          arguments: [nil, "", "85283473ffffff", "85283473fffffff0", "85283473FFFFFFF", "85283473ffffffg",
                      "8528347 fffffff", "85283473ffffff/", "85283473ffffff:", "85283473ffffff`", " 85283473ffffff"])
    func cellRefused(_ cell: String?) async {
        let fake = Self.reply(200, #"{"waitlisted":true}"#)
        let memory = MemoryWaitlist()
        let answer = await Self.client(fake, cells: RecordingCellOf(cell), memory: memory).joinWaitlist(near: Self.la)
        #expect(answer == .refusedOnDevice)
        #expect(await fake.count == 0)
        #expect(memory.remembered.isEmpty)
    }

    @Test("Every hex position admits 0, 9, a and f - the bounds of both classes",
          arguments: ["000000000000000", "999999999999999", "aaaaaaaaaaaaaaa", "fffffffffffffff"])
    func cellClassBounds(_ cell: String) async {
        let fake = Self.reply(200, #"{"waitlisted":true}"#)
        let answer = await Self.client(fake, cells: RecordingCellOf(cell)).joinWaitlist(near: Self.la)
        #expect(await fake.requests == [Self.request(cell)])
        #expect(answer == .joined)
    }

    @Test("Once per cell per install: a joined cell sends nothing again, another cell sends, a failed cell sends again")
    func oncePerCell() async {
        let joined = Self.reply(200, #"{"waitlisted":true}"#)
        let memory = MemoryWaitlist([Self.cell])
        let again = await Self.client(joined, memory: memory).joinWaitlist(near: Self.la)
        #expect(again == .alreadyJoined)
        #expect(await joined.count == 0)
        let fresh = await Self.client(joined, cells: RecordingCellOf(Self.other), memory: memory)
            .joinWaitlist(near: Self.la)
        #expect(fresh == .joined)
        #expect(await joined.requests == [Self.request(Self.other)])
        #expect(memory.remembered == [Self.cell, Self.other])
        let down = Self.reply(503, #"{"error":"waitlist_unavailable"}"#)
        let empty = MemoryWaitlist()
        #expect(await Self.client(down, memory: empty).joinWaitlist(near: Self.la) == .unavailable)
        #expect(await Self.client(down, memory: empty).joinWaitlist(near: Self.la) == .unavailable)
        #expect(await down.requests == [Self.request(Self.cell), Self.request(Self.cell)])
        #expect(empty.remembered.isEmpty)
    }
}
