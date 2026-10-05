import Foundation
import ScenicKit

/// The app's client for the Worker's POST /plan (T-0251). One call, one request, one typed outcome.
///
/// The request carries ONE coordinate, already at 2 dp, and a corpus place id (R3); anything else is refused
/// here with zero requests made. Every reply - and the absence of one - is a `PlanResponse` or a `PlanError`
/// by the R6 table in `PlanResponseReader`.
public struct PlanClient: Sendable {
    public let base: URL
    let transport: any PlanTransport

    public init(base: URL, transport: any PlanTransport) {
        self.base = base
        self.transport = transport
    }

    /// Plans `origin` -> the corpus place `place` with `budgetMinutes` of extra time.
    public func plan(from origin: Coordinate, to place: Int64, budgetMinutes: Int,
                     departsAt: Date? = nil) async throws(PlanError) -> PlanResponse {
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
                                      headers: ["content-type": "application/json"], body: bytes)
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
