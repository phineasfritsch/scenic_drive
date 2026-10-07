/// A planned route as the preview shows it (T-0294 R6): the line, the ETA against the fastest route's, whether the
/// ETA is an estimate, and the hazard runs. Built from the Worker's 200 by ScenicAPIClient's `ClientPlanner`.
public struct PlanPreview: Equatable, Sendable {
    /// The preview's footer text. The route is drawn from OpenStreetMap ways the router returned, so the preview
    /// credits them at every detent (P-ATTR-01). It lives here because apps/ios may hold one OpenStreetMap literal.
    public static let attribution = "Route data © OpenStreetMap contributors"
    /// CLAUDE.md: shown until a corridor has 5 learned samples. The device keeps none yet, and the server always
    /// sends `eta_is_estimate: true`, so today it is always shown (R6).
    public static let estimateBadge = "estimate · no traffic data"
    /// CLAUDE.md: the safety disclaimer stays visible on the route screen - its persistent line, on the preview.
    public static let conditions = "Conditions change. Verify locally."

    public let route: [Coordinate]
    public let etaSeconds: Double
    public let fastestEtaSeconds: Double
    public let etaIsEstimate: Bool
    public let hazards: [PlanHazardRun]

    public init(route: [Coordinate], etaSeconds: Double, fastestEtaSeconds: Double, etaIsEstimate: Bool,
                hazards: [PlanHazardRun]) {
        self.route = route
        self.etaSeconds = etaSeconds
        self.fastestEtaSeconds = fastestEtaSeconds
        self.etaIsEstimate = etaIsEstimate
        self.hazards = hazards
    }

    /// Whether the badge is drawn: whenever the ETA is an estimate.
    public var showsEstimateBadge: Bool { etaIsEstimate }

    /// The drive's minutes, to the nearest minute.
    public var etaMinutes: Int { Int((etaSeconds / 60).rounded()) }

    /// Minutes beyond the fastest route, to the nearest minute, never below zero.
    public var extraMinutes: Int { max(0, Int(((etaSeconds - fastestEtaSeconds) / 60).rounded())) }

    /// "52 min · 14 min longer than the fastest way", or "· about as quick as the fastest way" when it is not longer.
    public var etaLine: String {
        let extra = extraMinutes
        return extra == 0
            ? "\(etaMinutes) min · about as quick as the fastest way"
            : "\(etaMinutes) min · \(extra) min longer than the fastest way"
    }
}
