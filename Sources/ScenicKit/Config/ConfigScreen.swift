/// The plan sheet's three planning screens, each degraded by /config on its own (T-0364 R3): the drive (Plan), the
/// loop and the road trip. Surprise Me is not one of them: it plans on the device and sends the Worker nothing.
public enum ConfigScreen: String, CaseIterable, Equatable, Sendable {
    case plan
    case loop
    case trip
}
