/// The ONE thing a failed plan offers to do next (the plan's Degraded states row; T-0294 R5). Each is something the
/// app can do today. T-0360: a start outside the served region offers the waitlist.
public enum PlanFailureAction: String, CaseIterable, Equatable, Sendable {
    /// Leave the plan sheet for the home's Surprise card, which plans nothing and spends no request.
    case surpriseMe
    /// Ask again with the same ticket's inputs.
    case tryAgain
    /// Back to the destination search.
    case chooseAnotherPlace
    /// Back to the start search.
    case changeStart
    /// Close the plan sheet.
    case close
    /// Count the start's area on the waitlist (T-0360 R1): one H3 resolution-5 cell, once per install.
    case joinWaitlist

    /// The button's words.
    public var title: String {
        switch self {
        case .surpriseMe: return "Surprise me instead"
        case .tryAgain: return "Try again"
        case .chooseAnotherPlace: return "Choose another place"
        case .changeStart: return "Change the start"
        case .close: return "Close"
        case .joinWaitlist: return "Count this area"
        }
    }
}
