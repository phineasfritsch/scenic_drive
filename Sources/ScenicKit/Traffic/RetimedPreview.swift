import Foundation

/// The preview's ETA and its estimate badge, from the device's traffic provider (T-0325 R4, P-SAFE-07).
///
/// The Worker always answers `eta_is_estimate: true` - learned speeds never leave the device - so only this can
/// clear the badge, and only when every corridor edge of the drawn route is learned. A preview without usable
/// time runs keeps the server's ETA and its badge: it fails toward saying less.
public enum RetimedPreview {
    /// `preview` with etaSeconds and etaIsEstimate from `provider`'s retime of the route's corridor edges departing
    /// at `departsAt`, every other field unchanged; `preview` itself when the runs do not make a CorridorRoute of
    /// its drawn line.
    public static func of(_ preview: PlanPreview, timeRuns: [CorridorTimeRun], by provider: some TrafficProvider,
                          departsAt: Date) -> PlanPreview {
        guard let route = CorridorRoute(route: preview.route, timeRuns: timeRuns) else { return preview }
        let retimed = provider.retime(route.edges, departsAt: departsAt)
        return PlanPreview(route: preview.route, etaSeconds: retimed.etaSeconds,
                           fastestEtaSeconds: preview.fastestEtaSeconds, etaIsEstimate: retimed.isEstimate,
                           hazards: preview.hazards, waypoints: preview.waypoints, lambda: preview.lambda,
                           continuation: preview.continuation)
    }
}
