import Foundation

/// DriveSession plus the reroute in flight, by ticket (T-0321 R2; rv2-t0317's recordable 4).
///
/// NavAdapter forwards every fix to `observe(_:)` and every reachability report to `connectivity(online:)`, does
/// what the returned commands say, and hands each reroute's reply or failure back with the ticket it was sent
/// under. Losing the connection while a reroute is out cancels that ticket; an answer under any ticket but the one
/// in flight is dropped. Without the ticket, a reply sent before a drop would land after the reconnect's request
/// and answer it - DriveSession alone cannot tell the two apart.
public struct DriveController: Sendable, Equatable {
    public private(set) var session: DriveSession
    /// The ticket of the reroute that is out, or nil.
    public private(set) var inFlight: Int?
    private var lastTicket = 0

    public init(session: DriveSession) {
        self.session = session
    }

    /// One location fix, forwarded whole to the session.
    public mutating func observe(_ fix: DriveFix) -> [DriveCommand] {
        guard let request = session.observe(fix) else { return [] }
        return [issue(request)]
    }

    /// A reachability report. The drop with a reroute out cancels it before the session hears the edge.
    public mutating func connectivity(online: Bool) -> [DriveCommand] {
        var commands: [DriveCommand] = []
        if !online, let lost = inFlight {
            inFlight = nil
            commands.append(.cancel(ticket: lost))
        }
        if let request = session.connectivity(online: online) { commands.append(issue(request)) }
        return commands
    }

    /// The reroute under `ticket` landed. Dropped (false, nothing changes) unless `ticket` is the one in flight.
    @discardableResult
    public mutating func rerouteArrived(ticket: Int, reply: RerouteReply) -> Bool {
        guard ticket == inFlight else { return false }
        inFlight = nil
        return session.rerouteArrived(line: reply.line, waypoints: reply.waypoints, planToken: reply.planToken)
    }

    /// The reroute under `ticket` failed. Dropped (false, nothing changes) unless `ticket` is the one in flight.
    @discardableResult
    public mutating func rerouteFailed(ticket: Int) -> Bool {
        guard ticket == inFlight else { return false }
        inFlight = nil
        session.rerouteFailed()
        return true
    }

    private mutating func issue(_ request: RerouteRequest) -> DriveCommand {
        lastTicket += 1
        inFlight = lastTicket
        return .send(request, ticket: lastTicket)
    }
}
