import Foundation

/// The app install's identity for the Worker's per-device quota (T-0260): `PlanClient` sends it as
/// `x-scenic-device` on every request, lowercased, and the Worker (routerDeps.ts `deviceIdentity`) keys each
/// install's anon quota by it instead of the shared `device:unidentified` bucket.
///
/// A `UUID`, so a malformed id cannot be represented. No argument, so nothing the client knows - no origin, no
/// place - can be an input to it (P-PRIV-05). The conformer that generates it ONCE per install and keeps it in the
/// keychain lives in the Apple package (M6); this package never generates an id, it only reads this one.
public protocol InstallIDProvider: Sendable {
    func installID() -> UUID
}
