import Foundation

/// The device's corpus OTA core (T-0300): decide from the publisher's manifest, verify a download into the pending
/// slot, and swap it in at a cold launch. The download itself is the app's `CorpusFetcher`; everything else is here,
/// on Foundation alone, so Linux and the Windows dev box run its tables.
///
/// Plan, Runtime lifecycles / OTA: "download only if schema_version == PlaceStore.schemaVersion && min_app_build <=
/// build; to tmp/, verify sha256, rename(2), activate at next cold launch (never while a Drive holds a connection)".
public struct CorpusUpdater: Sendable {
    public let slots: CorpusSlots
    public let drives: DriveSessionLock
    /// Throws when the file at the URL may not be opened as a corpus. In production, `PlaceStore(path:)`.
    private let validate: @Sendable (URL) throws -> Void

    /// `validate` decides whether a swapped-in corpus is kept; the tables pass a fake, the app the GRDB-only
    /// `init(directory:drives:)`.
    public init(directory: URL, drives: DriveSessionLock, validate: @escaping @Sendable (URL) throws -> Void) {
        self.slots = CorpusSlots(directory: directory)
        self.drives = drives
        self.validate = validate
    }

    #if canImport(GRDB)
    /// The production updater: a swapped-in corpus is kept only when the shipping `PlaceStore(path:)` opens it -
    /// application_id, schema_version and build_complete, the same gate every launch runs.
    public init(directory: URL, drives: DriveSessionLock) {
        self.init(directory: directory, drives: drives, validate: { url in _ = try PlaceStore(path: url.path) })
    }
    #endif

    /// What to do with the manifest the app fetched (T-0300 O2). `activeVersion` is the active corpus's
    /// `meta.corpus_version`, nil when there is none. Throws a `CorpusUpdateError` for a malformed manifest.
    public static func decide(manifestJSON: Data, appBuild: Int, activeVersion: String?) throws
        -> CorpusUpdateDecision {
        let manifest = try CorpusManifest.parse(manifestJSON)
        guard manifest.schemaVersion == PlaceStore.schemaVersion else {
            return .refusedSchemaVersion(manifest: manifest.schemaVersion, reader: PlaceStore.schemaVersion)
        }
        guard manifest.minAppBuild <= appBuild else {
            return .refusedAppBuild(minAppBuild: manifest.minAppBuild, build: appBuild)
        }
        if manifest.version == activeVersion {
            return .upToDate(version: manifest.version)
        }
        return .download(manifest)
    }

    /// Downloads into the staging slot and renames it over the pending slot only when its byte count AND its
    /// SHA-256 are the manifest's (T-0300 O6). Any failure deletes the staging file and rethrows; the active corpus
    /// and an earlier pending file are never touched by a failed stage.
    public func stage(_ manifest: CorpusManifest, fetcher: some CorpusFetcher) async throws {
        let staging = slots.staging
        try FileManager().createDirectory(at: staging.deletingLastPathComponent(), withIntermediateDirectories: true)
        slots.remove(staging)
        do {
            try await fetcher.fetch(manifest, to: staging)
            let found = try SHA256.digest(ofFileAt: staging)
            let hashMatches = found.hex == manifest.sha256
            guard found.count == manifest.bytes, hashMatches else {
                throw CorpusUpdateError.verifyFailed(foundBytes: found.count, hashMatches: hashMatches)
            }
            try slots.replace(slots.pending, with: staging)
        } catch {
            slots.remove(staging)
            throw error
        }
    }

    /// Called once when the app opens the store (T-0300 O7). Only a cold launch with no drive token alive touches
    /// the files: it first restores an interrupted swap's old corpus, then swaps pending -> active and keeps the
    /// result only if `validate` accepts it - otherwise the swap is undone and the pending file is gone.
    public func openForLaunch(isColdLaunch: Bool) -> CorpusActivation {
        guard isColdLaunch else {
            return slots.exists(slots.pending) ? .deferredWarmLaunch : .noPending
        }
        guard !drives.isHeld else {
            return slots.exists(slots.pending) ? .deferredDriveHeld : .noPending
        }
        if slots.exists(slots.previous) {
            try? slots.replace(slots.active, with: slots.previous)
        }
        guard slots.exists(slots.pending) else {
            return .noPending
        }
        let hadActive = slots.exists(slots.active)
        var movedOld = false
        do {
            if hadActive {
                try slots.replace(slots.previous, with: slots.active)
                movedOld = true
            }
            try slots.replace(slots.active, with: slots.pending)
            try validate(slots.active)
        } catch {
            slots.remove(slots.pending)
            if movedOld {
                slots.remove(slots.active)
                try? slots.replace(slots.active, with: slots.previous)
            } else if !hadActive {
                slots.remove(slots.active)
            }
            return .rejected
        }
        slots.remove(slots.previous)
        return .activated
    }
}
