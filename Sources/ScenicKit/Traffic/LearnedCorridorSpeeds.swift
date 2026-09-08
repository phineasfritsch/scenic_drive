import Foundation

/// What this driver's corridors actually do, learned on the device from their own completed drives.
///
/// ## Why this exists
///
/// The plan's second-highest risk is *"rush-hour ETA over-promises - High likelihood, trust blast radius."*
/// We have no traffic feed at launch: the router knows free-flow speeds and nothing about Tuesday at 17:40.
/// Telling a user their scenic drive home takes 34 minutes when it takes 51 is the kind of wrong that ends
/// the relationship, and it would happen on the commute - the exact drive the product is for.
///
/// So the ratio of actual to free-flow duration is learned per corridor per hour-of-week, from drives the
/// user has already completed, with an EWMA so recent weeks matter more than old ones.
///
/// ## Two rules that are product invariants, not implementation details
///
/// **Until a corridor has `confidenceThreshold` samples, we do not claim to know.** CLAUDE.md: *"ETAs show
/// the estimate - no traffic data badge until a corridor has >= 5 learned samples."* `ratio(for:)` returns
/// nil below that, and nil means "show the badge", not "assume 1.0". Returning 1.0 would be an unbadged
/// free-flow ETA presented as a learned one - the over-promise this whole type exists to prevent, wearing
/// the costume of the fix.
///
/// **Nothing here is `Codable`, on purpose.** P-PRIV-05: *"learned speeds have no Codable conformance"*.
/// This is a record of when and where one person drives, at hour-of-week granularity - a commute pattern.
/// It never leaves the device. Conformance is the mechanism by which that leaks: one `JSONEncoder` in a
/// diagnostics payload, one `Codable` request body that happens to include a field of this type, and the
/// pattern is on a server. Persistence is deliberately explicit SQL in `PlaceStore`, written and reviewed as
/// its own thing, rather than something a synthesised conformance does for free. The test suite asserts the
/// absence of conformance at runtime, because the absence of a protocol is not something a compiler warns
/// about when somebody adds it later.
public struct LearnedCorridorSpeeds: Sendable {
    /// Samples required before a corridor's ratio is trusted enough to drop the badge.
    public static let confidenceThreshold = 5

    /// EWMA weight for the newest sample. 0.3 keeps roughly the last handful of drives dominant while a
    /// single unusual Tuesday - a crash, a ballgame - cannot move the estimate far on its own.
    public static let smoothing = 0.3

    // The stored ratio is FREE-FLOW OVER ACTUAL, so 1.0 means "moving at free-flow" and lower means slower.
    // Both comments below were transposed in the first version - each described the other constant - and a
    // reviewer noticed that the one with no real test was also the one whose comment pointed at the wrong
    // identifier. Those two facts are not a coincidence: a comment nothing checks is a comment nobody reads
    // against the code.

    /// Below this the corridor is not congested, it is closed: a third of free-flow on a road the router
    /// thinks runs at 60 km/h is 20 km/h sustained over the whole corridor. Clamped rather than rejected,
    /// because a genuinely terrible Tuesday is real data and should count.
    public static let minRatio = 0.3

    /// Nothing is faster than free-flow. The router's free-flow speed is already the legal limit, so a
    /// sample above 1.0 is measuring something other than traffic - a GPS glitch, or a drive that skipped
    /// part of the corridor.
    ///
    /// Untested, this constant is the over-promise reached from the other side. A reviewer mutated it to
    /// 3.0 and the whole suite stayed green, after which five fast drives gave `adjust(1800)` a duration of
    /// 600 s with `learned == true` - an ETA BELOW the free-flow it was handed, badge off. The guard that
    /// was supposed to prevent that read `#expect(r2 <= LearnedCorridorSpeeds.maxRatio)`, which is true for
    /// any value the constant takes.
    public static let maxRatio = 1.0

    private var ratios: [CorridorKey: Double] = [:]
    private var counts: [CorridorKey: Int] = [:]

    public init() {}

    /// Record one completed drive through a corridor.
    ///
    /// `actual` and `freeFlow` are seconds. Returns false and records nothing if the sample is not usable -
    /// silently absorbing a bad sample is how a learned model drifts without anybody noticing.
    @discardableResult
    public mutating func record(_ key: CorridorKey, actual: TimeInterval,
                                freeFlow: TimeInterval) -> Bool {
        guard actual.isFinite, freeFlow.isFinite, actual > 0, freeFlow > 0 else { return false }
        // The ratio stored is free-flow over actual, so 1.0 is "moving at free-flow" and lower is slower.
        // Clamped rather than rejected: a genuinely terrible Tuesday is real data and should count, it just
        // must not drag the estimate somewhere the model cannot represent.
        let raw = freeFlow / actual
        guard raw.isFinite else { return false }
        let sample = min(Self.maxRatio, max(Self.minRatio, raw))

        let n = counts[key] ?? 0
        if n == 0 {
            ratios[key] = sample
        } else {
            ratios[key] = Self.smoothing * sample + (1 - Self.smoothing) * (ratios[key] ?? sample)
        }
        counts[key] = n + 1
        return true
    }

    /// How many drives have been recorded for this corridor and hour.
    public func sampleCount(for key: CorridorKey) -> Int { counts[key] ?? 0 }

    /// True once there is enough history to stop showing the *estimate - no traffic data* badge.
    public func isConfident(about key: CorridorKey) -> Bool {
        sampleCount(for: key) >= Self.confidenceThreshold
    }

    /// The learned free-flow-to-actual ratio, or nil when we do not yet know.
    ///
    /// **nil means show the badge.** It does not mean 1.0. A caller that substitutes 1.0 has re-created the
    /// unbadged free-flow ETA this type exists to replace.
    public func ratio(for key: CorridorKey) -> Double? {
        guard isConfident(about: key), let r = ratios[key] else { return nil }
        return r
    }

    /// Adjust a free-flow duration by what we have learned, or return it unchanged with `learned == false`.
    ///
    /// Returning the pair rather than just a number is the point: every call site is forced to handle the
    /// unlearned case, because the badge is driven by the same value the ETA is.
    public func adjust(_ freeFlow: TimeInterval, for key: CorridorKey) -> (duration: TimeInterval,
                                                                          learned: Bool) {
        guard freeFlow.isFinite, freeFlow > 0, let r = ratio(for: key) else { return (freeFlow, false) }
        return (freeFlow / r, true)
    }
}
