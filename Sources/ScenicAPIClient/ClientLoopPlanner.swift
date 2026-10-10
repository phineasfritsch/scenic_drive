import Foundation
import ScenicKit

/// The live loop planner (T-0314 R3, R6): one LoopClient call per ticket, the answer turned into the preview the sheet
/// shows - after the DEVICE's own retrace check on the returned path. A path RetraceDetector cannot measure, or finds
/// retracing more than maxRetraceFraction, is not shown: noCleanLoop.
public struct ClientLoopPlanner: LoopPlanning {
    public let client: LoopClient

    public init(client: LoopClient) {
        self.client = client
    }

    public func plan(_ ticket: LoopTicket) async -> LoopOutcome {
        do {
            return Self.outcome(of: try await client.loop(from: ticket.start, minutes: ticket.minutes))
        } catch {
            return .failure(error.failure)
        }
    }

    public static func outcome(of response: LoopResponse) -> LoopOutcome {
        outcome(of: response, fraction: RetraceDetector.retraceFraction(response.route))
    }

    /// The decision on a measured fraction (rv1-t0314 B1): no route fixture lands on 0.15, so the bound is reachable
    /// only here, and the comparison is RetraceDetector's own witnessed `isAcceptable(fraction:)`, never a copy.
    public static func outcome(of response: LoopResponse, fraction measured: Double?) -> LoopOutcome {
        guard let fraction = measured,
              RetraceDetector.isAcceptable(fraction: fraction) else { return .failure(.noCleanLoop) }
        return .preview(LoopPreview(path: response.route, waypoints: response.waypoints,
                                    durationSeconds: response.durationSeconds,
                                    distanceMeters: response.distanceMeters, retraceFraction: fraction,
                                    etaIsEstimate: response.etaIsEstimate, closures: response.closuresHazard,
                                    hazards: response.hazards.map(ClientPlanner.run)))
    }
}
