import Foundation

/// A drive's menu (T-0246): the rows `ops/plan --menu` printed for the trip, as `ops/lib/make-menu-bundle.py`
/// bundled them - spare minutes traded for a better road, one chip per row.
///
/// ## What the app does with it
///
/// The home sheet shows one chip per row; the selected row's line is drawn in the route colour and the others
/// muted; the button hands the selected row's own URL to Apple Maps (`HandoffDrive.url(row:)`). A selection the
/// menu does not have - none yet, or an index past the rows - is the bundle's `default_row`, which the script
/// ruled (the one row over Saddle Peak Road). The app never chooses a row of its own.
///
/// ## Why the box is the MENU's
///
/// `geoJSON(selected:)` writes the menu's `bbox` - the extent of every row, computed by the script from the
/// positions it wrote - on whichever row is selected, so the camera frames all the choices and a chip tap moves
/// no camera. `SaddlePeakMenuBundleTests` refuses a bundle whose `bbox` is not every row's extent.
public struct DriveMenu: Decodable, Equatable, Sendable {
    /// The `ops/plan` arguments the bundle was printed by, and everything they printed, line for line.
    public let command: [String]
    public let printed: [String]
    /// The Douglas-Peucker tolerance the lines were simplified at, in metres.
    public let toleranceM: Double
    /// The row shown before anyone taps a chip.
    public let defaultRow: Int
    /// `[west, south, east, north]` over every row's line.
    public let bbox: [Double]
    public let rows: [DriveMenuRow]

    enum CodingKeys: String, CodingKey {
        case command, printed, bbox, rows
        case toleranceM = "tolerance_m"
        case defaultRow = "default_row"
    }

    /// The menu in `data`, or a thrown `HandoffError.notAMenu` naming what is missing: no rows, a default row the
    /// menu does not have, a box that is not four numbers, or a line that is not two positions or more.
    public init(data: Data) throws {
        let menu: DriveMenu
        do {
            menu = try JSONDecoder().decode(DriveMenu.self, from: data)
        } catch {
            throw HandoffError.notAMenu("\(error)")
        }
        guard !menu.rows.isEmpty, menu.rows.indices.contains(menu.defaultRow) else {
            throw HandoffError.notAMenu("default_row \(menu.defaultRow) of \(menu.rows.count) row(s)")
        }
        guard menu.bbox.count == 4, menu.bbox.allSatisfy(\.isFinite) else {
            throw HandoffError.notAMenu("bbox \(menu.bbox)")
        }
        for (index, row) in menu.rows.enumerated()
        where row.line.count < 2 || !row.line.allSatisfy({ $0.count == 2 && $0.allSatisfy(\.isFinite) }) {
            throw HandoffError.notAMenu("row \(index) carries no line")
        }
        self = menu
    }

    /// The row a selection names, or the default row when it names none the menu has.
    public func index(selected: Int?) -> Int {
        guard let selected, rows.indices.contains(selected) else { return defaultRow }
        return selected
    }

    public func row(selected: Int?) -> DriveMenuRow {
        rows[index(selected: selected)]
    }

    /// The selected row's line: a FeatureCollection with one LineString and the menu's `bbox`.
    public func geoJSON(selected: Int?) -> Data {
        collection(of: [row(selected: selected)])
    }

    /// Every other row's line, one LineString each, in row order - the muted lines under the selected one.
    public func mutedGeoJSON(selected: Int?) -> Data {
        let chosen = index(selected: selected)
        return collection(of: rows.indices.filter { $0 != chosen }.map { rows[$0] })
    }

    private func collection(of drawn: [DriveMenuRow]) -> Data {
        let features: [[String: Any]] = drawn.map { row in
            ["type": "Feature", "properties": [String: Any](),
             "geometry": ["type": "LineString", "coordinates": row.line]]
        }
        let doc: [String: Any] = ["type": "FeatureCollection", "bbox": bbox, "features": features]
        return (try? JSONSerialization.data(withJSONObject: doc, options: [.sortedKeys])) ?? Data()
    }
}
