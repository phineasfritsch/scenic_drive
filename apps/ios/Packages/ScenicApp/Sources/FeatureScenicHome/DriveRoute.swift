import DesignSystem
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
    /// The bundled line for `drive`, in `DesignTokens.route` over a `DesignTokens.surface` casing.
    static func resolve(for drive: HandoffDrive) -> MapRoute? {
        guard let name = drive.routeGeometryResource else {
            return nil
        }
        return MapRoute.bundled(named: name,
                                subdirectory: HandoffDrive.routeGeometrySubdirectory,
                                withExtension: HandoffDrive.routeGeometryExtension,
                                lineColor: DesignTokens.route,
                                casingColor: DesignTokens.surface)
    }
}
