import Foundation

/// What DriveController tells NavAdapter to do with the network (T-0321 R2). The adapter acts on these and nothing
/// else: it never decides when to ask, and it hands each answer back with the ticket it was sent under.
public enum DriveCommand: Sendable, Equatable {
    /// Ask for this reroute; the reply or failure comes back under `ticket`.
    case send(RerouteRequest, ticket: Int)
    /// The reroute under `ticket` is lost (the connection dropped): stop it; its reply or failure, if one still
    /// lands, is dropped by DriveController.
    case cancel(ticket: Int)
}
