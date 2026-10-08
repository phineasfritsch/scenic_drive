import Foundation
import ScenicKit

/// POST /trip (T-0313 R1, R3). One request per call and no retries: the body is validated on the device first (a
/// refusal sends nothing), sent once with the install id PlanClient sends, and the reply read once through
/// TripReplyReader. A transport throw is routingOffline.
public struct TripClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let installID: (any InstallIDProvider)?
    let accountToken: (any AccountTokenProvider)?

    public init(base: URL, transport: any PlanTransport, installID: (any InstallIDProvider)?,
                accountToken: (any AccountTokenProvider)?) {
        self.base = base
        self.transport = transport
        self.installID = installID
        self.accountToken = accountToken
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

        let request = PlanHTTPRequest(url: base.appendingPathComponent("trip"), method: "POST",
                                      headers: IdentityHeaders.json(device: installID.installID(),
                                                                     account: await accountToken?.accountToken()),
                                      body: bytes)
        let reply: PlanHTTPReply
        do {
            reply = try await transport.send(request)
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
