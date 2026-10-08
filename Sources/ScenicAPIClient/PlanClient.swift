import Foundation
import ScenicKit

/// The app's client for the Worker's POST /plan (T-0251). One call, one request, one typed outcome.
///
/// The request carries ONE coordinate, already at 2 dp, and a corpus place id (R3); anything else is refused
/// here with zero requests made, as is a plan from a client with no install id; every request carries
/// `x-scenic-device`, the install id lowercased (T-0260), plus the purchase's `x-scenic-account-token` when
/// the device holds one - IdentityHeaders' one header set (T-0315 R1, R2). Every reply - and the absence of one -
/// is a `PlanResponse` or a `PlanError` by the R6 table in `PlanResponseReader`.
public struct PlanClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let installID: (any InstallIDProvider)?
    let accountToken: (any AccountTokenProvider)?

    /// `installID` has no default: a client without one must say so (`nil`), and every plan it makes is then
    /// refused on the device as `.noInstallID` (T-0260 R3).
    public init(base: URL, transport: any PlanTransport, installID: (any InstallIDProvider)?,
                accountToken: (any AccountTokenProvider)?) {
        self.base = base
        self.transport = transport
        self.installID = installID
        self.accountToken = accountToken
    }

    /// Plans `origin` -> the corpus place `place` with `budgetMinutes` of extra time, for `vehicle` (T-0311 R6:
    /// `.standard` unless named - the only profile the stored read can return today).
    public func plan(from origin: Coordinate, to place: Int64, budgetMinutes: Int,
                     departsAt: Date? = nil, vehicle: VehicleProfile = .standard)
        async throws(PlanError) -> PlanResponse {
        // No install id, no request: without x-scenic-device the Worker bills the shared unidentified bucket.
        guard let installID else { throw .refusedOnDevice(.noInstallID) }
        let body: PlanRequestBody
        switch PlanRequestBody.validated(origin: origin, place: place, budgetMinutes: budgetMinutes,
                                         departsAt: departsAt, vehicle: vehicle) {
        case .failure(let refusal):
            throw .refusedOnDevice(refusal)
        case .success(let validated):
            body = validated
        }
        return try await send(body, installID: installID)
    }

    /// T-0319 R9: the rest of THIS drive. The origin is rounded to 2 dp HERE, on the device - the fix is full
    /// precision. remainingWaypoints, the destination coordinate and lambda stay on the device: the Worker
    /// remembered them under `token`, and the request names only the token and `firstRemainingWaypoint`.
    public func reroute(_ request: RerouteRequest, token: String, place: Int64, budgetMinutes: Int,
                        vehicle: VehicleProfile = VehicleProfile.standard) async throws(PlanError) -> PlanResponse {
        guard let installID else { throw .refusedOnDevice(.noInstallID) }
        let origin = Coordinate(latitude: (request.origin.latitude * 100).rounded() / 100,
                                longitude: (request.origin.longitude * 100).rounded() / 100)
        switch PlanRequestBody.validatedReroute(origin: origin, place: place, budgetMinutes: budgetMinutes,
                                                vehicle: vehicle, token: token,
                                                firstPin: request.firstRemainingWaypoint) {
        case .failure(let refusal):
            throw .refusedOnDevice(refusal)
        case .success(let body):
            return try await send(body, installID: installID)
        }
    }

    /// One validated body, encoded with sorted keys, as ONE request carrying IdentityHeaders' set; the reply by R6.
    private func send(_ body: PlanRequestBody, installID: any InstallIDProvider) async throws(PlanError) -> PlanResponse {
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        // Only a non-finite Double can make this encoder throw, and validated() refused those as out of range.
        guard let bytes = try? encoder.encode(body) else { throw .refusedOnDevice(.originOutOfRange) }

        let request = PlanHTTPRequest(url: base.appendingPathComponent("plan"), method: "POST",
                                      headers: IdentityHeaders.json(device: installID.installID(),
                                                                     account: await accountToken?.accountToken()),
                                      body: bytes)
        let reply: PlanHTTPReply
        do {
            reply = try await transport.send(request)
        } catch {
            throw .routingOffline
        }
        switch PlanResponseReader.read(reply) {
        case .success(let plan):
            return plan
        case .failure(let error):
            throw error
        }
    }
}
