import Foundation
import ScenicAPIClient
import ScenicKit
import Testing

/// T-0313 R1: the /trip request by FULL equality (url, method, headers, body bytes), and every bound the device
/// refuses with 0 requests - each bound just outside, each exact bound accepted with the whole request compared.
@Suite("TripClientRequestTests")
struct TripClientRequestTests {
    static func request(_ body: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/trip")!, method: "POST",
                        headers: ["content-type": "application/json", "x-scenic-device": PlanWire.deviceHeader],
                        body: Data(body.utf8))
    }

    @Test("the /trip request is exactly the whitelisted body, sent once")
    func requestByFullEquality() async {
        let fake = CountingPlanTransport(reply: TripWire.reply(200, TripWire.previewBody))
        let outcome = await TripWire.trip(through: fake, days: 3, extraBudgetPercent: 30)
        #expect(outcome == .success(TripWire.preview))
        let expected = Self.request(
            #"{"days":3,"destination":{"place":"42"},"extra_budget_pct":30,"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#)
        #expect(await fake.requests == [expected])
    }

    struct Row: Sendable {
        let label: String
        let origin: Coordinate
        let days: Int
        let percent: Int
        let vehicle: VehicleProfile
        let install: Bool
        let refusal: TripRefusal?
        let body: String?
    }

    static func row(_ label: String, lat: Double = 34.02, lon: Double = -118.49, days: Int = 2, percent: Int = 40,
                    vehicle: VehicleProfile = .standard, install: Bool = true, refusal: TripRefusal? = nil,
                    body: String? = nil) -> Row {
        Row(label: label, origin: Coordinate(latitude: lat, longitude: lon), days: days, percent: percent,
            vehicle: vehicle, install: install, refusal: refusal, body: body)
    }

    static let rows: [Row] = [
        row("days 0", days: 0, refusal: .daysOutOfRange),
        row("days 1", days: 1, body: #"{"days":1,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#),
        row("days 5", days: 5, body: #"{"days":5,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#),
        row("days 6", days: 6, refusal: .daysOutOfRange),
        row("days Int.min", days: Int.min, refusal: .daysOutOfRange),
        row("days Int.max", days: Int.max, refusal: .daysOutOfRange),
        row("percent -1", percent: -1, refusal: .extraPercentOutOfRange),
        row("percent 0", percent: 0, body: #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":0,"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#),
        row("percent 40", percent: 40, body: #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#),
        row("percent 41", percent: 41, refusal: .extraPercentOutOfRange),
        row("lat 90", lat: 90, body: #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":90,"lon":-118.49},"vehicle":"standard"}"#),
        row("lat just over 90", lat: 90.0.nextUp, refusal: .originOutOfRange),
        row("lat -90", lat: -90, body: #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":-90,"lon":-118.49},"vehicle":"standard"}"#),
        row("lat just under -90", lat: (-90.0).nextDown, refusal: .originOutOfRange),
        row("lon 180", lon: 180, body: #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":34.02,"lon":180},"vehicle":"standard"}"#),
        row("lon just over 180", lon: 180.0.nextUp, refusal: .originOutOfRange),
        row("lon -180", lon: -180, body: #"{"days":2,"destination":{"place":"42"},"extra_budget_pct":40,"origin":{"lat":34.02,"lon":-180},"vehicle":"standard"}"#),
        row("lon just under -180", lon: (-180.0).nextDown, refusal: .originOutOfRange),
        row("lat NaN", lat: .nan, refusal: .originOutOfRange),
        row("lon infinity", lon: .infinity, refusal: .originOutOfRange),
        row("lat at 3 dp", lat: 34.015, refusal: .originMoreThanTwoDecimals),
        row("lon at 3 dp", lon: -118.495, refusal: .originMoreThanTwoDecimals),
        row("no install id", install: false, refusal: .noInstallID),
    ] + VehicleProfile.allCases.filter { !$0.isEnabled }.map {
        row("vehicle \($0.rawValue)", vehicle: $0, refusal: .vehicleNotEnabled)
    }

    @Test("every bound: refused on the device with 0 requests, or sent once exactly as written",
          arguments: rows.map(\.label))
    func bounds(_ label: String) async {
        guard let row = Self.rows.first(where: { $0.label == label }) else { return }
        let fake = CountingPlanTransport(reply: TripWire.reply(200, TripWire.previewBody))
        let outcome = await TripWire.trip(through: fake, from: row.origin, days: row.days,
                                          extraBudgetPercent: row.percent, vehicle: row.vehicle, install: row.install)
        if let refusal = row.refusal {
            #expect(outcome == .failure(.refusedOnDevice(refusal)), "\(label)")
            #expect(await fake.count == 0, "\(label)")
        } else {
            #expect(outcome == .success(TripWire.preview), "\(label)")
            #expect(await fake.requests == [Self.request(row.body ?? "")], "\(label)")
        }
    }

    @Test("the table holds a refused row and an accepted row for every field it bounds")
    func tableCoversEveryField() {
        #expect(Set(Self.rows.compactMap(\.refusal)) == [.daysOutOfRange, .extraPercentOutOfRange, .originOutOfRange,
                                                         .originMoreThanTwoDecimals, .noInstallID,
                                                         .vehicleNotEnabled])
        #expect(Self.rows.filter { $0.body != nil }.count == 8)
    }
}
