import DesignSystem
import ScenicKit
import SwiftUI

/// The Surprise card (T-0273): one place within reach of the bundled corpus, why to go, an ESTIMATED round trip,
/// the golden-hour line when there is one, Open in Apple Maps and four ways to say "not this".
///
/// It never opens a URL. `onOpenInMaps` is the home's gated opener, handed in by the shell: the safety disclaimer
/// stands between this button and Apple Maps exactly as it does for the home's own button (P-SAFE-03).
public struct SurpriseCard: View {
    private let failure: String?
    private let onOpenInMaps: @MainActor (Coordinate) -> Void

    /// The device's history (every place shown, T-0310 R7, and every "not this") and the basis the pick is made
    /// from, which recording never moves (T-0312 R5).
    @State private var state = SurpriseCardHistory()
    @State private var ledgerPlaces: [SurpriseLedgerPlace]?
    @State private var ledgerRead = false
    @Environment(\.surpriseLedger) private var ledger
    @State private var now = Date()

    public init(failure: String?, onOpenInMaps: @escaping @MainActor (Coordinate) -> Void) {
        self.failure = failure
        self.onOpenInMaps = onOpenInMaps
    }

    public var body: some View {
        Group {
            if let deck = SurpriseDeck.bundled, let pick = deck.pick(history: merged(deck), at: now),
               let candidate = deck.byID[pick.candidateId], let placeClass = deck.classes[pick.candidateId] {
                content(pick: pick, candidate: candidate, placeClass: placeClass)
            } else {
                empty
            }
        }
        .padding(12)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(RoundedRectangle(cornerRadius: 14, style: .continuous).fill(DesignTokens.surface))
        .overlay(
            RoundedRectangle(cornerRadius: 14, style: .continuous)
                .strokeBorder(DesignTokens.border, lineWidth: 1)
        )
        .accessibilityElement(children: .contain)
        .accessibilityIdentifier("surprise.card")
        .task {
            state = state.restoring(SurpriseShownLog.load())
            SurpriseShownLog.save(state.history.shown, today: SurpriseDeck.context(at: now).date)
            ledgerPlaces = await ledger?.ledgerPlaces()
            ledgerRead = true
        }
        .task(id: shownID) { await recordShown(shownID) }
    }

    /// The device's history united with the ledger's 90 days (T-0307 R5); nil places - no session - leave it be.
    private func merged(_ deck: SurpriseDeck) -> SurpriseHistory {
        SurpriseHistoryMerge.merged(device: state.basis, ledger: ledgerPlaces, candidates: deck.candidates)
    }

    /// The place on the card once the ledger has answered (or there is none to ask); nil before.
    private var shownID: String? {
        guard ledgerRead, let deck = SurpriseDeck.bundled else { return nil }
        return deck.pick(history: merged(deck), at: now)?.candidateId
    }

    /// The shown place goes into the device history once a day, to the user store (T-0312) and, with a session, to
    /// the ledger with the place's own cell (T-0310 R7, P-PRIV-05).
    private func recordShown(_ id: String?) async {
        let today = SurpriseDeck.context(at: now).date
        guard let id, let deck = SurpriseDeck.bundled, let candidate = deck.byID[id],
              let next = state.showing(candidate, on: today)
        else { return }
        state = next
        SurpriseShownLog.save(state.history.shown, today: today)
        await ledger?.recordShown(candidate)
    }

