import Foundation
import PlaceStore

/// The bytes in every slot of one corpus directory (T-0300 O4), nil where no file is. The stage and activation
/// tables compare a WHOLE directory to the state a row expects, so a slot nobody looked at cannot hide a write.
struct CorpusSlotState: Equatable, CustomStringConvertible {
    var active: Data?
    var pending: Data?
    var previous: Data?
    var staging: Data?

    init(active: Data?, pending: Data? = nil, previous: Data? = nil, staging: Data? = nil) {
        self.active = active
        self.pending = pending
        self.previous = previous
        self.staging = staging
    }

    init(reading slots: CorpusSlots) {
        active = try? Data(contentsOf: slots.active)
        pending = try? Data(contentsOf: slots.pending)
        previous = try? Data(contentsOf: slots.previous)
        staging = try? Data(contentsOf: slots.staging)
    }

    /// Writes this state into `slots`: every non-nil slot as a file (the tmp/ directory created when staging is),
    /// and nothing for a nil one.
    func write(to slots: CorpusSlots) throws {
        try FileManager().createDirectory(at: slots.staging.deletingLastPathComponent(),
                                          withIntermediateDirectories: true)
        for (data, url) in [(active, slots.active), (pending, slots.pending), (previous, slots.previous),
                            (staging, slots.staging)] {
            if let data { try data.write(to: url) }
        }
    }

    var description: String {
        func show(_ d: Data?) -> String {
            guard let d else { return "-" }
            return String(data: d, encoding: .utf8).map { "\"\($0)\"" } ?? "\(d.count) bytes"
        }
        return "active \(show(active)) pending \(show(pending)) previous \(show(previous)) staging \(show(staging))"
    }

    /// A fresh corpus directory per row, so no row reads a file another row left.
    static func scratch() throws -> CorpusSlots {
        let dir = FileManager().temporaryDirectory.appendingPathComponent("corpus-ota-\(UUID().uuidString)",
                                                                          isDirectory: true)
        try FileManager().createDirectory(at: dir, withIntermediateDirectories: true)
        return CorpusSlots(directory: dir)
    }
}
