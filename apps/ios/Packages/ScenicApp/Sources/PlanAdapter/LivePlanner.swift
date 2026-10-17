import Foundation
import ScenicAPIClient
import ScenicKit

/// THE ONLY IMPORTER OF ScenicAPIClient UNDER apps/ios (T-0294 R1), as MapAdapter is of MapLibre: the app's live
/// planner, built once by the shell and handed to the plan sheet as a `RoutePlanning` that is also the sheet's
/// `WaitlistJoining` (T-0360 R5: LiveWaitlist's client, or none).
///
/// The base URL is LiveBaseURL.url (T-0394): the Info.plist value, or in DEBUG the `-plan.base.url` launch
/// argument. Without one the planner answers routingOffline and sends nothing.
public enum LivePlanner {
    /// The sheet's planner composed once (T-0357 x T-0360 merge ruling): WaitlistRoutePlanner outermost, so joining is
    /// reachable from the one value; it forwards plan and degrade to `planner()`.
    public static func make() -> any RoutePlanning & WaitlistJoining & PlaceSearching {
        WaitlistRoutePlanner(planner: planner(), waitlist: LiveWaitlist.make(), search: placeSearch())
    }

    /// T-0362 R2, R9: the address search on the same base and the same identity as the plan client - the Worker
    /// remembers each row's place id under the identity /plan computes; NoPlaceSearch without an https base.
    static func placeSearch() -> any PlaceSearching {
        guard let base = LiveBaseURL.url else { return NoPlaceSearch() }
        return ClientPlaceSearch(client: SearchClient(base: base, transport: URLSessionPlanTransport(),
                                                      installID: StoredInstallID(), accountToken: StoreKitAccountToken(),
                                                      session: LiveSession.store))
    }

    /// T-0357 R7: the ClientPlanner with the /config cache and our build, so the sheet hears a pause or an update
    /// before the user taps Plan; TelemetryRoutePlanner wraps that whole gate, so plan_requested still wraps the plan.
    static func planner() -> any RoutePlanning {
        guard let base = LiveBaseURL.url else { return UnreachablePlanner() }
        let cache = Self.cache(base)
        let build = Self.appBuild
        return TelemetryRoutePlanner(inner: ConfiguredPlanner(planner: ClientPlanner(client: client(base)), cache: cache,
                                                              appBuild: build))
    }

    /// T-0368 R1: feature_surprise from the KEPT /config answer - the store only, no request - for the home and the plan
    /// sheet alike; without an https base nothing was ever kept, so the bundled answer (on).
    public static func surpriseGate() -> SurpriseGate {
        guard let base = LiveBaseURL.url else { return SurpriseGate.of(RemoteConfig.bundled) }
        return SurpriseGate.of(cache(base).kept)
    }

    /// The /config cache every live planner degrades through (T-0357 R4; T-0364 R3: plan, loop and trip alike).
    static func cache(_ base: URL) -> ConfigCache {
        ConfigCache(client: ConfigClient(base: base, transport: URLSessionPlanTransport()), storage: DefaultsConfigStorage())
    }

    /// Our build, as /config's min_app_build is compared against it (T-0357 R5).
    static var appBuild: Int? {
        AppBuild.parse(Bundle.main.object(forInfoDictionaryKey: "CFBundleVersion") as? String)
    }

    /// The drive's reroute sender (T-0328 R2): PlanRerouter on the same client, continuing `preview`'s plan; the sender
    /// that asks nothing (RerouteUnavailable - the drive rejoins) without an https base or a plan token.
    public static func rerouter(for preview: PlanPreview) -> any RerouteSending {
        guard let base = LiveBaseURL.url, let continuation = preview.continuation else { return RerouteUnavailable() }
        return PlanRerouter(client: client(base), place: continuation.place, budgetMinutes: continuation.budgetMinutes)
    }

    private static func client(_ base: URL) -> PlanClient {
        PlanClient(base: base, transport: URLSessionPlanTransport(), installID: StoredInstallID(),
                   accountToken: StoreKitAccountToken(), session: LiveSession.store)
    }
}
