/// One learned slot as plain values, the shape the device's store keeps across launches (T-0343 R2): the H3-8
/// cell's index, the hour of the week, the ratio and its samples. PlaceStore cannot name CorridorSlot, so the app
/// carries these between the two. On the device only - no Codable conformance (P-PRIV-05).
public struct CorridorSlotRow: Equatable, Sendable {
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
