/// One slot's learned speed ratio (actual speed / free-flow speed, in [0.3, 1.0]) and how many drives taught it.
/// On the device only (P-PRIV-05).
public struct CorridorRatio: Equatable, Sendable {
    public let ratio: Double
    public let samples: Int

    public init(ratio: Double, samples: Int) {
        self.ratio = ratio
        self.samples = samples
    }
}
