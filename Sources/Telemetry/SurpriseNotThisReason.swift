import Foundation

/// Why a surprise was turned down - the `reason` of `surprise_not_this`. A closed list with no "other, tell
/// us" case: a typed answer would be the free-form string P-PRIV-05 forbids.
public enum SurpriseNotThisReason: String, CaseIterable, Sendable {
    case tooFar = "too_far"
    case beenThere = "been_there"
    case notMyThing = "not_my_thing"
}
