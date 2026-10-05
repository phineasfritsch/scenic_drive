import Foundation

/// One row of a drive's menu (T-0246): how many minutes it adds over the fastest way, how much good road it buys,
/// its roads, the Apple Maps URL `ops/plan --menu` printed for it, and the line the map draws for it.
///
/// Every field is read from the bundle `ops/lib/make-menu-bundle.py` writes from the CLI's stdout; nothing here
/// recomputes a route, a duration or a URL. `SaddlePeakMenuBundleTests` binds each field to the CLI's printed
/// output by exact equality.
public struct DriveMenuRow: Decodable, Equatable, Sendable {
    /// The CLI's `extra=+N.Nmin`: the ETA over the fastest row, in minutes, already rounded UP to a tenth.
    public let extraMinutes: Double
    /// The CLI's `fun_km=`: kilometres of road scored 6 or better on this row.
    public let funKm: Double
    /// The CLI's `roads=`, in driving order.
    public let roads: [String]
    /// The CLI's `URL i` line's URL, exactly as printed.
    public let appleMapsURL: String
    /// The row's road line, `[longitude, latitude]` pairs, Douglas-Peucker-simplified by the script.
    public let line: [[Double]]

    enum CodingKeys: String, CodingKey {
        case extraMinutes = "extra_minutes"
        case funKm = "fun_km"
        case roads
        case appleMapsURL = "apple_maps_url"
        case line
    }

    /// The whole minutes the chip shows: the extra rounded UP, so a chip never promises less time than the row
    /// takes (P-SAFE-04; ruling R3 in T-0246's Log - "+17 min" over 17.1 would be 63 ms short of the real ETA).
    public var displayedMinutes: Int {
        Int(extraMinutes.rounded(.up))
    }

    /// The chip's calm label: `Fastest` for the row that adds nothing, else `+N min`.
    public var chipLabel: String {
        displayedMinutes == 0 ? "Fastest" : "+\(displayedMinutes) min"
    }

    /// The good road beside the minutes, at the one decimal the CLI prints - in integer tenths, so no locale
    /// can turn the point into a comma.
    public var goodRoadLabel: String {
        let tenths = Int((funKm * 10).rounded())
        return "\(tenths / 10).\(tenths % 10) km good road"
    }

    /// The roads as one sentence, for the sheet's road line and the failure card's paste.
    public var roadList: String {
        roads.joined(separator: ", ") + "."
    }

    /// The URL this row hands to Apple Maps: the printed string parsed, never rebuilt.
    public func url() throws -> URL {
        guard let url = URL(string: appleMapsURL), url.scheme == "https", url.host == "maps.apple.com" else {
            throw HandoffError.notAMapsURL(appleMapsURL)
        }
        return url
    }
}
