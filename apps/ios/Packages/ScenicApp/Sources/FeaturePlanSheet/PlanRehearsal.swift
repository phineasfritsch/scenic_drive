import Foundation
import ScenicKit

/// The plan sheet a DEBUG build opens on when launched with `-screen preview|nothingPretty|loop|trip|saved` -
/// ios-screenshot's plan-sheet shots (T-0336 R2) - and in every release build, none.
///
/// The `-screen` pair lands in UserDefaults' argument domain, read here inside `#if DEBUG` and written nowhere
/// (DriveRehearsal's pattern). Each state is built through its machine's own public API - the gate's ticket, then
/// `finish` with a fixed outcome (R3) - by `PlanRehearsalFixtures`, a file compiled only in DEBUG. No planner is called.
/// It lives here because the shell may carry no `#` directive (ops/lib/check-safety-disclaimer-frozen).
public struct PlanRehearsal {
    /// Which of the sheet's contents is on screen.
    enum Tab {
        case plan
        case loop
        case trip
        case saved
    }

    let tab: Tab
    let sheet: PlanSheet
    let loop: LoopSheet
    let trip: TripSheet
    let savedRows: [SavedRow]

    /// The rehearsal to open, or nil: always nil outside DEBUG.
    static var atLaunch: PlanRehearsal? {
        #if DEBUG
        return UserDefaults.standard.string(forKey: "screen").flatMap(PlanRehearsalFixtures.rehearsal(named:))
        #else
        return nil
        #endif
    }

    /// Whether the shell opens the plan sheet at launch: false in every release build.
    public static var opensSheet: Bool {
        atLaunch != nil
    }
}
