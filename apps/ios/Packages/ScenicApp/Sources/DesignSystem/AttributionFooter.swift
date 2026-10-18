import SwiftUI

/// The map attribution line, bottom-right, on every map surface at every sheet detent (P-ATTR-01).
///
/// The basemap licences are not decoration: OSM's ODbL and Protomaps both require visible credit, and the demo
/// basemap credits different parties again. That is why `text` is a **required** initialiser parameter with no
/// default: whoever mounts the map states what the map is made of, and this type never names a party.
///
/// T-0404: a caption, not a box. At every non-accessibility Dynamic Type size it is ONE line that shrinks rather
/// than wraps; at accessibility sizes it is a strip of at most TWO lines split at the credit's own " · "
/// separator (one line when the text is a single party). Every visible line has `lineLimit(1)`, so no break can fall inside a word
/// ("OpenStreet-Map" at AX5 on T-0397's drive screen), and Dynamic Type is clamped at `.accessibility2` so the
/// strip's height is bounded and it never grows over the route, MapLibre's (i) or the sheet's controls. The text is
/// rendered verbatim and nothing is dropped; VoiceOver reads `text` whole, whatever the visible split or scale.
public struct AttributionFooter: View {
    private let text: String
    @Environment(\.dynamicTypeSize) private var typeSize

    /// - Parameter text: the credit for the tiles actually on screen. Required; see the type note.
    public init(text: String) {
        self.text = text
    }

    public var body: some View {
        HStack(spacing: 0) {
            // MapLibre's logo hangs from the top-left (MapView.swift, `logoViewPosition = .topLeft`), so the
            // lower-left is free and the caption may use the full width rather than wrap.
            Spacer(minLength: 12)
            if typeSize.isAccessibilitySize {
                // Always the strip at accessibility sizes: run 39062709376 showed a ViewThatFits here accepting
                // the one-line child at half scale (about 12 pt at AX5), so the split is decided, not measured.
                VStack(alignment: .trailing, spacing: 0) {
                    ForEach(Array(AttributionFooter.strip(text).enumerated()), id: \.offset) { item in
                        line(item.element)
                    }
                }
            } else {
                line(text)
            }
        }
        // Bounded height: two caption2 lines at about 24 pt is the most this ever draws.
        .dynamicTypeSize(...DynamicTypeSize.accessibility2)
        // At least 44 pt tall so it is a real target when it becomes tappable (licence links); bottom-aligned, so
        // the extra height is empty, not drawn.
        .frame(minHeight: 44, alignment: .bottomTrailing)
        .padding(.trailing, 12)
        .padding(.bottom, 8)
        // One element, labelled with the whole credit verbatim, so a VoiceOver user hears every party even when
        // the visible caption is split over two lines or scaled down.
        .accessibilityElement(children: .ignore)
        .accessibilityLabel(Text(text))
        // Load-bearing identifier for the XCUITest that proves attribution survives every sheet detent (T-0180);
        // it anchors here rather than on the text, because the text changes with the basemap.
        .accessibilityIdentifier("attribution.footer")
        // NEVER hidden from accessibility. Stated as an explicit `false` so removing it is a visible deletion in a
        // diff: `.accessibilityHidden(true)` here is a licence breach that renders identically in every screenshot.
        .accessibilityHidden(false)
    }

    /// One visible line: caption2, muted, never wrapped. It shrinks to fit instead of breaking or truncating; the
    /// longest line the CI credit produces needs about 0.65 at xxxLarge, inside the 0.5 floor.
    private func line(_ string: String) -> some View {
        Text(string)
            .font(.caption2)
            // `fgMuted`: attribution is secondary text and must not compete with the map.
            .foregroundStyle(DesignTokens.fgMuted)
            .lineLimit(1)
            .minimumScaleFactor(0.5)
            .allowsTightening(true)
            // No box: a crisp one-point outline in `surface` - the ground `fgMuted` clears 4.5:1 against in both
            // appearances - keeps the glyphs legible on any tile and covers nothing beyond the letters. Blurred
            // shadows went translucent and muddy on the light demo tiles in dark mode (run 39065139596).
            .shadow(color: DesignTokens.surface, radius: 0, x: 1, y: 0)
            .shadow(color: DesignTokens.surface, radius: 0, x: -1, y: 0)
            .shadow(color: DesignTokens.surface, radius: 0, x: 0, y: 1)
            .shadow(color: DesignTokens.surface, radius: 0, x: 0, y: -1)
    }

    /// The credit split at its " · " separators into at most two lines with the most even lengths. The first
    /// line keeps the trailing " ·" so the reader sees the credit continue. One party stays one line.
    static func strip(_ caption: String) -> [String] {
        let separator = " · "
        let parties = caption.components(separatedBy: separator)
        guard parties.count > 1 else { return [caption] }
        var best = 1
        var bestWidth = Int.max
        for cut in 1..<parties.count {
            let head = parties[..<cut].joined(separator: separator).count + 2
            let tail = parties[cut...].joined(separator: separator).count
            if max(head, tail) < bestWidth {
                bestWidth = max(head, tail)
                best = cut
            }
        }
        return [
            parties[..<best].joined(separator: separator) + " ·",
            parties[best...].joined(separator: separator),
        ]
    }
}
