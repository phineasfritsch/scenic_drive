import Foundation
import ScenicKit

/// The app's client for the Worker's POST /plan (T-0251). One call, one request, one typed outcome.
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
        throw .unexpectedResponse(status: -1)
    }
}
