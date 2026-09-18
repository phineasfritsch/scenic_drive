import SwiftUI

/// The map attribution line, bottom-right, on every map surface at every sheet detent.
///
/// The plan's P-ATTR-01, not yet filed in PINS.yaml (`grep -c P-ATTR-01 pins/PINS.yaml` -> 0); it is
/// written when the real PMTiles basemap lands, and nothing mechanical enforces this file until then.
/// The basemap licences are not decoration: OSM's ODbL and Protomaps both require visible
/// credit, and the demo basemap this skeleton ships against credits different parties again. That is
/// why `text` is a **required** initialiser parameter with no default. A default would be a string
/// baked in here that stays put when the tiles underneath it change, and the first thing anybody would
/// do with it is leave it - which is how a map ends up crediting OpenStreetMap for data that is not
/// theirs. Whoever mounts the map states what the map is made of.
///
/// - Note: the plan's `© OpenStreetMap contributors · Protomaps` string arrives with the real PMTiles
///   basemap. This type pins the *visibility* now and takes no view on the wording.
public struct AttributionFooter: View {
    private let text: String

    /// - Parameter text: the credit for the tiles actually on screen. Required; see the type note.
    public init(text: String) {
        self.text = text
    }

    public var body: some View {
        HStack(spacing: 0) {
            Spacer(minLength: 0)
            Text(text)
                .font(.footnote)
                // `fgMuted`, not `fg`: attribution is secondary text and must not compete with the
                // map. Both appearances of the pair clear 4.5:1 against `surface`, which is why the
                // chip below is opaque enough to be a surface rather than a tint over the tiles.
                .foregroundStyle(DesignTokens.fgMuted)
                .multilineTextAlignment(.trailing)
                // Dynamic Type can wrap this onto two lines on the largest sizes. Wrapping is correct;
                // truncating would drop a licence term, so there is no `lineLimit` here.
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 10)
                .padding(.vertical, 6)
                .background(
                    // Readable on both appearances because it carries its own ground rather than
                    // trusting the tiles: `surface` at 0.85 over anything the renderer draws, plus a
                    // hairline so the chip has an edge on a busy basemap.
                    RoundedRectangle(cornerRadius: 8, style: .continuous)
                        .fill(DesignTokens.surface.opacity(0.85))
                        .overlay(
                            RoundedRectangle(cornerRadius: 8, style: .continuous)
                                .strokeBorder(DesignTokens.border, lineWidth: 1)
                        )
                )
        }
        // Bottom-right, and at least 44 pt tall so it is a real target when it becomes tappable
        // (licence links) and so nothing lays out on top of it by accident.
        .frame(minHeight: 44, alignment: .bottomTrailing)
        .padding(.trailing, 12)
        .padding(.bottom, 8)
        .accessibilityElement(children: .combine)
        // Load-bearing identifier, reserved rather than used: no XCUITest exists yet - this package
        // has no test targets, because an XCTest bundle authored on a box with no Apple toolchain
        // could never be seen red. The XCUITest that proves attribution survives every sheet detent
        // arrives with the first green Xcode Cloud run, and it will anchor on this identifier rather
        // than on the text, because the text changes with the basemap.
        .accessibilityIdentifier("attribution.footer")
        // NEVER hidden from accessibility. Stated as an explicit `false` rather than left to the
        // default so that removing it is a visible deletion in a diff: a screen reader user is
        // entitled to the same credit line as everybody else, and `.accessibilityHidden(true)` here
        // would be a licence breach that renders identically in every screenshot.
        .accessibilityHidden(false)
    }
}
