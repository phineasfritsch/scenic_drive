/// One plan the sheet let through its gate (T-0294 R2): the request's three inputs and the serial that ties the
/// reply back to it. Only `PlanSheet.startPlanning()` makes one, so no ticket exists that the gate did not issue.
public struct PlanTicket: Equatable, Sendable {
    public let serial: Int
    /// The start's coordinate, already at 2 decimal places (R4).
    public let origin: Coordinate
    /// The destination's corpus `place_id`.
    public let place: Int64
    public let budgetMinutes: Int

    init(serial: Int, origin: Coordinate, place: Int64, budgetMinutes: Int) {
        self.serial = serial
        self.origin = origin
        self.place = place
        self.budgetMinutes = budgetMinutes
    }
}
