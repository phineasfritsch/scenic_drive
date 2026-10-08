/// The corridor cell a learned ratio is kept for: an H3 resolution-8 index as uber/h3 spells it (T-0320 R1).
/// ScenicKit neither computes nor validates H3 - it may not import Telemetry, whose builder makes resolution-5 cells
/// only - so the caller that holds the drive's coordinates hands the index in, and the learner treats it as opaque.
public struct CorridorCell: Hashable, Sendable {
    public let index: UInt64

    public init(index: UInt64) {
        self.index = index
    }
}
