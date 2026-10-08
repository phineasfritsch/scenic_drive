import Foundation
import ScenicKit

/// The app's client for the Worker's POST /plan (T-0251). One call, one request, one typed outcome.
///
/// The request carries ONE coordinate, already at 2 dp, and a corpus place id (R3); anything else is refused
/// here with zero requests made, as is a plan from a client with no install id; every request carries
/// `x-scenic-device`, the install id lowercased, and no other identifying header (T-0260). Every reply - and
/// the absence of one - is a `PlanResponse` or a `PlanError` by the R6 table in `PlanResponseReader`.
public struct PlanClient: Sendable {
    public let base: URL
    let transport: any PlanTransport
    let installID: (any InstallIDProvider)?

    /// `installID` has no default: a client without one must say so (`nil`), and every plan it makes is then
    /// refused on the device as `.noInstallID` (T-0260 R3).
    public init(base: URL, transport: any PlanTransport, installID: (any InstallIDProvider)?) {
        self.base = base
        self.transport = transport
        self.installID = installID
    }

    /// Plans `origin` -> the corpus place `place` with `budgetMinutes` of extra time.
    public func plan(from origin: Coordinate, to place: Int64, budgetMinutes: Int,
                     departsAt: Date? = nil, vehicle: VehicleProfile = .standard)
        async throws(PlanError) -> PlanResponse {
        // No install id, no request: without x-scenic-device the Worker bills the shared unidentified bucket.
        guard let installID else { throw .refusedOnDevice(.noInstallID) }
        let body: PlanRequestBody
        switch PlanRequestBody.validated(origin: origin, place: place, budgetMinutes: budgetMinutes,
                                         departsAt: departsAt) {
        case .failure(let refusal):
            throw .refusedOnDevice(refusal)
        case .success(let validated):
            body = validated
        }
        let encoder = JSONEncoder()
        encoder.outputFormatting = [.sortedKeys]
        // Only a non-finite Double can make this encoder throw, and validated() refused those as out of range.
        guard let bytes = try? encoder.encode(body) else { throw .refusedOnDevice(.originOutOfRange) }

        let request = PlanHTTPRequest(url: base.appendingPathComponent("plan"), method: "POST",
                                      headers: ["content-type": "application/json",
                                                "x-scenic-device": installID.installID().uuidString.lowercased()],
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
