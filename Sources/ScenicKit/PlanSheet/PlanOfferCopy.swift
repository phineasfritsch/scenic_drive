/// The offer card's words (T-0334 R5): the line names the minutes the plan asked with, and each button names the
/// minutes it will ask for - "+40" as budget + 40, "all back roads" as its real ETA and the extra time that covers it.
/// An offer the answer did not make has no button; the card's last way on is choosing another place.
public struct PlanOfferCopy: Hashable, Sendable {
    public let line: String
    public let moreTime: String?
    public let backRoads: String?
    public let action: PlanFailureAction

    public init(line: String, moreTime: String?, backRoads: String?, action: PlanFailureAction) {
        self.line = line
        self.moreTime = moreTime
        self.backRoads = backRoads
        self.action = action
    }

    public static func of(_ offer: PlanOffer) -> PlanOfferCopy {
        let line = offer.budgetMinutes == 0
            ? "Not much pretty on this drive without extra time."
            : "Not much pretty within \(extra(offer.budgetMinutes)) of this drive."
        var backRoads: String?
        if let eta = offer.backRoadsEtaSeconds, let minutes = offer.backRoadsBudgetMinutes {
            backRoads = "All back roads: about \(Int((eta / 60).rounded())) min, \(extra(minutes))"
        }
        return PlanOfferCopy(line: line, moreTime: offer.moreTimeMinutes.map { "Try \(extra($0))" },
                             backRoads: backRoads, action: .chooseAnotherPlace)
    }

    static func extra(_ minutes: Int) -> String {
        switch minutes {
        case 0: return "no extra time"
        case 1: return "1 extra minute"
        default: return "\(minutes) extra minutes"
        }
    }
}
