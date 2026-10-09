import Foundation
import ScenicKit

/// The plan sheet's production planner (T-0294 R1): one ticket, one `PlanClient.plan` call, one `PlanOutcome`.
///
/// It sends exactly what the ticket carries - the start at 2 dp, the destination's place id, the budget - and
/// nothing else; a reply is a `PlanPreview`, a failure is `PlanError.failure`. It never plans without a ticket,
/// and only `PlanSheet.startPlanning()` issues one (P-SAFE-03).
public struct ClientPlanner: RoutePlanning {
    public let client: PlanClient

    public init(client: PlanClient) {
        self.client = client
    }

    public func plan(_ ticket: PlanTicket) async -> PlanOutcome {
        do {
            let response = try await client.plan(from: ticket.origin, to: ticket.place,
                                                 budgetMinutes: ticket.budgetMinutes, allBackRoads: ticket.allBackRoads)
            return .preview(Self.preview(of: response, place: ticket.place, budgetMinutes: ticket.budgetMinutes))
        } catch {
            if case .nothingPretty(let offer) = error { return Self.offered(offer, budgetMinutes: ticket.budgetMinutes) }
            return .failure(error.failure)
        }
    }

    /// T-0334 R4: the sheet's view of a 422 nothing_pretty - only when it echoes THIS ticket's budget and every
    /// minute is whole; any other offer is not this plan's answer, so it is `unexpectedResponse`.
    public static func offered(_ offer: NothingPrettyOffer, budgetMinutes: Int) -> PlanOutcome {
        guard offer.budgetMinutes == Double(budgetMinutes) else { return .failure(.unexpectedResponse) }
        let more = offer.moreTimeMinutes.map { Int(exactly: $0) }
        let minutes = offer.backRoadsBudgetMinutes.map { Int(exactly: $0) }
        if more == .some(nil) || minutes == .some(nil) { return .failure(.unexpectedResponse) }
        return .offered(PlanOffer(budgetMinutes: budgetMinutes, moreTimeMinutes: more ?? nil,
                                  backRoadsEtaSeconds: offer.backRoadsEtaSeconds, backRoadsBudgetMinutes: minutes ?? nil))
    }

    /// The preview's view of a Worker 200: the line, both ETAs, the estimate flag and every hazard run, in order, and
    /// (T-0328 R1) the plan's continuation - its token with the ticket's place and budget - exactly when it has one.
    public static func preview(of response: PlanResponse, place: Int64, budgetMinutes: Int) -> PlanPreview {
        PlanPreview(route: response.route, etaSeconds: response.etaSeconds,
                    fastestEtaSeconds: response.fastestEtaSeconds, etaIsEstimate: response.etaIsEstimate,
                    hazards: response.hazards.map {
                        PlanHazardRun(kind: $0.kind, value: $0.value, fromIndex: $0.fromIndex, toIndex: $0.toIndex)
                    }, waypoints: response.waypoints, lambda: response.lambda,
                    continuation: response.planToken.map {
                        PlanContinuation(token: $0, place: place, budgetMinutes: budgetMinutes)
                    })
    }
}
