import Foundation

/// How much of a drive was driven, as a WHOLE percent 0...100 - the `pct` of `drive_completed` and
/// `drive_abandoned`. Whole and clamped so the value says how far, never where: a fraction of a route carried
/// to many decimals would locate the stop along a route the server could reconstruct.
public struct CompletionPercent: Equatable, Sendable {
    public let value: Int

    /// The fraction driven (1.0 = the whole route), floored to a whole percent and clamped into 0...100.
    /// A non-finite fraction is 0.
    public init(fraction: Double) {
        guard fraction.isFinite else {
            value = 0
            return
        }
        let percent = (fraction * 100).rounded(.down)
        value = Int(Swift.min(100, Swift.max(0, percent)))
    }
}
