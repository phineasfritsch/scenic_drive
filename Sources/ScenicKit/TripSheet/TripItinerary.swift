/// A planned road trip as the sheet shows it (T-0313 R5): preview or full, the whole ETA against the fastest, the
/// estimate flag (CLAUDE.md: the badge stays until a corridor has learned samples), and the days in order.
public struct TripItinerary: Equatable, Sendable {
    public let isFull: Bool
    public let etaSeconds: Double
    public let fastestEtaSeconds: Double
    public let etaIsEstimate: Bool
    public let days: [TripItineraryDay]

    public init(isFull: Bool, etaSeconds: Double, fastestEtaSeconds: Double, etaIsEstimate: Bool,
                days: [TripItineraryDay]) {
        self.isFull = isFull
        self.etaSeconds = etaSeconds
        self.fastestEtaSeconds = fastestEtaSeconds
        self.etaIsEstimate = etaIsEstimate
        self.days = days
    }
}
