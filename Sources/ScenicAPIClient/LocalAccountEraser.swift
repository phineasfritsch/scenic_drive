import Foundation

/// The device's side of a confirmed deletion (T-0356 R3): erases one stored item. Production's is PlanAdapter
/// `DeviceAccountEraser`; `AccountDeletion` decides which items, and calls it for nothing else.
public protocol LocalAccountEraser: Sendable {
    func erase(_ item: LocalAccountItem) async
}
