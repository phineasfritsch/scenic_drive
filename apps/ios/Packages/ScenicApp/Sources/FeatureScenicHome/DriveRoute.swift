import DesignSystem
import Foundation
import Handoff
import MapAdapter

/// The road line a drive draws on the map, or `nil` - resolved from the app bundle, in the token colours.
///
/// ## Where the name comes from
///
/// `HandoffDrive.routeGeometryResource` - a Linux-testable property beside the drive's pins, so the file the
/// map draws and the URL the button opens are bound by `SaddlePeakGeometryTests` rather than by review. This
/// type names no drive: a drive with a resource draws it, a drive without one draws nothing, and nothing here
/// could draw straight lines between pins, which would cross the mountains.
///
/// ## Why the caller keeps it off the body's hot path
///
/// It reads a file from the bundle. `ScenicHomeScreen` holds the answer in `@State` and asks once per
/// selection change and once per appearance change, beside `DriveBasemap.resolve` and for the same reason.
enum DriveRoute {
    /// The muted rows' colour: the route's own blue, faded, so the menu reads as one family of lines and the
    /// selected one is the only line at full strength (T-0246).
    static let mutedOpacity = 0.35

    /// The bundled line for `drive`, in `DesignTokens.route` over a `DesignTokens.surface` casing, carrying the
    /// drive's data credit for the footer - a drive that names a line and no credit draws none.
    ///
    /// A drive with a `menu` (T-0246) draws the menu's `selected` row in place of that line and the other rows
    /// muted under it: `MapRoute.redrawn` swaps the geometry of the route bound here and keeps its credit, so
    /// the footer's credit is still the one bound on the first line of this function.
    static func resolve(for drive: HandoffDrive, menu: DriveMenu?, selected: Int?) -> MapRoute? {
        guard let name = drive.routeGeometryResource, let credit = drive.routeGeometryCredit else {
            return nil
        }
        let route = MapRoute.bundled(named: name,
                                     subdirectory: HandoffDrive.routeGeometrySubdirectory,
                                     withExtension: HandoffDrive.routeGeometryExtension,
                                     dataCredit: credit,
                                     lineColor: DesignTokens.route,
                                     casingColor: DesignTokens.surface)
        guard let menu else { return route }
        return route?.redrawn(geoJSON: menu.geoJSON(selected: selected),
                              muted: menu.mutedGeoJSON(selected: selected),
                              mutedColor: DesignTokens.route.opacity(mutedOpacity))
    }

    /// The drive's bundled menu, or `nil` - a drive without one, or a build that does not carry the file. The
    /// same two lookups as `MapRoute.bundled`: the buildable folder's shape, then the bundle root.
    static func menu(for drive: HandoffDrive, bundle: Bundle = .main) -> DriveMenu? {
        guard let name = drive.menuResource else { return nil }
        let url = bundle.url(forResource: name, withExtension: HandoffDrive.menuExtension,
                             subdirectory: HandoffDrive.routeGeometrySubdirectory)
            ?? bundle.url(forResource: name, withExtension: HandoffDrive.menuExtension)
        guard let url, let data = try? Data(contentsOf: url) else { return nil }
        return try? DriveMenu(data: data)
    }
}
