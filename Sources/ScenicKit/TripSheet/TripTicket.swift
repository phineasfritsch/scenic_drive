/// One road-trip request the sheet issued (T-0313 R1): the ONE coordinate it sends, already at 2 dp
/// (P-PRIV-05), the destination's corpus place id, the days and the extra-time percent. Only TripSheet makes one.
public struct TripTicket: Equatable, Sendable {
    public let serial: Int
    public let origin: Coordinate
    public let place: Int64
    public let days: Int
    public let extraBudgetPercent: Int

    init(serial: Int, origin: Coordinate, place: Int64, days: Int, extraBudgetPercent: Int) {
        self.serial = serial
        self.origin = origin
        self.place = place
        self.days = days
        self.extraBudgetPercent = extraBudgetPercent
    }
}
