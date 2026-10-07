import Foundation
import PlaceStore
import ScenicKit

/// The user store behind the Saved list (T-0306): Application Support/user.sqlite, a file of its own that an OTA
/// corpus replacement never touches (T-0290 R1). Everything here stays on the device.
enum SavedDriveShelf {
    static let fileName = "user.sqlite"

    /// Opened on first use and kept; nil when the file would not open, and the Saved list is then simply empty.
    static let store: SavedDriveStore? = {
        guard let folder = try? FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask,
                                                        appropriateFor: nil, create: true) else { return nil }
        return try? SavedDriveStore(path: folder.appendingPathComponent(fileName).path)
    }()

    /// Keeps `draft` (R2): the T-0290 value through PlaceStore's refusing gate, placed against the bundled corpus by
    /// the shipped resolver (nearest within 25 m, else it needs a re-plan), then stored. False when anything refused.
    static func save(_ draft: SavedDraft) -> Bool {
        guard let store else { return false }
        do {
            var drive = try SavedDrive.unresolved(name: draft.name,
                                                  points: draft.points.map { (latitude: $0.latitude, longitude: $0.longitude) },
                                                  lambda: draft.lambda, budgetMinutes: draft.budgetMinutes,
                                                  createdAt: draft.createdAt)
            if let corpus = PlanPlaceSearch.store {
                drive = try SavedDriveResolver.resolve(drive, against: corpus)
            }
            _ = try store.save(drive)
            return true
        } catch {
            return false
        }
    }

    /// The saved drives as the list holds them: the name, the budget, the re-plan flag and the two saved ends.
    static func rows() -> [SavedRow] {
        guard let store, let drives = try? store.list() else { return [] }
        return drives.compactMap { drive in
            guard let id = drive.id else { return nil }
            let ends = drive.segments.map { Coordinate(latitude: $0.midpoint.latitude, longitude: $0.midpoint.longitude) }
            return SavedRow(id: id, name: drive.name, createdAt: drive.createdAt, needsReplan: drive.needsReplan,
                            start: ends.first, end: ends.last, budgetMinutes: drive.budgetMinutes)
        }
    }

    /// The list's edit, handed to the store.
    static func apply(_ edit: SavedEdit) {
        guard let store else { return }
        switch edit {
        case .rename(let id, let name): try? store.rename(id: id, to: name)
        case .delete(let id): try? store.delete(id: id)
        }
    }

    /// The named corpus places within `SavedReplay.reach` of `point` on each axis - a lookup on the device.
    static func places(near point: Coordinate) -> [PlanPlace] {
        guard let corpus = PlanPlaceSearch.store else { return [] }
        let reach = SavedReplay.reach
        let box = BoundingBox(minLon: point.longitude - reach, minLat: point.latitude - reach,
                              maxLon: point.longitude + reach, maxLat: point.latitude + reach)
        guard let places = try? corpus.places(in: box) else { return [] }
        return places.compactMap { place in
            guard let name = place.name else { return nil }
            return PlanPlace(id: place.placeID, name: name,
                             coordinate: Coordinate(latitude: Double(place.latE7) / 10_000_000,
                                                    longitude: Double(place.lonE7) / 10_000_000))
        }
    }
}
