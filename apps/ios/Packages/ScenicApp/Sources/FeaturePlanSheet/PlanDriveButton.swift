import DesignSystem
import SwiftUI

/// The home's way into the plan sheet, composed over the home by the app shell (T-0294 R1).
public struct PlanDriveButton: View {
    private let action: () -> Void

    public init(action: @escaping () -> Void) {
        self.action = action
    }

    public var body: some View {
        Button(action: action) {
            Text("Plan a drive")
                .font(.headline)
                .foregroundStyle(DesignTokens.fg)
                .padding(.horizontal, 16)
                .frame(minHeight: 44)
                .background(
                    Capsule()
                        .fill(DesignTokens.surface.opacity(0.92))
                        .overlay(Capsule().strokeBorder(DesignTokens.border, lineWidth: 1))
                )
        }
        .buttonStyle(.plain)
        .padding(.leading, 16)
        .padding(.top, 8)
        .accessibilityIdentifier("plan.start")
    }
}
