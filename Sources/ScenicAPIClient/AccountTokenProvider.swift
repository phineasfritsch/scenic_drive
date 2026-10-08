import Foundation

/// Where the paid-tier purchase id comes from (T-0315 R3): the appAccountToken of this Apple ID's most recent
/// subscription purchase, live or not, or nil when it never bought one. The Worker decides the tier from it (T-0272
/// R1-R3); a client never guesses one. Production's provider is PlanAdapter's `StoreKitAccountToken`; nothing that
/// conforms may log the value - it is a bearer secret until the session JWT carries it (T-0272 R5).
public protocol AccountTokenProvider: Sendable {
    func accountToken() async -> UUID?
}
