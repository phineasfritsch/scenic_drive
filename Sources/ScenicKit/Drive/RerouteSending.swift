import Foundation

/// How a reroute travels (T-0321 R3). The Worker's wire is T-0319's; until it lands the app sends through
/// RerouteUnavailable, which asks nothing.
public protocol RerouteSending: Sendable {
    func reroute(_ request: RerouteRequest) async throws -> RerouteReply
}
