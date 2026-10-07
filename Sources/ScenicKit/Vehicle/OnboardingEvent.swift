/// What the user can do on an onboarding screen (T-0309 R3). Only `accept`, on the disclaimer step, records the
/// acknowledgement; every other event leaves it as it was.
public enum OnboardingEvent: Equatable, Sendable {
    case choose(VehicleProfile)
    case next
    case back
    case skip
    case accept
}
