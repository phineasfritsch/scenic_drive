import Foundation
import Testing
@testable import Telemetry

/// The `pct` of drive_completed and drive_abandoned: a WHOLE percent, floored, clamped into 0...100.
@Suite("CompletionPercent") struct CompletionPercentTests {
    static let table: [(fraction: Double, value: Int)] = [
        (0.0, 0), (0.375, 37), (0.987, 98), (0.999, 99), (1.0, 100), (1.5, 100), (-0.2, 0),
        (.nan, 0), (.infinity, 0), (-.infinity, 0),
    ]

    @Test("a fraction floors to a whole percent clamped into 0...100")
    func floorsAndClamps() {
        #expect(Self.table.map { CompletionPercent(fraction: $0.fraction).value } == Self.table.map(\.value))
    }
}
