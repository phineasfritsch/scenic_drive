import DesignSystem
import ScenicKit
import SwiftUI

/// The day-by-day itinerary (T-0313 R5): the whole drive against the fastest with the estimate badge, then each day's
/// drive time and distance and whether it ends with a night's stop. A day opens in Apple Maps only when its answer
/// carries the day's own path - a full itinerary; the free preview says so calmly. The safety line stays on screen.
struct TripItineraryCard: View {
    let itinerary: TripItinerary
    let destination: String
    let dayLinks: ([Coordinate]) -> [URL]
    let onChange: () -> Void

    var body: some View {
        List {
            Section {
                Text(itinerary.days.count == 1 ? "A one-day drive to \(destination)"
                                               : "\(itinerary.days.count) days to \(destination)")
                    .font(.headline)
                Text("About \(Self.duration(itinerary.etaSeconds)) behind the wheel, \(Self.duration(max(0, itinerary.etaSeconds - itinerary.fastestEtaSeconds))) more than the fastest way")
                    .fixedSize(horizontal: false, vertical: true)
                if itinerary.etaIsEstimate {
                    Text(PlanPreview.estimateBadge)
                        .font(.caption)
                        .foregroundStyle(DesignTokens.fgMuted)
                        .accessibilityIdentifier("trip.estimate")
                }
                ForEach(Array(HazardCopy.lines(for: itinerary).enumerated()), id: \.offset) { _, line in
                    Label(line, systemImage: "exclamationmark.triangle.fill")
                        .fixedSize(horizontal: false, vertical: true)
                        .accessibilityIdentifier("trip.closures")
                }
            }
            ForEach(itinerary.days, id: \.day) { day in
                Section("Day \(day.day)") {
                    Text("\(Self.duration(day.driveSeconds)) · \(Self.miles(day.distanceMeters))")
                    if day.overnight {
                        Text("Ends with a night's stop. Places along the way are not searched yet.")
                            .foregroundStyle(DesignTokens.fgMuted)
                            .fixedSize(horizontal: false, vertical: true)
                    }
                    if let path = day.path {
                        let links = dayLinks(path)
                        ForEach(Array(links.enumerated()), id: \.offset) { index, url in
                            Link(Self.label(day: day.day, part: index + 1, of: links.count), destination: url)
                                .accessibilityIdentifier("trip.day\(day.day).maps\(index + 1)")
                        }
                    }
                }
            }
            Section {
                if !itinerary.isFull {
                    Text("Day-by-day Apple Maps handoff comes with the full itinerary.")
                        .foregroundStyle(DesignTokens.fgMuted)
                        .fixedSize(horizontal: false, vertical: true)
                }
                Text(PlanPreview.conditions)
                    .font(.footnote)
                    .fixedSize(horizontal: false, vertical: true)
                Button("Change the trip", action: onChange)
                    .accessibilityIdentifier("trip.change")
            }
        }
    }

    static func label(day: Int, part: Int, of parts: Int) -> String {
        parts == 1 ? "Open day \(day) in Apple Maps" : "Open day \(day), part \(part) of \(parts), in Apple Maps"
    }

    static func duration(_ seconds: Double) -> String {
        let minutes = Int((seconds / 60).rounded())
        return minutes < 60 ? "\(minutes) min" : "\(minutes / 60) h \(minutes % 60) min"
    }

    static func miles(_ meters: Double) -> String {
        "\(Int((meters / 1609.344).rounded())) mi"
    }
}
