import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import ScenicAPIClient
import ScenicKit
import XCTest

/// The production pair - `PlanClient.plan` over `URLSessionPlanTransport` - with only the socket replaced: a stub
/// URLProtocol on the transport's session reads the URLRequest the transport built and answers a recorded reply.
/// Every other test drives the counting fake, which never sees what URLSession is handed (T-0251 pre-review MC).
final class URLSessionPlanTransportTests: XCTestCase {
    func testURLSessionCarriesTheWholeRequestAndReturnsTheWholeReply() async throws {
        let session = StubPlanURLProtocol.session(answering: try PlanWire.recordedReply("502-no-route"))
        let transport = URLSessionPlanTransport(timeout: 12, session: session)
        let outcome = await PlanWire.plan(through: transport, to: 1_234_567_890_123, budgetMinutes: 25)
        let seen = StubPlanURLProtocol.seen()
        let body = #"{"budget_minutes":25,"destination":{"place":"1234567890123"},"origin":{"lat":34.02,"lon":-118.49}}"#
        XCTAssertEqual(seen.requests, [PlanHTTPRequest(
            url: URL(string: "https://scenic-api.test/plan")!, method: "POST",
            headers: ["content-type": "application/json", "x-scenic-device": PlanWire.deviceHeader],
            body: Data(body.utf8))])
        XCTAssertEqual(seen.timeouts, [12])
        // 502 is .noRoute only with the no_route body: status and body bytes both came back through URLSession.
        XCTAssertEqual(PlanWire.error(outcome), .noRoute)
    }
}
