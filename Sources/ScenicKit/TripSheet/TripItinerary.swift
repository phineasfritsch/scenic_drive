/// A planned road trip as the sheet shows it (T-0313 R5): preview or full, the whole ETA against the fastest, the
/// estimate flag (CLAUDE.md: the badge stays until a corridor has learned samples), and the days in order.
public struct TripItinerary: Equatable, Sendable {
    public let isFull: Bool
    public let etaSeconds: Double
    public let fastestEtaSeconds: Double
    public let etaIsEstimate: Bool
    public let days: [TripItineraryDay]
    /// T-0341 R1: what the answer said about road closures; the itinerary card reads its lines.
    public let closures: ClosuresHazard

    public init(isFull: Bool, etaSeconds: Double, fastestEtaSeconds: Double, etaIsEstimate: Bool,
                days: [TripItineraryDay], closures: ClosuresHazard = .clear) {
        self.closures = closures
        self.isFull = isFull
        self.etaSeconds = etaSeconds
        self.fastestEtaSeconds = fastestEtaSeconds
        self.etaIsEstimate = etaIsEstimate
        self.days = days
    }
}
