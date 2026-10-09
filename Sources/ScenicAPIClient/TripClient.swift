import Foundation
import ScenicKit

/// POST /trip (T-0313 R1, R3). One request per call and no retries - but ONE resend after a 401 to its Bearer
/// (T-0333 R3, PlanFamilySend): the body is validated on the device first (a
/// refusal sends nothing), sent once with the install id PlanClient sends, and the reply read once through
/// TripReplyReader. A transport throw is routingOffline.
public struct TripClient: Sendable {
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

    public func trip(from origin: Coordinate, to place: Int64, days: Int, extraBudgetPercent: Int,
                     vehicle: VehicleProfile = .standard) async throws(TripError) -> TripResponse {
        guard let installID else { throw .refusedOnDevice(.noInstallID) }
        let body: TripRequestBody
        switch TripRequestBody.validated(origin: origin, place: place, days: days,
                                         extraBudgetPercent: extraBudgetPercent, vehicle: vehicle) {
        case .failure(let refusal):
            throw .refusedOnDevice(refusal)
        case .success(let validated):
            body = validated
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        guard let bytes = try? encoder.encode(body) else { throw .refusedOnDevice(.originOutOfRange) }

        let account = await accountToken?.accountToken()
        let reply: PlanHTTPReply
        do {
            // T-0333 R3: a 401 to a Bearer is handed back, the session asked again, and the same bytes sent once more.
            reply = try await PlanFamilySend.send(base.appendingPathComponent("trip"), body: bytes,
                                                  device: installID.installID(), account: account, session: session,
                                                  transport: transport)
        } catch {
            throw .routingOffline
        }
        switch TripReplyReader.read(reply) {
        case .success(let trip):
            return trip
        case .failure(let error):
            throw error
        }
    }
}
