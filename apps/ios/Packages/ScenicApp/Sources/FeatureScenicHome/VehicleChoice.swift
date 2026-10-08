import DesignSystem
import ScenicKit
import SwiftUI

/// The first onboarding step (T-0309): what you drive. Every `VehicleProfile` case is listed; only the enabled one can
/// be picked, and each other row says plainly why not yet. Calm copy: no promise about roads, no exclamation marks.
struct VehicleChoice: View {
    let chosen: VehicleProfile
    let onChoose: (VehicleProfile) -> Void
    let onContinue: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("What are you driving?")
                .font(.title2)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)

            Text("Routes are planned for a standard car. Other vehicles come later, once the map knows their limits.")
                .font(.body)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)

            ScrollView {
                VStack(alignment: .leading, spacing: 8) {
                    ForEach(VehicleProfile.allCases, id: \.self) { profile in
                        row(profile)
                    }
                }
            }

            Button(action: onContinue) {
                Text("Continue")
                    .font(.headline)
                    .foregroundStyle(DesignTokens.onPrimary)
                    .frame(maxWidth: .infinity, minHeight: 44)
                    .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(DesignTokens.primary))
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("onboarding.vehicle.continue")
        }
    }

    /// One vehicle: its name, a check when chosen, and the reason when it cannot be chosen yet.
    private func row(_ profile: VehicleProfile) -> some View {
        Button {
            onChoose(profile)
        } label: {
            HStack(alignment: .firstTextBaseline, spacing: 12) {
                VStack(alignment: .leading, spacing: 4) {
                    Text(profile.name)
                        .font(.body)
                        .foregroundStyle(profile.isEnabled ? DesignTokens.fg : DesignTokens.fgMuted)
                    if let reason = profile.disabledReason {
                        Text(reason)
                            .font(.footnote)
                            .foregroundStyle(DesignTokens.fgMuted)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                }
                Spacer(minLength: 0)
                if profile == chosen {
                    Image(systemName: "checkmark")
                        .foregroundStyle(DesignTokens.fg)
                        .accessibilityHidden(true)
                }
            }
            .frame(maxWidth: .infinity, minHeight: 44, alignment: .leading)
            .padding(12)
            .background(RoundedRectangle(cornerRadius: 12, style: .continuous).fill(DesignTokens.surface))
        }
        .buttonStyle(.plain)
        .disabled(!profile.isEnabled)
        .accessibilityAddTraits(profile == chosen ? .isSelected : [])
        .accessibilityIdentifier("onboarding.vehicle.\(profile.rawValue)")
    }
}
