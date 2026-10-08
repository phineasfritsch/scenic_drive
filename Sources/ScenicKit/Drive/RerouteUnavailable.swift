import Foundation

/// The reroute sender while /plan carries neither pins nor lambda (T-0321 R3): it fails at once and makes no
/// request, so an online off-route drive is rejoin mode with zero requests, exactly as offline. T-0319 replaces it.
public struct RerouteUnavailable: RerouteSending, Error, Equatable {
    public init() {}

    public func reroute(_ request: RerouteRequest) async throws -> RerouteReply {
        throw self
    }
}