    private func content(pick: SurprisePick, candidate: SurpriseCandidate,
                         placeClass: SurprisePlaceClass) -> some View {
        VStack(alignment: .leading, spacing: 8) {
            Label {
                Text(placeClass.label)
                    .foregroundStyle(DesignTokens.fgMuted)
            } icon: {
                Image(systemName: Self.symbol(placeClass))
                    .foregroundStyle(DesignTokens.primary)
            }
            .font(.caption.weight(.semibold))
            .accessibilityIdentifier("surprise.class")

            Text(pick.name)
                .font(.title3.weight(.semibold))
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityAddTraits(.isHeader)
                .accessibilityIdentifier("surprise.name")

            Text(pick.reason.hook)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("surprise.hook")

            roundTrip(minutes: pick.reason.roundTripMinutes)

            if let line = pick.reason.goldenHourLine {
                Label {
                    Text(line)
                        .foregroundStyle(DesignTokens.fg)
                } icon: {
                    Image(systemName: "sun.horizon")
                        .foregroundStyle(DesignTokens.primary)
                }
                .font(.footnote)
                .accessibilityIdentifier("surprise.goldenHour")
            }

            if let failure {
                Text(failure)
                    .font(.footnote)
                    .foregroundStyle(DesignTokens.destructive)
                    .accessibilityIdentifier("surprise.failure")
            }

            Button {
                onOpenInMaps(candidate.coordinate)
            } label: {
                Text(Copy.openInAppleMaps)
                    .font(.headline)
                    .foregroundStyle(DesignTokens.onPrimary)
                    .frame(maxWidth: .infinity, minHeight: 44)
                    .background(
                        RoundedRectangle(cornerRadius: 12, style: .continuous)
                            .fill(DesignTokens.primary)
                    )
            }
            .buttonStyle(.plain)
            .accessibilityIdentifier("surprise.openInAppleMaps")

            SurpriseNotThis { reason in
                notThis(reason, pick: pick, candidate: candidate)
            }
        }
    }

    private func roundTrip(minutes: Int) -> some View {
        HStack(alignment: .firstTextBaseline, spacing: 6) {
            Image(systemName: "clock.arrow.circlepath")
                .foregroundStyle(DesignTokens.primary)
                .accessibilityHidden(true)
            Text("About \(minutes) min round trip from \(SurpriseOfflineReach.originName)")
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("surprise.roundTrip")
            Text(Copy.estimate)
                .font(.caption2.weight(.semibold))
                .foregroundStyle(DesignTokens.fgMuted)
                .padding(.horizontal, 6)
                .padding(.vertical, 2)
                .overlay(Capsule().strokeBorder(DesignTokens.border, lineWidth: 1))
                .fixedSize()
                .accessibilityIdentifier("surprise.estimate")
        }
        .font(.subheadline)
    }

    private var empty: some View {
        VStack(alignment: .leading, spacing: 8) {
            Text(Copy.empty)
                .font(.subheadline)
                .foregroundStyle(DesignTokens.fg)
                .fixedSize(horizontal: false, vertical: true)
                .accessibilityIdentifier("surprise.empty")
            if !state.history.feedback.isEmpty {
                Button(Copy.startOver) {
                    state = state.startingOver()
                }
                    .font(.subheadline.weight(.semibold))
                    .foregroundStyle(DesignTokens.fg)
                    .frame(minHeight: 44)
                    .accessibilityIdentifier("surprise.startOver")
            }
        }
    }

    /// The pick is set aside for the reason given (T-0253's four rules) and the card picks again.
    private func notThis(_ reason: SurpriseFeedback.Reason, pick: SurprisePick, candidate: SurpriseCandidate) {
        let feedback = SurpriseFeedback(candidateId: candidate.id, category: candidate.category,
                                        roundTripMinutes: pick.reason.roundTripMinutes,
                                        date: SurpriseDeck.context(at: now).date, reason: reason)
        state = state.declining(feedback)
    }

    static func symbol(_ placeClass: SurprisePlaceClass) -> String {
        switch placeClass {
        case .viewpoint: return "binoculars"
        case .peak: return "mountain.2"
        case .waterfall: return "drop"
        case .beach: return "beach.umbrella"
        case .trailhead: return "figure.hiking"
        case .museum: return "building.columns"
        case .cafe: return "cup.and.saucer"
        case .garden: return "leaf"
        case .park: return "tree"
        case .town: return "storefront"
        }
    }

    private enum Copy {
        static let openInAppleMaps = "Open in Apple Maps"
        static let estimate = "estimate · no traffic data"
        static let empty = "Nothing within reach right now."
        static let startOver = "Start over"
    }
}
