/// First-run onboarding as a value (T-0309 R1, R3): vehicle -> disclaimer -> done.
///
/// The app's `SafetyDisclaimer` sheet runs this machine and records the device acknowledgement only when
/// `disclaimerAccepted` turns true, so the plan gate (`PlanSheet.startPlanning()`) and the handoff gate still read the
/// one stored key. Skipping or backing out never accepts: only `accept` on the disclaimer step does.
public struct Onboarding: Equatable, Sendable {
    public private(set) var step: OnboardingStep
    public private(set) var vehicle: VehicleProfile
    public private(set) var disclaimerAccepted: Bool

    /// First launch: the vehicle step, a standard car, nothing accepted.
    public init() {
        self.init(step: .vehicle, vehicle: .standard, disclaimerAccepted: false)
    }

    init(step: OnboardingStep, vehicle: VehicleProfile, disclaimerAccepted: Bool) {
        self.step = step
        self.vehicle = vehicle
        self.disclaimerAccepted = disclaimerAccepted
    }

    /// One user action. An event a step does not take leaves the whole value unchanged.
    public mutating func send(_ event: OnboardingEvent) {
        switch (step, event) {
        case (.vehicle, .choose(let profile)):
            if profile.isEnabled { vehicle = profile }
        case (.vehicle, .next), (.vehicle, .skip):
            step = .disclaimer
        case (.disclaimer, .back):
            step = .vehicle
        case (.disclaimer, .accept):
            step = .done
            disclaimerAccepted = true
        case (.vehicle, .back), (.vehicle, .accept), (.disclaimer, .choose), (.disclaimer, .next),
             (.disclaimer, .skip), (.done, _):
            break
        }
    }
}
