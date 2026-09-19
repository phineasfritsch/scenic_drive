import Foundation
import Handoff
import ScenicKit
import UIKit

/// The walking skeleton's one hard-coded drive, handed to Apple Maps: San Francisco, down the
/// Peninsula the pretty way, back to San Francisco.
///
/// M1.5 in the plan - *"'Open in Apple Maps' with a hard-coded Skyline waypoint list ... You open it
/// on your phone in week 2 and tap into Apple Maps on Skyline."* There is no planner yet, no routing
/// service and no corpus; this is the handoff proven end to end with a route a human chose, so that
/// when `ScenicKit` starts producing waypoints the only new thing is where the array comes from.
///
/// ## Where the coordinates went
///
/// The route itself - the destination, the seven pins, the Nominatim result beside each one and the
/// Bicycle Sunday note - is `Handoff.SkylineRoute`, in the root package. It was here, in an
/// Apple-only target that has no test bundle and no compiler on the authoring box, which meant the
/// one property worth checking (that the pins are close enough together that Apple Maps cannot take
/// the Edgewood Road rat-run back onto 280) had nowhere to be checked from. `SkylineRouteTests` in
/// `Tests/HandoffTests` checks it now, on Linux and on this box. This type keeps the UIKit half:
/// building the URL and leaving.
///
/// **Why the source is nil and the destination is San Francisco.** `source: nil` means "wherever you
/// are", which Apple Maps resolves to current location - the app never asks for a location permission
/// to build this URL. The route is therefore a loop: leave from where you stand, run the ridge, come
/// back. That is also why the last waypoint is the turn-around, not the end.
public enum SkylineHandoff {
    // MARK: - The route

    /// Where the selected drive ends, from `HandoffDrive`.
    ///
    /// Re-exported rather than re-declared: `ScenicHomeScreen` centres the map on it, and one verified
    /// coordinate with one home is the whole point of moving the arrays out of this file.
    public static func destination(for drive: HandoffDrive) -> Coordinate { drive.destination }

    /// The selected drive's pins, in driving order, from `HandoffDrive`.
    ///
    /// Order is the route: `AppleMapsDirections` emits repeated `waypoint` parameters in array order
    /// and Apple reads them in that order, so sorting or deduplicating this array would silently
    /// re-plan the drive.
    public static func waypoints(for drive: HandoffDrive) -> [Coordinate] { drive.waypoints }

    // MARK: - Handoff

    /// The selected route as a handoff request. `driving`, and no `avoid` - see `AppleMapsDirections`:
    /// asking Apple to avoid highways would throw away the freeway baseline that gets you to the
    /// pretty part of either drive.
    public static func directions(for drive: HandoffDrive) -> AppleMapsDirections {
        AppleMapsDirections(source: nil,
                            destination: drive.destination,
                            waypoints: drive.waypoints,
                            mode: .driving)
    }

    /// The `maps.apple.com/directions` URL, or the refusal `Handoff` raises.
    ///
    /// Throwing rather than returning an optional keeps the reason: `HandoffError` distinguishes "too
    /// many waypoints" from "that is not a coordinate", and a screen that shows the user a useful
    /// message needs to know which.
    public static func url(for drive: HandoffDrive) throws -> URL {
        try directions(for: drive).url()
    }

    /// Hands the drive to Apple Maps.
    ///
    /// `@MainActor` because `UIApplication.shared` is main-actor isolated under Swift 6; the isolation
    /// is declared here so the call site does not have to guess.
    ///
    /// The completion handler is ignored on purpose. `open` reports only whether iOS accepted the
    /// URL, and a `false` from a `https://maps.apple.com` URL means Maps is not installed - a state
    /// with no useful recovery from this button. It is not an error the user caused and not one this
    /// skeleton can fix, so it does not get an alert it cannot act on.
    /// THE ONE DOOR OUT OF THE APP, and it takes the drive as a VALUE rather than growing a sibling.
    ///
    /// `ops/lib/check-safety-disclaimer` (P-SAFE-03, (iv)) decides that `SkylineHandoff.open(` occurs
    /// exactly once across `apps/ios`, in `GatedHandoffButton.swift`, dominated by a guard on the
    /// acknowledgement. A second entry point for the second drive - `laOpen(` beside this - would be a
    /// second door with one lock, which is the hole that check exists to refuse, and it would leave
    /// the count at one while the gate held on only one of two taps. So the LA drive arrives here as a
    /// `HandoffDrive`, through the same guard, and a third drive would change none of it.
    ///
    /// The type keeps the name `SkylineHandoff` although it now hands over either drive: the check's
    /// anchors are that identifier and this file name, and `ops/` is outside this task's `touches:`.
    @MainActor
    public static func open(_ drive: HandoffDrive) throws {
        let destinationURL = try url(for: drive)
        UIApplication.shared.open(destinationURL, options: [:], completionHandler: nil)
    }
}
