import Foundation
import ScenicKit

/// The app's client for the Worker's POST /search (T-0359): typed address search through our Photon.
///
/// One call, at most one request, one `SearchOutcome` - nothing is retried. The body is the query and at most one
/// bias coordinate rounded to 2 dp on the device (`SearchRequestBody`); a query or bias the Worker would refuse is
/// answered here with ZERO requests. The request carries the JSON content type and `x-scenic-device` (the daily
/// search allowance is the install's; without it every device would share one bucket). T-0362 R2: the request carries
/// EXACTLY /plan's identity - PlanFamilySend, IdentityHeaders' one set: the purchase's account token when held and the
/// session whose act is that purchase as a Bearer, re-sent once after a 401 to that Bearer - because the Worker
/// remembers each row's place id under the identity /plan will compute, and that set is what reads the paid allowance.
/// No install id: refused here, zero requests.
public struct SearchClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let installID: (any InstallIDProvider)?
    let accountToken: (any AccountTokenProvider)?
    let session: (any PlanSessionProvider)?

    public init(base: URL, transport: any PlanTransport, installID: (any InstallIDProvider)?,
                accountToken: (any AccountTokenProvider)?, session: (any PlanSessionProvider)?) {
        self.base = base
        self.transport = transport
        self.installID = installID
        self.accountToken = accountToken
        self.session = session
    }

    public func search(_ query: String, near: Coordinate?) async -> SearchOutcome {
        guard let installID, let body = SearchRequestBody(query: query, near: near) else { return .refusedOnDevice }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys, .withoutEscapingSlashes]
        // A string and two finite doubles: this encoder cannot throw on them.
        guard let data = try? encoder.encode(body) else { return .refusedOnDevice }
        let account = await accountToken?.accountToken()
        do {
            return SearchReplyReader.read(try await PlanFamilySend.send(base.appendingPathComponent("search"), body: data,
                                                                        device: installID.installID(), account: account,
                                                                        session: session, transport: transport))
        } catch {
            return .offline
        }
    }
}
