import Foundation
import ScenicAPIClient
import ScenicKit
import XCTest

/// T-0260: every request `PlanClient.plan` builds carries `x-scenic-device`, the injected install id lowercased -
/// the form services/api/src/routerDeps.ts `DEVICE_ID` accepts - and nothing else identifying; a client with no
/// provider sends nothing. Every assertion is on the whole recorded request, by exact equality.
final class PlanClientDeviceTests: XCTestCase {
    private let ok = PlanHTTPReply(status: 200, body: Data())
    private let body = #"{"budget_minutes":25,"destination":{"place":"42"},"origin":{"lat":34.02,"lon":-118.49},"vehicle":"standard"}"#

    private func request(device: String, body: String) -> PlanHTTPRequest {
        PlanHTTPRequest(url: URL(string: "https://scenic-api.test/plan")!, method: "POST",
                        headers: ["content-type": "application/json", "x-scenic-device": device],
                        body: Data(body.utf8))
    }

    func testRefusesAPlanWithNoInstallIDProviderAndSendsNothing() async {
        let (outcome, fake) = await PlanWire.plan(answering: ok, installID: nil)
        XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.noInstallID))
        let count = await fake.count
        XCTAssertEqual(count, 0)
    }

    func testNoInstallIDIsRefusedBeforeTheOriginIsJudged() async {
        let (outcome, fake) = await PlanWire.plan(answering: ok,
                                                  from: Coordinate(latitude: 34.021, longitude: -118.49),
                                                  installID: nil)
        XCTAssertEqual(PlanWire.error(outcome), .refusedOnDevice(.noInstallID))
        let count = await fake.count
        XCTAssertEqual(count, 0)
    }

    func testSendsTheInjectedProvidersIDLowercasedAsTheWholeHeaderSet() async {
        let other = FixedInstallID("E621E1F8-C36C-495A-93FC-0C247A3E6E5F")
        let (_, fake) = await PlanWire.plan(answering: ok, installID: other)
        let sent = await fake.requests
        XCTAssertEqual(sent, [request(device: "e621e1f8-c36c-495a-93fc-0c247a3e6e5f", body: body)])
    }

    func testOneClientSendsTheSameIDFromEveryOrigin() async {
        let fake = CountingPlanTransport(reply: ok)
        let client = PlanClient(base: PlanWire.base, transport: fake, installID: PlanWire.install, accountToken: nil)
        for origin in [PlanWire.santaMonica, Coordinate(latitude: 37.77, longitude: -122.42)] {
            _ = try? await client.plan(from: origin, to: 42, budgetMinutes: 25)
        }
        let sent = await fake.requests
        XCTAssertEqual(sent, [
            request(device: PlanWire.deviceHeader, body: body),
            request(device: PlanWire.deviceHeader,
                    body: #"{"budget_minutes":25,"destination":{"place":"42"},"origin":{"lat":37.77,"lon":-122.42},"vehicle":"standard"}"#),
        ])
    }
}
