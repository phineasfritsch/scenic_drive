import DesignSystem
import SwiftUI

/// The first-run places download (T-0305 R5): what it is, its progress, Download and Not now. Plain values and
/// closures - the shell hands in PlanAdapter's LiveCorpus state; this target imports no root module.
///
/// Presented by the shell FULL HEIGHT (no presentationDetents: no partial sheet ever covers the home's credit,
/// P-ATTR-01). "Not now" only closes it: the download carries on, and Surprise Me and search keep reading the bundled
/// corpus until the next cold launch activates the new one - nothing waits on this sheet.
public struct CorpusDownloadSheet: View {
    private let status: String
    private let fraction: Double
    private let isWorking: Bool
    private let onDownload: () -> Void
    private let onLater: () -> Void

    public init(status: String, fraction: Double, isWorking: Bool, onDownload: @escaping () -> Void,
                onLater: @escaping () -> Void) {
        self.status = status
        self.fraction = fraction
        self.isWorking = isWorking
        self.onDownload = onDownload
        self.onLater = onLater
    }

    public var body: some View {
        NavigationStack {
            VStack(alignment: .leading, spacing: 16) {
                Text(status)
                    .foregroundStyle(DesignTokens.fg)
                    .accessibilityIdentifier("corpus.status")
                if isWorking {
                    ProgressView(value: min(max(fraction, 0), 1))
                        .accessibilityIdentifier("corpus.progress")
                }
                Text("Uses Wi-Fi only unless you change it in Settings.")
                    .font(.footnote)
                    .foregroundStyle(DesignTokens.fgMuted)
                Button("Download", action: onDownload)
                    .disabled(isWorking)
                    .frame(minHeight: 44)
                    .accessibilityIdentifier("corpus.download")
                Spacer()
            }
            .padding(16)
            .frame(maxWidth: .infinity, alignment: .leading)
            .background(DesignTokens.bg)
            .navigationTitle("Places")
            .toolbar {
                ToolbarItem(placement: .cancellationAction) {
                    Button("Not now", action: onLater)
                        .frame(minHeight: 44)
                        .accessibilityIdentifier("corpus.later")
                }
            }
        }
        .tint(DesignTokens.fg)
    }
}
