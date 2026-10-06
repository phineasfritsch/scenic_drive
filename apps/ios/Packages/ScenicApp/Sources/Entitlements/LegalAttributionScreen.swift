import DesignSystem
import SwiftUI

/// Legal & Attribution: the OpenStreetMap ODbL notice, word for word from LICENSE-DATA (pin P-ATTR-02's file).
///
/// `odblNotice` is LICENSE-DATA's `## OpenStreetMap — ODbL 1.0` section, one element per line of that file, and
/// ops/lib/check-store-links.py compares the two line for line: an edit to either is refused until both move
/// (ruling R7). The Protomaps line is not copied here - it carries the plan's credit string, which P-ATTR-01 allows
/// exactly once in the app, at its declaration in MapAdapter.
public struct LegalAttributionScreen: View {
    public init() {}

    static let odblNotice: [String] = [
        "© OpenStreetMap contributors. Data available under the Open Database License, https://www.openstreetmap.org/copyright.",
        "Our derived databases (the scenic segment corpus, the tagged routing extract, the basemap tiles) contain information",
        "from OpenStreetMap and are themselves offered under the ODbL. The scoring algorithm and its weights are ours.",
        "Attribution \"© OpenStreetMap contributors\" is shown on every map surface in the app.",
    ]

    public var body: some View {
        ScrollView {
            VStack(alignment: .leading, spacing: 16) {
                Text("OpenStreetMap — ODbL 1.0")
                    .font(.headline)
                    .foregroundStyle(DesignTokens.fg)
                    .accessibilityAddTraits(.isHeader)
                Text(Self.odblNotice.joined(separator: " "))
                    .font(.body)
                    .foregroundStyle(DesignTokens.fg)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("legal.odbl")
                Link(destination: URL(string: "https://www.openstreetmap.org/copyright")!) {
                    Label("openstreetmap.org/copyright", systemImage: "arrow.up.right.square")
                        .font(.body)
                        .foregroundStyle(DesignTokens.fg)
                        .frame(minHeight: 44)
                }
                .accessibilityIdentifier("legal.copyright")
            }
            .frame(maxWidth: .infinity, alignment: .leading)
            .padding(16)
        }
        .background(DesignTokens.bg)
        .navigationTitle("Legal & Attribution")
        .navigationBarTitleDisplayMode(.inline)
    }
}
