/// One row of the user store's corridor_ratio table (T-0343 R3): a learned corridor slot - the H3-8 cell's index,
/// the hour of the week, the ratio and its samples - kept across launches. On the device only: no Codable
/// conformance, no path to the API client or telemetry (P-PRIV-05).
public struct CorridorRatioRecord: Sendable, Equatable {
    public let cell: UInt64
    public let hour: Int
    public let ratio: Double
    public let samples: Int

    public init(cell: UInt64, hour: Int, ratio: Double, samples: Int) {
        self.cell = cell
        self.hour = hour
        self.ratio = ratio
        self.samples = samples
    }
}
