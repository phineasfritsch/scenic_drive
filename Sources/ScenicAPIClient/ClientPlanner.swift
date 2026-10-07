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
                                                 budgetMinutes: ticket.budgetMinutes)
            return .preview(Self.preview(of: response))
        } catch {
            return .failure(error.failure)
        }
    }

    /// The preview's view of a Worker 200: the line, both ETAs, the estimate flag and every hazard run, in order.
    public static func preview(of response: PlanResponse) -> PlanPreview {
        PlanPreview(route: response.route, etaSeconds: response.etaSeconds,
                    fastestEtaSeconds: response.fastestEtaSeconds, etaIsEstimate: response.etaIsEstimate,
                    hazards: response.hazards.map {
                        PlanHazardRun(kind: $0.kind, value: $0.value, fromIndex: $0.fromIndex, toIndex: $0.toIndex)
                    }, waypoints: response.waypoints, lambda: response.lambda)
    }
}
