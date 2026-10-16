import Foundation
import ScenicKit

/// A test's address search (T-0362 A6): records every call's query and bias and answers `answer`.
actor RecordingPlaceSearch: PlaceSearching {
    let answer: PlaceSearchAnswer
    private(set) var calls: [String] = []
    private(set) var biases: [Coordinate?] = []

    init(answer: PlaceSearchAnswer) {
        self.answer = answer
    }

    func searchPlaces(_ query: String, near: Coordinate?) -> PlaceSearchAnswer {
        calls.append(query)
        biases.append(near)
        return answer
    }
}
