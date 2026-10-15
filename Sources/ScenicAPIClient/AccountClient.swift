import Foundation

/// The app's client for the Worker's DELETE /account (T-0356; the Worker half is T-0287, P-PRIV-04): deletes every
/// server row of the session's user and revokes its Apple tokens server side.
///
/// The request carries the session as `authorization: Bearer` and nothing else - no body, no content type, never
/// `x-scenic-device` (the Worker reads only the Bearer, R2). No session token is `noSession` with ZERO requests. A
/// 401 hands the token back (`accountSessionRejected`) and, when the provider renews it to a different token, makes
/// exactly ONE more request (R4) - at most two per call. Every answer is one `AccountOutcome`.
public struct AccountClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let session: any AccountSessionProvider

    public init(base: URL, transport: any PlanTransport, session: any AccountSessionProvider) {
        self.base = base
        self.transport = transport
        self.session = session
    }

    public func deleteAccount() async -> AccountOutcome {
        guard let token = await token() else { return .noSession }
        let outcome = await send(token)
        guard outcome == .unauthorized else { return outcome }
        await session.accountSessionRejected(token)
        guard let renewed = await self.token(), renewed != token else { return .unauthorized }
        let retried = await send(renewed)
        if retried == .unauthorized { await session.accountSessionRejected(renewed) }
        return retried
    }

    /// The session the provider holds, never empty.
    func token() async -> String? {
        guard let token = await session.accountSession(), !token.isEmpty else { return nil }
        return token
    }

    private func send(_ token: String) async -> AccountOutcome {
        let request = PlanHTTPRequest(url: base.appendingPathComponent("account"), method: "DELETE",
                                      headers: ["authorization": "Bearer " + token], body: Data())
        do {
            return AccountReplyReader.read(try await transport.send(request))
        } catch {
            return .offline
        }
    }
}
