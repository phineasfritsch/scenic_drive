import Foundation

/// The per-way score a surface may show: the plan's formula under the router's class ceiling (T-0218 R1).
///
/// The ETL quantises `min(score.score(...), CLASS_SCORE_CEILING[highway])` onto the way
/// (`services/etl/etl/assemble.py`, `scored_row`), so the router bands a hillside residential street at 6
/// however pretty its terms are. `SegmentScore.score(for:)` is the formula alone - it is held to the
/// 1000-row oracle and to `score.score`, which are pre-ceiling by T-0207 R1 - so a surface that showed it
/// would show 0.80 for a way the router uses as a 6. This type is the one place the device applies the same
/// ceiling, and every caller of the formula outside it is whitelisted by name in `SegmentScoreSurfaceTests`.
///
/// `byClass` is bound to the ETL table by `SegmentScoreCeilingTests`, which parses the one
/// `CLASS_SCORE_CEILING = {...}` line of assemble.py and requires whole-table equality: the same class
/// strings, matched exactly as Python's `dict.get` matches them, and the same numbers. Motorway and trunk
/// are not here: they score 0 in the formula itself and are penalised, never gated.
public enum SegmentScoreCeiling {

    /// assemble.py's `CLASS_SCORE_CEILING`. 0.6499 is the largest four-decimal unit the quantiser sends
    /// below the band of 7; a service way is not a drive and carries 0.
    public static let byClass: [String: Double] = ["residential": 0.6499, "living_street": 0.6499, "service": 0.0]

    /// The formula's score capped by the class ceiling, or nil when `SegmentScore` refuses the terms - never
    /// the ceiling in place of a refusal.
    public static func score(for t: SegmentTerms) -> Double? {
        guard let formula = SegmentScore.score(for: t) else { return nil }
        guard let ceiling = byClass[t.highway] else { return formula }
        return min(formula, ceiling)
    }
}
