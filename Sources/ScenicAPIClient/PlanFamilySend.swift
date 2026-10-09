import Foundation

/// The one send of every plan-family request - POST /plan, /trip and /loop - with IdentityHeaders' set (T-0333 R3).
/// A reply of 401 (`session_rejected`: the Worker could not verify the Bearer, e.g. after a SESSION_JWT_SECRET rotation)
/// to a request that CARRIED a Bearer hands that token back to the session provider, asks it again for the same
/// purchase, and sends the byte-identical body ONCE more with the answer - a Bearer, or none. That second reply is
/// final: a 401 to it hands its token back too, and is returned to the route's reader. Never a third request; a request
/// with no Bearer is never resent. The body is the same bytes, so the server learns no second coordinate.
enum PlanFamilySend {
    static let rejectedStatus = 401

    static func send(_ url: URL, body: Data, device: UUID, account: UUID?, session: (any PlanSessionProvider)?,
                     transport: any PlanTransport) async throws -> PlanHTTPReply {
        func request(_ bearer: String?) -> PlanHTTPRequest {
            PlanHTTPRequest(url: url, method: "POST",
                            headers: IdentityHeaders.json(device: device, account: account, bearer: bearer), body: body)
        }
        let bearer = await session?.planSession(account: account)
        let first = try await transport.send(request(bearer))
        guard first.status == rejectedStatus, let bearer, let session else { return first }
        await session.planSessionRejected(bearer)
        let renewed = await session.planSession(account: account)
        let second = try await transport.send(request(renewed))
        if second.status == rejectedStatus, let renewed { await session.planSessionRejected(renewed) }
        return second
    }
}
