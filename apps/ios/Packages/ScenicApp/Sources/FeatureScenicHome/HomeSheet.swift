import DesignSystem
import SwiftUI

/// The home screen's bottom sheet: a grabber, the summary always, the details at `medium` (T-0237).
///
/// ## An overlay, not a presentation (ruling R1)
///
/// This is a view laid out in the screen's own stack, not a `.sheet`. ScenicHomeScreen mounts it as the second
/// child of a `VStack(spacing: 0)` whose first child is the credit pill, so the pill sits on the map directly above
/// this view's top edge at every detent and in the middle of a drag - by layout, which P-ATTR-01's limb (h) reads
/// (`ops/lib/check-map-attribution-sheet`). A system sheet is presented in its own window over the map, and a credit
/// kept above it has to chase a height reported back across the presentation.
///
/// Nothing dismisses it: there is no presentation to dismiss, and a drag only moves between the two detents. It is
/// not modal: it takes touches inside its own frame and the map above it takes the rest.
///
/// ## Its ground
///
/// `DesignTokens.bg` with `fg`/`fgMuted` on it - the pairs the token table states contrast for - and a `border`
/// hairline so its edge reads on either basemap. The ground runs under the home indicator; the content stops above
/// it.
struct HomeSheet<Summary: View, Details: View>: View {
    @Binding var detent: HomeSheetDetent
    @ViewBuilder let summary: () -> Summary
    @ViewBuilder let details: () -> Details

    /// A drag shorter than this is not a request to change detent.
    private static var dragThreshold: CGFloat { 40 }

    var body: some View {
        VStack(alignment: .leading, spacing: 0) {
            grabber

            VStack(alignment: .leading, spacing: 12) {
                summary()
                if detent == .medium {
                    details()
                        .transition(.opacity)
                }
            }
            .padding(.horizontal, 16)
            .padding(.bottom, 12)
        }
        .frame(maxWidth: .infinity, alignment: .leading)
        .background {
            UnevenRoundedRectangle(topLeadingRadius: 20, topTrailingRadius: 20, style: .continuous)
                .fill(DesignTokens.bg)
                .overlay(
                    UnevenRoundedRectangle(topLeadingRadius: 20, topTrailingRadius: 20, style: .continuous)
                        .stroke(DesignTokens.border, lineWidth: 1)
                )
                .shadow(color: Color.black.opacity(0.15), radius: 10, x: 0, y: -2)
                .ignoresSafeArea(edges: .bottom)
        }
        .contentShape(Rectangle())
        .gesture(drag)
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("home.sheet")
    }

    /// The handle, and a real button: a tap moves to the other detent, so VoiceOver and Switch Control users are
    /// never asked to drag. 44 pt tall across the whole width.
    private var grabber: some View {
        Button {
            withAnimation(.snappy) { detent = detent.toggled }
        } label: {
            Capsule()
                .fill(DesignTokens.fgMuted.opacity(0.5))
                .frame(width: 36, height: 5)
                .frame(maxWidth: .infinity, minHeight: 44)
                .contentShape(Rectangle())
        }
        .buttonStyle(.plain)
        .accessibilityLabel(detent == .medium ? "Show less about this drive" : "Show more about this drive")
        .accessibilityIdentifier("home.sheet.grabber")
    }

    /// Up for `medium`, down for `collapsed`; never off the screen, because there is no third place to go.
    private var drag: some Gesture {
        DragGesture(minimumDistance: 12)
            .onEnded { value in
                let rise = -value.translation.height
                guard abs(rise) > Self.dragThreshold else { return }
                withAnimation(.snappy) { detent = rise > 0 ? .medium : .collapsed }
            }
    }
}
