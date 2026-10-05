#if canImport(GRDB)
import PlaceStore
import XCTest

/// `PlaceStore.search(query:limit:)` over a corpus the shipping `python -m etl.corpus` built from
/// services/etl/tests/fixtures/corpus_extract_places.json. Every expected row is a TYPED literal: place_id is
/// segid.place_id's value for the (osm_type, osm_id) pair, the e7 pair is the fixture's degrees x 1e7 - so
/// a reader that returned the wrong row, the wrong order or the wrong column fails by exact equality.
///
/// The three Mulholland place_ids sort 1002 < 1003 < 1001, so the bm25 order (1, 2, 3 tokens) is neither
/// ascending nor descending place_id (T-0254 ruling R4).
final class PlaceStoreSearchTests: XCTestCase {
    static let mulholland = Place(placeID: 5_174_896_685_818_850_037, osmType: "n", osmID: 1001, cls: "viewpoint",
                                  name: "Mulholland", lonE7: -1_184_103_000, latE7: 341_281_000)
    static let mulhollandDam = Place(placeID: 5_174_893_387_283_965_404, osmType: "n", osmID: 1002,
                                     cls: "viewpoint", name: "Mulholland Dam", lonE7: -1_183_256_000,
                                     latE7: 341_257_000)
    static let mulhollandOverlook = Place(placeID: 5_174_894_486_795_593_615, osmType: "n", osmID: 1003,
                                          cls: "viewpoint", name: "Mulholland Scenic Overlook",
                                          lonE7: -1_183_694_000, latE7: 341_308_000)
    static let cafe = Place(placeID: 5_174_891_188_260_708_982, osmType: "n", osmID: 1004, cls: "cafe",
                            name: "Café Tropical", lonE7: -1_182_729_000, latE7: 340_872_000)
    static let rockStore = Place(placeID: 5_174_892_287_772_337_193, osmType: "n", osmID: 1005, cls: "cafe",
                                 name: "Rock Store", lonE7: -1_187_539_000, latE7: 341_201_000)
    static let saddlePeak = Place(placeID: 5_739_051_218_924_217_510, osmType: "w", osmID: 2001,
                                  cls: "restaurant", name: "Saddle Peak Lodge", lonE7: -1_186_597_000,
                                  latE7: 340_959_000)
    static let nearys = Place(placeID: 5_174_890_088_749_080_771, osmType: "n", osmID: 1007, cls: "pub",
                              name: "Neary's Pub", lonE7: -1_184_912_000, latE7: 340_195_000)
    static let malibuCreek = Place(placeID: 3_508_864_315_908_228_945, osmType: "r", osmID: 3001, cls: "park",
                                   name: "Malibu Creek State Park", lonE7: -1_187_313_000, latE7: 340_985_000)

    private func store() throws -> PlaceStore {
        try PlaceStore(path: CorpusFixture.build(extract: CorpusFixture.placesExtract).path)
    }

    func testSearchRanksByBM25NotByPlaceID() throws {
        XCTAssertEqual(try store().search(query: "mulholland", limit: 10),
                       [Self.mulholland, Self.mulhollandDam, Self.mulhollandOverlook])
    }

    /// A one-letter type-ahead ties bm25 exactly: "p" ties Neary's Pub and Saddle Peak Lodge (3 tokens, one
    /// p-token each), "s" ties Neary's Pub, Mulholland Scenic Overlook and Saddle Peak Lodge. The tie-break is
    /// ascending place_id (ruling R4): 5_174_890_... < 5_174_894_... < 5_739_051_....
    func testSearchBreaksABM25TieByAscendingPlaceID() throws {
        let store = try store()
        XCTAssertEqual(try store.search(query: "p", limit: 10), [Self.nearys, Self.saddlePeak, Self.malibuCreek])
        XCTAssertEqual(try store.search(query: "s", limit: 10),
                       [Self.rockStore, Self.nearys, Self.mulhollandOverlook, Self.saddlePeak, Self.malibuCreek])
    }

    func testSearchMatchesEveryTokenAsAPrefixForTypeAhead() throws {
        let store = try store()
        XCTAssertEqual(try store.search(query: "mulh", limit: 10),
                       [Self.mulholland, Self.mulhollandDam, Self.mulhollandOverlook])
        XCTAssertEqual(try store.search(query: "sadd pe", limit: 10), [Self.saddlePeak])
        XCTAssertEqual(try store.search(query: "mulholland d", limit: 10), [Self.mulhollandDam])
        XCTAssertEqual(try store.search(query: "near", limit: 10), [Self.nearys])
    }

    func testSearchFoldsCaseAndDiacritics() throws {
        let store = try store()
        XCTAssertEqual(try store.search(query: "CAFE", limit: 10), [Self.cafe])
        XCTAssertEqual(try store.search(query: "café", limit: 10), [Self.cafe])
        XCTAssertEqual(try store.search(query: "cafe\u{0301} tropica\u{0301}l", limit: 10), [Self.cafe])
    }

    func testSearchHonoursLimit() throws {
        let store = try store()
        XCTAssertEqual(try store.search(query: "mulholland", limit: 2), [Self.mulholland, Self.mulhollandDam])
        XCTAssertEqual(try store.search(query: "mulholland", limit: 0), [])
        XCTAssertEqual(try store.search(query: "mulholland", limit: -1), [])
    }

    /// Only `places.name` is indexed: a class is not a name, and the unnamed viewpoint (n/1006) is in places
    /// but can never be typed.
    func testSearchIndexesNamesOnly() throws {
        let store = try store()
        XCTAssertEqual(try store.search(query: "viewpoint", limit: 10), [])
        XCTAssertEqual(try store.search(query: "park", limit: 10), [Self.malibuCreek])
        XCTAssertEqual(try store.search(query: "pub", limit: 10), [Self.nearys])
    }

    /// A user string is never FTS5 syntax (ruling R6). Each raw string here would either throw an FTS5 syntax
    /// error or select a DIFFERENT set: `name:rock` is a column filter, `rock OR malibu` a disjunction,
    /// `NEAR(mulholland dam)` a proximity group, `AND` and `(mulholland` parse errors.
    func testSearchNeverPassesTheUserStringAsFTS5Syntax() throws {
        let store = try store()
        let cases: [(String, [Place])] = [
            ("rock\"store", [Self.rockStore]),
            ("\"Rock Store\"", [Self.rockStore]),
            ("name:rock", []),
            ("rock OR malibu", []),
            ("NEAR(mulholland dam)", []),
            ("AND", []),
            ("(mulholland", [Self.mulholland, Self.mulhollandDam, Self.mulhollandOverlook]),
            ("-rock", [Self.rockStore]),
            ("^saddle*", [Self.saddlePeak]),
            ("neary's", [Self.nearys]),
            ("saddle + peak", [Self.saddlePeak]),
        ]
        for (query, expected) in cases {
            XCTAssertEqual(try store.search(query: query, limit: 10), expected, "query \(query)")
        }
    }

    func testSearchWithNoTokenIsEmpty() throws {
        let store = try store()
        for query in ["", "   ", "\"", "*", "\"\"*", "-", "()", "\u{0301}", "😀"] {
            XCTAssertEqual(try store.search(query: query, limit: 10), [], "query \(query)")
        }
    }
}
#endif
