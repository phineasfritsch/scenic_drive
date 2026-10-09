import ScenicKit
import Testing

/// T-0334 A7: the offer card's words, compared WHOLE over the cross product budget x more time x back roads. Each
/// row's expected value is a function of its variant, so no row can ignore one.
@Suite("PlanOfferCopyTests")
struct PlanOfferCopyTests {
    static let lines = [0: "Not much pretty on this drive without extra time.",
                        25: "Not much pretty within 25 extra minutes of this drive."]
    static let more: [(Int?, String?)] = [(nil, nil), (65, "Try 65 extra minutes")]
    static let back: [((Double, Int)?, String?)] = [
        (nil, nil),
        ((3578.87, 32), "All back roads: about 60 min, 32 extra minutes"),
        ((600, 1), "All back roads: about 10 min, 1 extra minute"),
        ((1260, 0), "All back roads: about 21 min, no extra time"),
    ]

    @Test("every budget x more x back-roads variant, whole")
    func crossProduct() {
        var seen = Set<PlanOfferCopy>()
        for budget in [0, 25] {
            for (moreMinutes, moreTitle) in Self.more {
                for (backOffer, backTitle) in Self.back {
                    let offer = PlanOffer(budgetMinutes: budget, moreTimeMinutes: moreMinutes,
                                          backRoadsEtaSeconds: backOffer?.0, backRoadsBudgetMinutes: backOffer?.1)
                    let expected = PlanOfferCopy(line: Self.lines[budget]!, moreTime: moreTitle, backRoads: backTitle,
                                                 action: .chooseAnotherPlace)
                    #expect(PlanOfferCopy.of(offer) == expected, "\(offer)")
                    seen.insert(PlanOfferCopy.of(offer))
                }
            }
        }
        #expect(seen.count == 2 * Self.more.count * Self.back.count)
    }

    @Test("a back-roads ETA with no budget to ask is not a button")
    func etaWithoutBudgetIsNoButton() {
        let offer = PlanOffer(budgetMinutes: 25, moreTimeMinutes: 65, backRoadsEtaSeconds: 12000,
                              backRoadsBudgetMinutes: nil)
        #expect(PlanOfferCopy.of(offer).backRoads == nil)
    }
}
