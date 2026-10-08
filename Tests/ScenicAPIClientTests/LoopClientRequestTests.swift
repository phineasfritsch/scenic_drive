import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0314 R1: the /loop request by FULL equality (url, method, headers, body bytes), and every bound the device
/// refuses with 0 requests - each bound just outside, each exact bound accepted with the whole request compared.
@Suite("LoopClientRequestTests")
struct LoopClientRequestTests {
    static func request(_ body: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/loop")!, method: "POST",
                        headers: ["content-type": "application/json", "x-scenic-device": PlanWire.deviceHeader],
                        body: Data(body.utf8))
    }

    static func body(minutes: Int = 45, lat: String = "34.02", lon: String = "-118.49") -> String {
        #"{"minutes":\#(minutes),"start":{"lat":\#(lat),"lon":\#(lon)},"vehicle":"standard"}"#
    }

    @Test("the /loop request is exactly the whitelisted body, one coordinate at 2 dp, sent once")
    func requestByFullEquality() async {
        let fake = CountingPlanTransport(reply: LoopWire.reply(200, LoopWire.squareBody))
        let outcome = await LoopWire.loop(through: fake, minutes: 60)
        #expect(outcome == .success(LoopWire.response()))
        #expect(await fake.requests == [Self.request(#"{"minutes":60,"start":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#)])
    }

    struct Row: Sendable {
        let label: String
        let start: Coordinate
        let minutes: Int
        let vehicle: VehicleProfile
        let install: Bool
        let refusal: LoopRefusal?
        let body: String?
    }

    static func row(_ label: String, lat: Double = 34.02, lon: Double = -118.49, minutes: Int = 45,
                    vehicle: VehicleProfile = .standard, install: Bool = true, refusal: LoopRefusal? = nil,
                    body: String? = nil) -> Row {
        Row(label: label, start: Coordinate(latitude: lat, longitude: lon), minutes: minutes, vehicle: vehicle,
            install: install, refusal: refusal, body: body)
    }

    static let rows: [Row] = [
        row("minutes Int.min", minutes: Int.min, refusal: .minutesOutOfRange),
        row("minutes 9", minutes: 9, refusal: .minutesOutOfRange),
        row("minutes 10", minutes: 10, body: body(minutes: 10)),
        row("minutes 180", minutes: 180, body: body(minutes: 180)),
        row("minutes 181", minutes: 181, refusal: .minutesOutOfRange),
        row("minutes Int.max", minutes: Int.max, refusal: .minutesOutOfRange),
        row("lat 90", lat: 90, body: body(lat: "90")),
        row("lat just over 90", lat: 90.0.nextUp, refusal: .startOutOfRange),
        row("lat -90", lat: -90, body: body(lat: "-90")),
        row("lat just under -90", lat: (-90.0).nextDown, refusal: .startOutOfRange),
        row("lon 180", lon: 180, body: body(lon: "180")),
        row("lon just over 180", lon: 180.0.nextUp, refusal: .startOutOfRange),
        row("lon -180", lon: -180, body: body(lon: "-180")),
        row("lon just under -180", lon: (-180.0).nextDown, refusal: .startOutOfRange),
        row("lat NaN", lat: .nan, refusal: .startOutOfRange),
        row("lon infinity", lon: .infinity, refusal: .startOutOfRange),
        row("lat at 3 dp", lat: 34.015, refusal: .startMoreThanTwoDecimals),
        row("lon at 3 dp", lon: -118.495, refusal: .startMoreThanTwoDecimals),
        row("no install id", install: false, refusal: .noInstallID),
    ] + VehicleProfile.allCases.filter { !$0.isEnabled }.map {
        row("vehicle \($0.rawValue)", vehicle: $0, refusal: .vehicleNotEnabled)
    }

    @Test("every bound: refused on the device with 0 requests, or sent once exactly as written",
          arguments: rows.map(\.label))
    func bounds(_ label: String) async {
        guard let row = Self.rows.first(where: { $0.label == label }) else { return }
        let fake = CountingPlanTransport(reply: LoopWire.reply(200, LoopWire.squareBody))
        let outcome = await LoopWire.loop(through: fake, from: row.start, minutes: row.minutes, vehicle: row.vehicle,
                                          install: row.install)
        if let refusal = row.refusal {
            #expect(outcome == .failure(.refusedOnDevice(refusal)), "\(label)")
            #expect(await fake.count == 0, "\(label)")
        } else {
            #expect(outcome == .success(LoopWire.response()), "\(label)")
            #expect(await fake.requests == [Self.request(row.body ?? "")], "\(label)")
        }
    }

    @Test("the table holds a refused row and an accepted row for every field it bounds")
    func tableCoversEveryField() {
        #expect(Set(Self.rows.compactMap(\.refusal)) == [.minutesOutOfRange, .startOutOfRange,
                                                         .startMoreThanTwoDecimals, .noInstallID,
                                                         .vehicleNotEnabled])
        #expect(Self.rows.filter { $0.body != nil }.count == 6)
    }
}
