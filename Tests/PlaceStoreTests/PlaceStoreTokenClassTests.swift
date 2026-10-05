#if canImport(GRDB)
import PlaceStore
import XCTest

/// Every Unicode general category `PlaceSearchQuery` treats as a token character (T-0254 ruling R6: L*, N*,
/// Co; Mn is PlaceStoreSearchTests' decomposed-mark case) is typed through the shipping `search(query:limit:)`
/// against a corpus `python -m etl.corpus` built from services/etl/tests/fixtures/corpus_extract_token_classes.json.
///
/// Each query is made ONLY of scalars of its category, so a token class that became a separator leaves no run
/// at all and the search returns [] - while unicode61 indexes every one of these scalars as a token character
/// (measured on sqlite 3.40.1 and 3.45.1, T-0254 Log). Every expected row is a typed literal: place_id is
/// segid.place_id for the (osm_type, osm_id) pair, the e7 pair is the fixture's degrees x 1e7.
final class PlaceStoreTokenClassTests: XCTestCase {
    static let etoile = Place(placeID: 5_170_868_075_213_841_833, osmType: "n", osmID: 4001, cls: "viewpoint",
                              name: "\u{00C9}toile Overlook", lonE7: -1_183_001_000, latE7: 341_001_000)
    static let dzakovo = Place(placeID: 5_170_864_776_678_957_200, osmType: "n", osmID: 4002, cls: "viewpoint",
                               name: "\u{01C5}akovo Bridge", lonE7: -1_183_002_000, latE7: 341_002_000)
    static let iolani = Place(placeID: 5_170_865_876_190_585_411, osmType: "n", osmID: 4003, cls: "viewpoint",
                              name: "\u{02BB}Iolani Lookout", lonE7: -1_183_003_000, latE7: 341_003_000)
    static let tofuHouse = Place(placeID: 5_170_871_373_748_726_466, osmType: "n", osmID: 4004,
                                 cls: "restaurant", name: "\u{BD81}\u{CC3D}\u{B3D9} \u{C21C}\u{B450}\u{BD80}",
                                 lonE7: -1_183_009_000, latE7: 340_631_000)
    static let route66 = Place(placeID: 5_170_872_473_260_354_677, osmType: "n", osmID: 4005, cls: "restaurant",
                               name: "Route 66 Diner", lonE7: -1_183_005_000, latE7: 341_005_000)
    static let gateXII = Place(placeID: 5_170_869_174_725_470_044, osmType: "n", osmID: 4006, cls: "viewpoint",
                               name: "Gate \u{216B} Trailhead", lonE7: -1_183_006_000, latE7: 341_006_000)
    static let mileHalf = Place(placeID: 5_170_870_274_237_098_255, osmType: "n", osmID: 4007, cls: "viewpoint",
                                name: "Mile \u{00BD} Marker", lonE7: -1_183_007_000, latE7: 341_007_000)
    static let archGrove = Place(placeID: 5_170_875_771_795_239_310, osmType: "n", osmID: 4008, cls: "viewpoint",
                                 name: "Arch \u{E000} Grove", lonE7: -1_183_008_000, latE7: 341_008_000)

    /// (category, query, the exact result). One row per token category of ruling R6.
    static let table: [(Unicode.GeneralCategory, String, [Place])] = [
        (.uppercaseLetter, "\u{00C9}TOILE", [etoile]),
        (.lowercaseLetter, "\u{00E9}toile", [etoile]),
        (.titlecaseLetter, "\u{01C5}", [dzakovo]),
        (.modifierLetter, "\u{02BB}", [iolani]),
        (.otherLetter, "\u{C21C}\u{B450}", [tofuHouse]),
        (.decimalNumber, "66", [route66]),
        (.letterNumber, "\u{216B}", [gateXII]),
        (.otherNumber, "\u{00BD}", [mileHalf]),
        (.privateUse, "\u{E000}", [archGrove]),
    ]

    func testSearchTypesEveryTokenCategory() throws {
        let store = try PlaceStore(path: CorpusFixture.build(extract: CorpusFixture.tokenClassesExtract).path)
        for (category, query, expected) in Self.table {
            XCTAssertTrue(query.unicodeScalars.allSatisfy { $0.properties.generalCategory == category },
                          "the \(category) query \(query) holds a scalar of another category")
            XCTAssertEqual(try store.search(query: query, limit: 10), expected, "\(category) query \(query)")
        }
    }
}
#endif
