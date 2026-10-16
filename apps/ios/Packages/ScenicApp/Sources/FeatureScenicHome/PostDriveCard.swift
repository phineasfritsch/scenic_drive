import DesignSystem
import ScenicKit
import SwiftUI

/// "Prettier than your usual way?" (T-0358 R5/R9): the question and ScenicKit's closed answer set, one button per
/// answer in its order. It decides nothing - the drive screen shows it only when PostDriveQuestion says so, and hands
/// the tapped answer to PostDriveQuestion.send.
struct PostDriveCard: View {
    let onAnswer: (PostDriveAnswer) -> Void

    var body: some View {
        VStack(alignment: .leading, spacing: 12) {
            Text(PostDriveQuestion.prompt)
                .font(.title3)
                .fontWeight(.semibold)
                .foregroundStyle(DesignTokens.fg)
                .accessibilityIdentifier("drive.question")
            HStack(spacing: 12) {
                ForEach(PostDriveAnswer.allCases, id: \.self) { answer in
                    Button(answer.title) { onAnswer(answer) }
                        .font(.body)
                        .fontWeight(answer == .dismissed ? .regular : .semibold)
                        .foregroundStyle(answer == .dismissed ? DesignTokens.fgMuted : DesignTokens.onPrimary)
                        .frame(maxWidth: .infinity, minHeight: 44)
                        .background(RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .fill(answer == .dismissed ? DesignTokens.surface : DesignTokens.primary))
                        .buttonStyle(.plain)
                        .accessibilityIdentifier("drive.question.\(answer)")
                }
            }
        }
    }
}
