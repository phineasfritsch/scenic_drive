import DesignSystem
import ScenicKit
import SwiftUI

/// The home's Surprise slot under /config's feature_surprise (T-0368 R2): the shell's card while the gate is on, and
/// in its place the gate's typed line while it is off - the card builder is not called then, so no deck is drawn and
/// nothing is read for one. The gate is the shell's, read from the kept /config answer (R1); this view sends nothing.
struct SurpriseGateSlot: View {
    let gate: SurpriseGate
    let card: () -> AnyView

    var body: some View {
        if let line = gate.homeLine {
            Text(line)
                .font(.footnote)
                .foregroundStyle(DesignTokens.fg)
                .frame(maxWidth: .infinity, alignment: .leading)
                .fixedSize(horizontal: false, vertical: true)
                .padding(.horizontal, 8)
                .padding(.vertical, 6)
                .accessibilityIdentifier("home.surprise.off")
        } else {
            card()
        }
    }
}
