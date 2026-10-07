import Foundation
import PlaceStore
import Testing

/// The verify step through the shipped entry point, `CorpusUpdater.stage` (T-0300 O6). Each row is a function of a
/// payload variant; the manifest hashes are python hashlib's (Log, O6), never this module's. Every row compares the
/// thrown error AND the whole corpus directory afterwards: a refused download leaves the active corpus and an
/// earlier pending file byte-identical and no staging file; an accepted one is renamed over pending.
struct CorpusStageTests {
    struct Payload {
        let bytes: Data
        let sha256: String
    }

    struct Row {
        let name: String
        let manifest: CorpusManifest
        let fetcher: FakeCorpusFetcher
        let error: CorpusUpdateError?
        let expected: CorpusSlotState
    }

    static let a = Payload(bytes: Data((0..<4096).map { UInt8(($0 * 7 + 3) % 256) }),
                           sha256: "7486da8f1e13943fae21a0b043f1e99640d7d8ebafb25266478b5cddae1272b5")
    static let b = Payload(bytes: Data([0x5a]),
                           sha256: "bbeebd879e1dff6918546dc0c179fdde505f2a21591c9a9c96e36b054ec5af83")
    static let oldActive = Data("OLD ACTIVE CORPUS".utf8)
    static let oldPending = Data("OLD PENDING CORPUS".utf8)
    static let before = CorpusSlotState(active: oldActive, pending: oldPending)

    static func manifest(_ p: Payload, bytes: Int? = nil) -> CorpusManifest {
        CorpusManifest(version: "20261006T000000Z", schemaVersion: PlaceStore.schemaVersion, minAppBuild: 1,
                       sha256: p.sha256, bytes: bytes ?? p.bytes.count)
    }

    static func rows(_ p: Payload) -> [Row] {
        let n = p.bytes.count
        var flipped = p.bytes
        flipped[n / 2] ^= 0x01
        func refused(_ name: String, _ m: CorpusManifest, _ served: Data, found: Int, hashMatches: Bool) -> Row {
            Row(name: name, manifest: m, fetcher: FakeCorpusFetcher(served: served),
                error: .verifyFailed(foundBytes: found, hashMatches: hashMatches), expected: before)
        }
        return [
            Row(name: "the exact bytes: renamed over pending", manifest: manifest(p),
                fetcher: FakeCorpusFetcher(served: p.bytes), error: nil,
                expected: CorpusSlotState(active: oldActive, pending: p.bytes)),
            refused("one byte changed", manifest(p), flipped, found: n, hashMatches: false),
            refused("truncated by one byte", manifest(p), p.bytes.dropLast(), found: n - 1, hashMatches: false),
            refused("one extra trailing byte", manifest(p), p.bytes + [0x00], found: n + 1, hashMatches: false),
            refused("the right hash, manifest bytes + 1", manifest(p, bytes: n + 1), p.bytes, found: n,
                    hashMatches: true),
            refused("the right hash, manifest bytes - 1", manifest(p, bytes: n - 1), p.bytes, found: n,
                    hashMatches: true),
            Row(name: "the download fails part-way", manifest: manifest(p),
                fetcher: FakeCorpusFetcher(served: p.bytes.prefix(n / 2 + 1), fails: true), error: nil,
                expected: before),
        ]
    }

    static func run(_ p: Payload) async throws {
        for row in rows(p) {
            let slots = try CorpusSlotState.scratch()
            try before.write(to: slots)
            let activeHash = try SHA256.hex(ofFileAt: slots.active)
            let updater = CorpusUpdater(directory: slots.directory, drives: DriveSessionLock(), validate: { _ in })
            var thrown: (any Error)?
            do {
                try await updater.stage(row.manifest, fetcher: row.fetcher)
            } catch {
                thrown = error
            }
            if row.fetcher.fails {
                #expect((thrown as? CocoaError)?.code == .fileReadUnknown, "\(row.name): \(String(describing: thrown))")
            } else {
                #expect(thrown as? CorpusUpdateError == row.error, "\(row.name): \(String(describing: thrown))")
                #expect((thrown == nil) == (row.error == nil), "\(row.name)")
            }
            #expect(CorpusSlotState(reading: slots) == row.expected, "\(row.name)")
            #expect(try SHA256.hex(ofFileAt: slots.active) == activeHash, "\(row.name): the active corpus moved")
        }
    }

    @Test func verifyTablePayloadA() async throws {
        try await Self.run(Self.a)
    }

    @Test func verifyTablePayloadB() async throws {
        try await Self.run(Self.b)
    }

    @Test func noStageRowIgnoresItsPayload() {
        let x = Self.rows(Self.a)
        let y = Self.rows(Self.b)
        #expect(x.map(\.name) == y.map(\.name))
        #expect(x.count == 7)
        for (r, s) in zip(x, y) {
            #expect(r.fetcher.served != s.fetcher.served || r.manifest != s.manifest, "\(r.name)")
            #expect(r.manifest != s.manifest, "\(r.name)")
        }
    }
}
