import Foundation
import ScenicKit
import Testing

/// T-0362 A6 (R6, R7): PlaceSearchSubmit - the plan sheet's one path to the address search - asks the searcher exactly
/// once per submit with the query as typed and the chosen start's coordinate (else the destination's, else none) as the
/// bias, and nothing for a blank submit.
@Suite("PlaceSearchSubmitTests") struct PlaceSearchSubmitTests {
    static let start = PlanPlace(id: 7, name: "Santa Monica Pier", coordinate: Coordinate(latitude: 34.0083, longitude: -118.4988))
    static let end = PlanPlace(id: -42, name: "Topanga", coordinate: Coordinate(latitude: 34.0676, longitude: -118.5957))
    static let found = PlaceSearchAnswer.places([end])

    @Test("one submit is exactly one call, with the query as typed, answered with the searcher's answer")
    func oneSubmitOneCall() async {
        let searcher = RecordingPlaceSearch(answer: Self.found)
        let answer = await PlaceSearchSubmit(searcher: searcher).submit(" Mulholland Dr ", start: Self.start, destination: nil)
        #expect(answer == Self.found)
        #expect(await searcher.calls == [" Mulholland Dr "])
        #expect(await searcher.biases == [Self.start.coordinate])
    }

    @Test("three submits are three calls - never fewer, never more")
    func eachSubmitOneCall() async {
        let searcher = RecordingPlaceSearch(answer: Self.found)
        let submit = PlaceSearchSubmit(searcher: searcher)
        for query in ["a", "a", "b"] { _ = await submit.submit(query, start: nil, destination: nil) }
        #expect(await searcher.calls == ["a", "a", "b"])
    }

    @Test("a blank submit asks nothing", arguments: ["", " ", "\n\t", "\u{3000}"])
    func blank(query: String) async {
        let searcher = RecordingPlaceSearch(answer: Self.found)
        let answer = await PlaceSearchSubmit(searcher: searcher).submit(query, start: Self.start, destination: Self.end)
        #expect(answer == nil)
        #expect(await searcher.calls.isEmpty)
    }

    @Test("the bias is the start, else the destination, else none")
    func bias() async {
        var biases: [Coordinate?] = []
        for (start, end) in [(Self.start, Self.end), (Self.start, nil), (nil, Self.end), (nil, nil)] as [(PlanPlace?, PlanPlace?)] {
            let searcher = RecordingPlaceSearch(answer: Self.found)
            _ = await PlaceSearchSubmit(searcher: searcher).submit("x", start: start, destination: end)
            biases += await searcher.biases
        }
        #expect(biases == [Self.start.coordinate, Self.start.coordinate, Self.end.coordinate, nil])
    }

    @Test("a build with no search answers the unavailable copy and sends nothing")
    func noSearch() async {
        #expect(await NoPlaceSearch().searchPlaces("x", near: nil) == .notice(PlaceSearchAnswer.unavailableNotice))
    }
}
