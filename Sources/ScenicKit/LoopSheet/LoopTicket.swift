/// One loop request the sheet issued (T-0314 R1): the ONE coordinate it sends, already at 2 dp (P-PRIV-05), and the
/// minutes on the dial. Only LoopSheet makes one.
public struct LoopTicket: Equatable, Sendable {
    public let serial: Int
    public let start: Coordinate
    public let minutes: Int

    init(serial: Int, start: Coordinate, minutes: Int) {
        self.serial = serial
        self.start = start
        self.minutes = minutes
    }
}
