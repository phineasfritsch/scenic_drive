import Foundation

/// A way's OSM tags, readable **only** on the keys a gate rule is written on.
///
/// ## Why this is a type and not a filtered dictionary
///
/// `Gates.decide` used to take the raw dictionary and narrow it on its first line:
///
/// ```swift
/// public static func decide(_ allTags: [String: String]) -> GateDecision {
///     let tags = allTags.filter { consideredTagKeys.contains($0.key) }
/// ```
///
/// Reviews of PR #82 then refused freeway geometry eleven times with the whole suite green, and the
/// fourth review showed why the filter above could never stop them: `allTags` is the function's own
/// parameter and stays in scope for the entire body, so a rule could read it by typing one extra
/// identifier. Worse, the filter was the *first* statement, so any branch added at the top of the function
/// **had** to read `allTags` - `tags` did not exist yet there. The narrowing was a naming convention.
///
/// This type moves the narrowing from a statement that runs once to the accessor that every rule goes
/// through. There is no filter line to delete and no second dictionary to reach for, because
/// `Gates.verdict` never receives the raw tags at all: they are captured here, behind a `private` stored
/// property, and the only way out a rule can NAME is the subscript below.
///
/// ## What that closes, and what it does not
///
/// **Closed against the three routes that were live - an enumeration, not a proof.** A rule in
/// `Gates.verdict` cannot read a key outside `Gates.consideredTagKeys` by naming another identifier, by
/// looping over a list of keys, or by deleting one line. Each of those was a live survivor against the
/// previous shape; each is now either `nil` at the read or a compile error.
///
/// **Reflection is NOT closed, and the sixth review of PR #82 measured it rather than arguing about it.**
/// `if let raw = Mirror(reflecting: tags).children.first?.value as? [String: String],
/// raw["destination"] != nil { return .refused(.noAccess) }` inside `verdict` **compiles** and reads the
/// `private` property below, and it really does refuse every signed ramp - the control went red. It was
/// caught, but by `irrelevantTagKeysCannotChangeADecision`, i.e. by behaviour and not by this type. So the
/// sentence above lists the routes a rule realistically takes; it is not a statement about all of them,
/// and an earlier wording that read "Closed." flat was claiming more than the type delivers.
///
/// **Not closed, and no type can close it.** A key that IS in `consideredTagKeys` reads through by design -
/// that is what "considered" means - so a refusal keyed on, say, `motor_vehicle` having any value but `yes`
/// is unaffected by everything above. Only behaviour pins that rule out, and
/// `freewayValuesOfConsideredKeysAreAllowed` is the one that does.
///
/// **Also not closed:** `Gates.decide` itself still has the raw dictionary in scope, because Swift gives a
/// function no way to drop its own parameter. Its body is one expression with no rule in it, and the
/// corpus in `ops/mutate/gates_corpus.py` puts eleven mutations there precisely so the gap is measured on
/// every run rather than argued about.
struct ConsideredTags {
    /// The raw tags. `private` is the whole point: `Gates.verdict` holds a `ConsideredTags`, not a
    /// dictionary, so this is unreachable from any rule.
    private let raw: [String: String]

    init(_ raw: [String: String]) {
        self.raw = raw
    }

    /// The value of `key`, or `nil` when no gate rule is written on that key.
    ///
    /// The check is **per read**, deliberately. A one-time `filter` in the initialiser would behave
    /// identically today and would put back the single line whose deletion revived four refusals in
    /// review; this cannot be switched off for one caller, because there is only one path to the data.
    subscript(key: String) -> String? {
        return Gates.consideredTagKeys.contains(key) ? raw[key] : nil
    }
}
