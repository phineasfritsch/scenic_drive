import Foundation

/// Where the corpus files live (T-0300 O4): every slot under ONE directory the caller supplies - the app passes its
/// Application Support URL; nothing here asks FileManager for a location.
public struct CorpusSlots: Equatable, Sendable {
    public let directory: URL

    public init(directory: URL) {
        self.directory = directory
    }

    /// The corpus PlaceStore opens.
    public var active: URL { directory.appendingPathComponent("corpus.sqlite") }
    /// A verified download waiting for the next cold launch.
    public var pending: URL { directory.appendingPathComponent("corpus-pending.sqlite") }
    /// The old active corpus, only while a swap is in progress: the undo slot.
    public var previous: URL { directory.appendingPathComponent("corpus-previous.sqlite") }
    /// A download in progress (the plan's "to tmp/").
    public var staging: URL {
        directory.appendingPathComponent("tmp", isDirectory: true).appendingPathComponent("corpus-staging.sqlite")
    }

    func exists(_ url: URL) -> Bool {
        FileManager().fileExists(atPath: url.path)
    }

    func remove(_ url: URL) {
        try? FileManager().removeItem(at: url)
    }

    /// Renames `source` over `destination` with rename(2): atomic, replacing what was there. Windows' rename
    /// refuses an existing target, so the dev box removes it first - never a device path (T-0300 O4).
    func replace(_ destination: URL, with source: URL) throws {
        #if os(Windows)
        let files = FileManager()
        if files.fileExists(atPath: destination.path) {
            try files.removeItem(at: destination)
        }
        try files.moveItem(at: source, to: destination)
        #else
        guard rename(source.path, destination.path) == 0 else {
            throw CorpusUpdateError.renameFailed(from: source.lastPathComponent, to: destination.lastPathComponent)
        }
        #endif
    }
}
