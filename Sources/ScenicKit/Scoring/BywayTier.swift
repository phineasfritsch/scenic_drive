import Foundation

/// How a way is designated as a scenic byway. **Three states, not two.**
///
/// This was a `Bool` until T-0154, and the Bool was wrong rather than merely coarse. Caltrans publishes two
/// statuses - *officially designated* and *eligible* - and the ETL has paid them different bonuses since
/// T-0028 (six review rounds): `services/etl/etl/byways.py:100` `DESIGNATED_BONUS = 0.15` and `:105`
/// `ELIGIBLE_BONUS = 0.06`. ScenicKit's single Bool paid 0.15 for both, so **every eligible byway in the
/// corpus scored 0.09 too high on E** here while the ETL scored it correctly - five orders of magnitude past
/// the 1e-6 the plan allows between the two (plan:219). The shared fixture put 240 of its 1,000 rows on that
/// difference before this type existed.
///
/// The tiers carry no numbers of their own. `SegmentScore.bonus(for:)` is the single place a tier becomes a
/// number, so the constants stay where the other thirteen weights are and a mutation on one of them has one
/// place to bite.
///
/// The fixture's own vocabulary (`"none"`, `"eligible"`, `"designated"`) is deliberately neither this enum's
/// spelling nor Caltrans's `OD`/`E` codes: each side translates at its own boundary, so neither side's
/// spelling can quietly become the contract.
public enum BywayTier: String, CaseIterable, Sendable {
    /// Not a byway, or a corridor whose status the source does not recognise. An unknown status scores
    /// nothing rather than guessing - the same rule `byways.status_bonus` follows.
    case none
    /// Caltrans *eligible*: the corridor meets the criteria and carries no official designation.
    case eligible
    /// Officially designated, by FHWA or Caltrans.
    case designated
}
