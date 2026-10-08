import Foundation
import PlaceStore
import ScenicKit

/// The bundled corpus, read once through PlaceStore and mapped for the selector (T-0273 R1-R3, R6).
///
/// The fallback is the only corpus on the device today; when a downloaded corpus exists it is preferred and the
/// fallback's frozen built_at is never presented as fresh (T-0270 F7) - nothing here shows a date.
struct SurpriseDeck: Sendable {
    let candidates: [SurpriseCandidate]
    let byID: [String: SurpriseCandidate]
    let classes: [String: SurprisePlaceClass]
    let reach: SurpriseReach

    static let corpusName = "corpus-fallback"
    static let everywhere = BoundingBox(minLon: -180, minLat: -90, maxLon: 180, maxLat: 90)
    static let userId = "on-device"

    /// Read on first use and kept: the card is rebuilt on every home render, the corpus is not.
    static let bundled: SurpriseDeck? = load(bundle: .main)

    static func load(bundle: Bundle) -> SurpriseDeck? {
        guard let url = LaunchCorpus.url(fallback: bundle.url(forResource: corpusName, withExtension: "sqlite")
                ?? bundle.url(forResource: corpusName, withExtension: "sqlite", subdirectory: "Corpus")),
              let store = try? PlaceStore(path: url.path),
              let places = try? store.places(in: everywhere) else { return nil }
        var candidates: [SurpriseCandidate] = []
        var classes: [String: SurprisePlaceClass] = [:]
        for place in places {
            guard let candidate = SurprisePlaceMapping.candidate(placeID: place.placeID, cls: place.cls,
                                                                 name: place.name, lonE7: place.lonE7,
                                                                 latE7: place.latE7),
                  let placeClass = SurprisePlaceClass(rawValue: place.cls) else { continue }
            candidates.append(candidate)
            classes[candidate.id] = placeClass
        }
        let reach = SurpriseOfflineReach.reach(from: SurpriseOfflineReach.origin, to: candidates,
                                               budgetMinutes: SurpriseOfflineReach.budgetMinutes)
        return SurpriseDeck(candidates: candidates,
                            byID: Dictionary(candidates.map { ($0.id, $0) }, uniquingKeysWith: { first, _ in first }),
                            classes: classes, reach: reach)
    }

    /// Today, now, here: the device's own calendar and offset. No fire-weather feed exists, so redFlag is false.
    static func context(at now: Date, calendar: Calendar = .current) -> SurpriseContext {
        let parts = calendar.dateComponents(in: calendar.timeZone, from: now)
        return SurpriseContext(userId: userId,
                               date: CivilDate(year: parts.year ?? 1970, month: parts.month ?? 1, day: parts.day ?? 1),
                               departureMinute: (parts.hour ?? 0) * 60 + (parts.minute ?? 0),
                               utcOffsetMinutes: calendar.timeZone.secondsFromGMT(for: now) / 60,
                               redFlag: false)
    }

    func pick(history: SurpriseHistory, at now: Date) -> SurprisePick? {
        Surprise.pick(candidates: candidates, reach: reach, history: history, context: Self.context(at: now), seed: 0)
    }
}
