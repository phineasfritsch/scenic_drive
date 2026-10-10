import Foundation
import ScenicKit

/// The app's client for the Worker's POST /search (T-0359): typed address search through our Photon.
///
/// One call, at most one request, one `SearchOutcome` - nothing is retried. The body is the query and at most one
/// bias coordinate rounded to 2 dp on the device (`SearchRequestBody`); a query or bias the Worker would refuse is
/// answered here with ZERO requests. The request carries the JSON content type and `x-scenic-device` (the daily
/// search allowance is the install's; without it every device would share one bucket) and nothing else: no account
/// token and no session in this task - the paid allowance is the app wiring's follow-up.
public struct SearchClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let device: UUID

    public init(base: URL, transport: any PlanTransport, device: UUID) {
        self.base = base
        self.transport = transport
        self.device = device
    }

    public func search(_ query: String, near: Coordinate?) async -> SearchOutcome {
        guard let body = SearchRequestBody(query: query, near: near) else { return .refusedOnDevice }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        // A string and two finite doubles: this encoder cannot throw on them.
        guard let data = try? encoder.encode(body) else { return .refusedOnDevice }
        let request = PlanHTTPRequest(url: base.appendingPathComponent("search"), method: "POST",
                                      headers: IdentityHeaders.json(device: device, account: nil, bearer: nil),
                                      body: data)
        do {
            return SearchReplyReader.read(try await transport.send(request))
        } catch {
            return .offline
        }
    }
}
