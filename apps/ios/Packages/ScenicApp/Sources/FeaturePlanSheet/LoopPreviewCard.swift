import DesignSystem
import ScenicKit
import SwiftUI

/// The loop's preview (T-0314 R6, R8): how long and how far against the dial, the estimate badge, the retrace check the
/// device ran on the path, and one Apple Maps link that starts and ends at the start through the loop's pins. Drawn
/// only in the sheet's preview state, which only a ticket reaches - after the safety note (P-SAFE-03). The safety
/// line stays on screen.
struct LoopPreviewCard: View {
    let preview: LoopPreview
    let minutes: Int
    let start: String
    let link: URL?
    let onChange: () -> Void

    var body: some View {
        List {
            Section {
                Text("A loop from \(start) and back")
                    .font(.headline)
                Text("About \(Self.duration(preview.durationSeconds)) behind the wheel, \(Self.miles(preview.distanceMeters)). You asked for \(minutes) min.")
                    .fixedSize(horizontal: false, vertical: true)
                if preview.etaIsEstimate {
                    Text(PlanPreview.estimateBadge)
                        .font(.caption)
                        .foregroundStyle(DesignTokens.fgMuted)
                        .accessibilityIdentifier("loop.estimate")
                }
                Text(Self.retraceLine(preview.retraceFraction))
                    .fixedSize(horizontal: false, vertical: true)
                    .accessibilityIdentifier("loop.retrace")
                ForEach(Array(HazardCopy.lines(for: preview).enumerated()), id: \.offset) { _, line in
                    Label(line, systemImage: "exclamationmark.triangle.fill")
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("loop.closures")
                }
            }
            Section {
                if let link {
                    Link("Open the loop in Apple Maps", destination: link)
                        .accessibilityIdentifier("loop.maps")
                }
                Text(PlanPreview.conditions)
                    .font(.footnote)
                    .fixedSize(horizontal: false, vertical: true)
                Button("Change the loop", action: onChange)
                    .accessibilityIdentifier("loop.change")
            }
        }
    }

    static func retraceLine(_ fraction: Double) -> String {
        let limit = Int((RetraceDetector.maxRetraceFraction * 100).rounded())
        return "Doubles back on \(Int((fraction * 100).rounded()))% of its road, inside the \(limit)% we allow."
    }

    static func duration(_ seconds: Double) -> String {
        let minutes = Int((seconds / 60).rounded())
        return minutes < 60 ? "\(minutes) min" : "\(minutes / 60) h \(minutes % 60) min"
    }

    static func miles(_ meters: Double) -> String {
        "\(Int((meters / 1609.344).rounded())) mi"
    }
}
