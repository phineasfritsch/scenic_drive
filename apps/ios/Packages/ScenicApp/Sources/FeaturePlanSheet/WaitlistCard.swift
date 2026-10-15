import DesignSystem
import ScenicKit
import SwiftUI

/// A start outside the served region, after "Count this area" (T-0360 R4): what the tap came to, what such a tap
/// sends at most, and the way on - another start. While the one request is out there is no button to send another.
struct WaitlistCard: View {
    /// Nil while the request is out.
    let answer: WaitlistAnswer?
    let onChangeStart: () -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 16) {
            Text("Count this area")
                .font(.headline)
                .foregroundStyle(DesignTokens.fg)
            if let answer {
                Text(answer.line)
                    .font(.body)
                    .foregroundStyle(DesignTokens.fg)
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("plan.waitlist.answer")
            } else {
                ProgressView("Counting this area")
                    .accessibilityIdentifier("plan.waitlist.sending")
            }
            Text("What this sends: one rough area around your start, worked out from it rounded to two decimals. "
                 + "Never the start itself, and once per area from this phone.")
                .font(.footnote)
                .foregroundStyle(DesignTokens.fgMuted)
                .fixedSize(horizontal: false, vertical: true)
            if answer != nil {
                Button(action: onChangeStart) {
                    Text(PlanFailureAction.changeStart.title)
                        .font(.headline)
                        .foregroundStyle(DesignTokens.onPrimary)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .background(RoundedRectangle(cornerRadius: 16, style: .continuous).fill(DesignTokens.primary))
                }
                .buttonStyle(.plain)
                .accessibilityIdentifier("plan.waitlist.changeStart")
            }
            Spacer(minLength: 0)
        }
        .padding(20)
    }
}
