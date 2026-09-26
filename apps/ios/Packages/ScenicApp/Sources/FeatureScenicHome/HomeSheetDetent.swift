import Foundation

/// How much of the drive the home sheet shows (T-0237, ruling R2).
///
/// Two detents and no third. `collapsed` is the title, the conditions line and the button - the first thing anyone
/// sees, so it is short. `medium` adds the road list, the distance and timing lines and the caption. There is no
/// `large`: the map is the screen, and the credit pill lives ON the map directly above the sheet, so a sheet that
/// covered the map would leave the credit nowhere to sit.
///
/// The heights are not stored here. Each detent is as tall as its content, so the largest Dynamic Type sizes grow
/// the sheet instead of clipping the safety line out of it.
enum HomeSheetDetent: String, CaseIterable, Sendable {
    case collapsed
    case medium

    /// The launch argument that picks the first detent: `-homeDetent medium`. `simctl launch` hands trailing
    /// arguments to the app, and a `-key value` pair lands in UserDefaults' argument domain, which is read here and
    /// written nowhere - nothing persists, and a plain launch is `collapsed`. The screenshot workflow uses it to
    /// shoot both detents (ruling R10).
    static let launchArgumentKey = "homeDetent"

    /// The detent the screen opens on.
    static var atLaunch: HomeSheetDetent {
        UserDefaults.standard.string(forKey: launchArgumentKey).flatMap(HomeSheetDetent.init(rawValue:)) ?? .collapsed
    }

    /// The other detent: what a tap on the grabber moves to.
    var toggled: HomeSheetDetent {
        switch self {
        case .collapsed: return .medium
        case .medium: return .collapsed
        }
    }
}
