import DesignSystem
import Handoff
import MapAdapter
import ScenicKit
import SwiftUI

/// The drive (T-0324): the planned line on the map with its credit, and exactly what ScenicKit's DriveDisplay says to
/// show for the navigator's surface and mode. This target never imports NavAdapter: the shell composes DriveHost's
/// published display into it (R1). It reads `display` and nothing else about the drive's state (P-SAFE-09, R7).
///
/// T-0397: on both surfaces, the map, its credit and DriveCard - the conditions line, the arrival, the minutes and
/// miles left (DriveDisplay's), the estimate caption and the one End pill, 60 pt tall while moving. Moving adds the
/// reroute or rejoin caption; stopped adds the status banner, the fresh-route note (T-0330 R3) and the End confirm.
public struct DriveScreen: View {
    @Environment(\.colorScheme) private var colorScheme
    /// T-0358 R7: where a post-drive answer goes - the shell's, from PlanAdapter; unset, nowhere.
    @Environment(\.postDriveAnswers) private var answers

    /// The basemap ACTUALLY on screen, named once so the tiles and the credit cannot drift apart (P-ATTR-01).
    @State private var style = MapStyle.maplibreDemoTiles
    /// The drive's current line as the map draws it - the plan's, then each taken reroute's (T-0328 R4); its data
    /// credit joins the footer.
    @State private var route: MapRoute?
    @State private var bannerBottom: CGFloat = 0
    @State private var creditBandTop: CGFloat = 0
    /// T-0358 R4: the question has been shown for this drive (one screen per drive); it is never shown again.
    @State private var asked = false
    /// T-0358 R2: the question is on screen in place of the controls.
    @State private var isAsking = false
    /// T-0397 R4: "End this drive?" is on screen in place of the card (full surface only).
    @State private var confirming = false

    private let preview: PlanPreview
    private let display: DriveDisplay
    private let onEnd: () -> Void

    public init(preview: PlanPreview, display: DriveDisplay, onEnd: @escaping () -> Void) {
        self.preview = preview
        self.display = display
        self.onEnd = onEnd
    }

    public var body: some View {
        ZStack(alignment: .top) {
            MapView(
                styleURL: style.url,
                centerLatitude: preview.route.first?.latitude ?? 0,
                centerLongitude: preview.route.first?.longitude ?? 0,
                zoomLevel: 12,
                coveredAboveY: bannerBottom,
                coveredBelowY: creditBandTop,
                route: route
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                banner
                    .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).maxY } action: { bannerBottom = $0 }

                Spacer(minLength: 0)

                VStack(spacing: 0) {
                    AttributionFooter(text: CreditLine.composed(basemap: style.attributionText, routeData: route?.dataCredit))
                    if isAsking {
                        PostDriveCard(onAnswer: answer)
                            .padding(16)
                            .frame(maxWidth: .infinity, alignment: .leading)
                            .background(DesignTokens.surface)
                    } else if confirming && display.showsDetails {
                        DriveEndConfirm(onKeep: { confirming = false }, onEnd: endDrive)
                    } else {
                        controls
                    }
                }
                .onGeometryChange(for: CGFloat.self) { $0.frame(in: .global).minY } action: { creditBandTop = $0 }
            }
        }
        .background(DesignTokens.bg)
        .task { resolveMap() }
        .onChange(of: colorScheme) { resolveMap() }
        .onChange(of: display.line) { resolveMap() }
        .onChange(of: display.showsDetails) { if !display.showsDetails { closeOnMoving() } }
    }

    /// The full surface's status, as a sentence under the status bar. Nothing on the minimal surface.
    @ViewBuilder private var banner: some View {
        if display.showsDetails, let status = display.status {
            Label(status, systemImage: "arrow.triangle.turn.up.right.circle")
                .font(.body)
                .foregroundStyle(DesignTokens.fg)
                .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
                .padding(.horizontal, 16)
                .background(DesignTokens.surface)
                .accessibilityIdentifier("drive.status")
        }
    }

    /// T-0397: the card on both surfaces - the conditions line, arrival, minutes and miles, the estimate caption and
    /// the one short End pill (R2/R3); the reroute or rejoin caption while moving, the fresh note when stopped.
    private var controls: some View {
        DriveCard(remainingSeconds: display.remainingSeconds, glanceLine: display.glanceLine,
                  showsEstimate: preview.showsEstimateBadge,
                  caption: display.showsDetails ? nil : display.status, note: display.note,
                  endTitle: display.actionTitle, endMinHeight: display.actionMinHeight, onEnd: endTapped)
    }

    /// T-0397 R4: stopped, End asks "End this drive?" first; moving, it ends at once - no new surface above 4.5 m/s.
    private func endTapped() {
        if display.showsDetails {
            confirming = true
        } else {
            endDrive()
        }
    }

    /// T-0358 R2: ending asks the post-drive question once when PostDriveQuestion says so (arrived, stopped, not
    /// asked); otherwise the drive ends.
    private func endDrive() {
        confirming = false
        if PostDriveQuestion.asks(after: display, alreadyAsked: asked) {
            asked = true
            isAsking = true
        } else {
            onEnd()
        }
    }

    /// T-0358 R2 / T-0397 R4: moving closes the confirm, and moving while the question shows is a skip.
    private func closeOnMoving() {
        confirming = false
        if isAsking { answer(.dismissed) }
    }

    /// T-0358 R5/R6: the tapped answer goes to PostDriveQuestion.send (a skip sends nothing), and the drive ends.
    /// Moving while the question shows is a skip (R2).
    private func answer(_ answer: PostDriveAnswer) {
        isAsking = false
        PostDriveQuestion.send(answer, to: answers)
        onEnd()
    }

    /// The LA basemap when the archive is on the phone, the demo tiles when it is not, and the line the drive is on.
    private func resolveMap() {
        route = DriveMapLine.route(for: display.line)
        style = DriveBasemap.planned(appearance: colorScheme == .dark ? .dark : .light)
    }
}
