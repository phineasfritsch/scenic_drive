import Testing
@testable import ScenicKit

/// P-PRIV-05 (T-0320 R9): learned speeds have no Codable conformance - none of the types that hold or carry a
/// learned ratio can be handed to an encoder or built by a decoder, wherever in the linked image a conformance sits.
@Suite("learned speeds stay on the device (T-0320)") struct LearnedSpeedsPrivacyTests {
    @Test("no learned-speed type is Encodable or Decodable")
    func noLearnedTypeIsCodable() {
        let types: [(String, Any.Type)] = [("LearnedCorridorSpeeds", LearnedCorridorSpeeds.self),
                                          ("CorridorSlot", CorridorSlot.self),
                                          ("CorridorRatio", CorridorRatio.self),
                                          ("RetimedRoute", RetimedRoute.self),
                                          ("CorridorClock", CorridorClock.self),
                                          ("CorridorSlotRow", CorridorSlotRow.self),
                                          ("[CorridorSlotRow]", [CorridorSlotRow].self),
                                          ("CorridorLearner", CorridorLearner.self),
                                          ("RetimingPlanner", RetimingPlanner.self),
                                          ("[CorridorSlot: CorridorRatio]", [CorridorSlot: CorridorRatio].self)]
        for (name, type) in types {
            #expect(!(type is Encodable.Type), "\(name) is Encodable")
            #expect(!(type is Decodable.Type), "\(name) is Decodable")
        }
    }
}
