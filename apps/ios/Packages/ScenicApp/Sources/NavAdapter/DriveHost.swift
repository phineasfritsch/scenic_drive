import ScenicKit
import SwiftUI

/// The drive on screen (T-0324 R1): owns one DriveNavigator for as long as it is shown - guidance starts when it
/// appears and stops when it goes - and hands the navigator's published DriveDisplay to the screen the shell
/// composes. The feature target that draws the drive never imports this module; the shell joins the two, and hands
/// it the reroute sender (T-0328 R2) - NavAdapter imports no API client.
public struct DriveHost<Content: View>: View {
    @StateObject private var navigator: DriveNavigator
    private let content: (DriveDisplay) -> Content

    /// nil when the preview is not a drivable line with its pins on it - DriveNavigator's own check, made first so
    /// the navigator (and its location provider) is built once, by the state object, and never thrown away.
    public init?(preview: PlanPreview, sender: any RerouteSending,
                 @ViewBuilder content: @escaping (DriveDisplay) -> Content) {
        guard DriveSession(line: preview.route, waypoints: preview.waypoints, lambda: preview.lambda,
                           online: true) != nil else { return nil }
        _navigator = StateObject(wrappedValue: DriveNavigator(preview: preview, sender: sender)!)
        self.content = content
    }

    public var body: some View {
        content(navigator.display)
            .onAppear { try? navigator.start() }
            .onDisappear { navigator.stop() }
    }
}
