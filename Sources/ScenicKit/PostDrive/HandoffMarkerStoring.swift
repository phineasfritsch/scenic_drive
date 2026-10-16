import Foundation

/// Where the handoff marker lives (T-0366 R1): one Int, the opens left to ask at. No place, no time, no route.
public protocol HandoffMarkerStoring: Sendable {
    func opensLeft() -> Int
    func setOpensLeft(_ value: Int)
}
