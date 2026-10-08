/// Where one learned ratio is kept: a corridor cell at one hour of the week. On the device only (P-PRIV-05).
public struct CorridorSlot: Hashable, Sendable {
    public let cell: CorridorCell
    public let hour: HourOfWeek

    public init(cell: CorridorCell, hour: HourOfWeek) {
        self.cell = cell
        self.hour = hour
    }
}
