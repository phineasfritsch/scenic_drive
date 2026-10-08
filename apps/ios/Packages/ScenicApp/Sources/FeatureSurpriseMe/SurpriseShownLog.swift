import Foundation
import PlaceStore
import ScenicKit

/// The card's bridge to the user store's Surprise history (T-0312 R8): Application Support/user.sqlite, the file
/// SavedDriveShelf keeps the saved drives in. Every failure - no folder, a refused file, a busy write - answers
/// nothing and the card keeps its in-memory history, T-0310's behaviour: losing the disk copy never blocks a pick.
@MainActor
enum SurpriseShownLog {
    static let fileName = "user.sqlite"

    static let store: SurpriseShownStore? = {
        guard let folder = try? FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                        appropriateFor: nil, create: true) else { return nil }
        return try? SurpriseShownStore(path: folder.appendingPathComponent(fileName).path)
    }()

    /// Every stored entry as the card's history holds it; a row whose category this build does not know is dropped.
    static func load() -> [SurpriseHistory.Shown] {
        ((try? store?.list()) ?? []).compactMap { record in
            guard let category = SurpriseCategory(rawValue: record.category) else { return nil }
            return SurpriseHistory.Shown(candidateId: record.placeID, category: category, corridor: record.corridor,
                                         date: SurpriseShownDay.date(record.day))
        }
    }

    /// Writes every shown entry (idempotent by place and day) and prunes what the pick no longer reads (R3, R6).
    static func save(_ shown: [SurpriseHistory.Shown], today: CivilDate) {
        let records = shown.map { entry in
            SurpriseShownRecord(placeID: entry.candidateId, category: entry.category.rawValue,
                                corridor: entry.corridor, day: SurpriseShownDay.number(entry.date))
        }
        _ = try? store?.record(records, keepingFrom: SurpriseShownDay.oldestKept(today: today))
    }
}
