import Foundation

/// The app's client for the Worker's GET and POST /ledger (T-0302, T-0307): the Surprise places a signed-in device
/// was shown, kept 90 days by the server so the no-repeat survives a reinstall.
///
/// One call, at most one request, one `LedgerOutcome` (R4) - nothing is retried, a 429 or a 401 included. No session
/// token, or an entry the Worker would refuse, is answered on the device with ZERO requests (R2, R3). The request
/// carries the session as `authorization: Bearer` and nothing else that identifies anyone: never `x-scenic-device`,
/// the legacy header path T-0302 R1 refuses.
public struct LedgerClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let session: any LedgerSessionProvider

    public init(base: URL, transport: any PlanTransport, session: any LedgerSessionProvider) {
        self.base = base
        self.transport = transport
        self.session = session
    }

    /// POST /ledger {cell, place_id}: the place `placeId`, in H3 resolution-5 cell `cell` (the PLACE's), was shown.
    public func record(placeId: String, cell: String) async -> LedgerOutcome {
        guard let token = await token() else { return .noSession }
        guard let entry = LedgerEntry(placeId: placeId, cell: cell) else { return .refusedOnDevice }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        // Two ASCII strings: this encoder cannot throw on them.
        guard let body = try? encoder.encode(entry) else { return .refusedOnDevice }
        return await send(PlanHTTPRequest(url: url, method: "POST",
                                          headers: ["authorization": "Bearer \(token)",
                                                    "content-type": "application/json"],
                                          body: body), isRead: false)
    }

    /// GET /ledger: this session's places of the last 90 UTC days.
    public func read() async -> LedgerOutcome {
        guard let token = await token() else { return .noSession }
        return await send(PlanHTTPRequest(url: url, method: "GET", headers: ["authorization": "Bearer \(token)"],
                                          body: Data()), isRead: true)
    }

    private var url: URL { base.appendingPathComponent("ledger") }

    private func token() async -> String? {
        guard let token = await session.sessionToken(), !token.isEmpty else { return nil }
        return token
    }

    private func send(_ request: PlanHTTPRequest, isRead: Bool) async -> LedgerOutcome {
        do {
            return LedgerReplyReader.read(try await transport.send(request), isRead: isRead)
        } catch {
            return .offline
        }
    }
}
