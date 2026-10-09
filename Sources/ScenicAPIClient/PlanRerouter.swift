import Foundation
import ScenicKit

/// The reroute sender NavAdapter is handed (T-0328 R2): DriveSession's RerouteRequest through `PlanClient.reroute`.
///
/// A request with no plan token is refused here with ZERO requests - the Worker remembered nothing, and a fresh
/// origin-to-place plan is not the rest of THIS drive (R5) - so DriveController hears a failure and the drive rejoins,
/// exactly as offline. Otherwise ONE request: the origin rounded to 2 dp by PlanClient, the place and budget the plan
/// was asked with, and {token, first_pin}. The 200 becomes the RerouteReply DriveController hands the session.
public struct PlanRerouter: RerouteSending {
    public let client: PlanClient
    public let place: Int64
    public let budgetMinutes: Int

    public init(client: PlanClient, place: Int64, budgetMinutes: Int) {
        self.client = client
        self.place = place
        self.budgetMinutes = budgetMinutes
    }

    public func reroute(_ request: RerouteRequest) async throws -> RerouteReply {
        guard let token = request.planToken else { throw RerouteUnavailable() }
        let response = try await client.reroute(request, token: token, place: place, budgetMinutes: budgetMinutes)
        return Self.reply(of: response)
    }

    /// The Worker's answer as DriveController.rerouteArrived takes it: its line, its pins and its own token.
    public static func reply(of response: PlanResponse) -> RerouteReply {
        RerouteReply(line: response.route, waypoints: response.waypoints, planToken: response.planToken)
    }
}
