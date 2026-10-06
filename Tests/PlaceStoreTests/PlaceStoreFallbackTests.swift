#if canImport(GRDB)
import Foundation
import PlaceStore
import XCTest

/// THE committed bundle file, apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite (T-0270 ruling F9), opened by
/// the shipping `PlaceStore.init` - so its application_id, schema_version and build_complete pass the device's
/// own gate - and searched by prefix. Every expected row is a typed literal read out of that file with
/// `search`'s SQL and quoted in the task Log before this test was written: a peak, a beach (a relation) and a
/// viewpoint, from the classes ruling F2 keeps whole.
final class PlaceStoreFallbackTests: XCTestCase {
    static let committed = CorpusFixture.root.appendingPathComponent("apps/ios/ScenicDrive/Corpus/corpus-fallback.sqlite")

    static let saddlePeak = Place(placeID: 8_789_912_370_140_821_739, osmType: "n", osmID: 358_796_572, cls: "peak",
                                  name: "Saddle Peak", lonE7: -1_186_550_579, latE7: 340_780_264)
    static let zumaBeach = Place(placeID: 161_142_772_170_980_305, osmType: "r", osmID: 6_170_634, cls: "beach",
                                 name: "Zuma Beach", lonE7: -1_188_273_532, latE7: 340_188_704)
    static let zumaRidge = Place(placeID: 9_209_992_011_737_221_183, osmType: "n", osmID: 11_229_801_355,
                                 cls: "trailhead", name: "Zuma Ridge", lonE7: -1_188_181_430, latE7: 340_340_341)
    static let zumaCanyonTrail = Place(placeID: 9_178_414_037_781_245_688, osmType: "n", osmID: 11_229_792_403,
                                       cls: "trailhead", name: "Zuma Canyon Trail", lonE7: -1_188_122_926,
                                       latE7: 340_317_681)
    static let inspiration1 = Place(placeID: 56_338_661_075_490_828, osmType: "n", osmID: 1_350_996_499,
                                    cls: "viewpoint", name: "Inspiration Point", lonE7: -1_189_428_330,
                                    latE7: 341_164_322)
    static let inspiration2 = Place(placeID: 1_282_017_580_421_293_454, osmType: "n", osmID: 12_640_140_401,
                                    cls: "viewpoint", name: "Inspiration Point", lonE7: -1_187_484_403,
                                    latE7: 341_780_677)
    static let inspiration3 = Place(placeID: 1_912_874_055_470_411_436, osmType: "n", osmID: 8_188_304_240,
                                    cls: "viewpoint", name: "Inspiration Point", lonE7: -1_183_488_967,
                                    latE7: 341_067_591)

    private func store() throws -> PlaceStore {
        try PlaceStore(path: Self.committed.path)
    }

    func testTheCommittedFallbackPassesTheReadersGateAsLA() throws {
        XCTAssertEqual(try store().meta(),
                       CorpusMeta(schemaVersion: PlaceStore.schemaVersion, minAppBuild: 1, region: "la",
                                  corpusVersion: "20261006T000000Z", builtAt: "2026-10-06T00:00:00Z",
                                  attribution: "© OpenStreetMap contributors · Protomaps"))
    }

    func testTheCommittedFallbackFindsSaddlePeakByPrefix() throws {
        XCTAssertEqual(try store().search(query: "saddle pea", limit: 10), [Self.saddlePeak])
    }

    func testTheCommittedFallbackFindsZumaBeachByPrefix() throws {
        XCTAssertEqual(try store().search(query: "zuma", limit: 10),
                       [Self.zumaBeach, Self.zumaRidge, Self.zumaCanyonTrail])
    }

    func testTheCommittedFallbackFindsInspirationPointByPrefix() throws {
        XCTAssertEqual(try store().search(query: "inspir", limit: 3),
                       [Self.inspiration1, Self.inspiration2, Self.inspiration3])
    }
}
#endif
