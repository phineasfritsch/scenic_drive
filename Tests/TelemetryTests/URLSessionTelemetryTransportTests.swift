import Foundation
#if canImport(FoundationNetworking)
import FoundationNetworking
#endif
import Testing
@testable import Telemetry

/// T-0355 round 1 (B1): the SHIPPING URLSessionTelemetryTransport under the shipping TelemetryClient. Every
/// TelemetryClientTests test stops at the TelemetryTransport seam; here the seam is the production transport and
/// only the network below it is a stub, so a transport that drops the method (a GET the Worker answers 405), the
/// headers or the body is red by name. One test: the stub's capture is process-wide state.
@Suite("URLSessionTelemetryTransport") struct URLSessionTelemetryTransportTests {
    @Test func shippingTransportPostsTheWholeRequestNotAGet() async throws {
        for row in TelemetryEventEncodingTests.rows {
            let session = StubTelemetryURLProtocol.session(answering: 405)
            let client = TelemetryClient(base: TelemetryClientTests.base, device: { TelemetryClientTests.device },
                                         transport: URLSessionTelemetryTransport(session: session))
            await client.record(row.event)
            #expect(StubTelemetryURLProtocol.seen() == [try TelemetryClientTests.expected([row.event])],
                    "\(row.event)")
        }
        // The status is the stubbed one, read from the HTTPURLResponse - never a default.
        let request = try TelemetryClientTests.expected([.previewShown])
        for status in [200, 400, 405, 429, 503] {
            let session = StubTelemetryURLProtocol.session(answering: status)
            let got = try await URLSessionTelemetryTransport(session: session).send(request)
            #expect(got == status)
            #expect(StubTelemetryURLProtocol.seen() == [request], "status \(status)")
        }
    }
}
