/// Where first-run onboarding is (T-0309 R3): the vehicle, then the safety disclaimer, then done.
public enum OnboardingStep: Equatable, Sendable, CaseIterable {
    case vehicle
    case disclaimer
    case done
}
