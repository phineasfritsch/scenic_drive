/// What Save keeps of a previewed route (T-0306 R2), before PlaceStore turns it into the T-0290 value: the route
/// ends and the scenic waypoints between them, each axis rounded ONCE to 5 dp here, and the lambda likewise.
/// PlaceStore refuses anything with more than 5 dp, so nothing is rounded a second time.
public struct SavedDraft: Equatable, Sendable {
    public static let scale: Double = 100_000
    public let name: String
    public let points: [Coordinate]
    public let lambda: Double
    public let budgetMinutes: Int
    public let createdAt: Int64

    public init(name: String, points: [Coordinate], lambda: Double, budgetMinutes: Int, createdAt: Int64) {
        self.name = name
        self.points = points
        self.lambda = lambda
        self.budgetMinutes = budgetMinutes
        self.createdAt = createdAt
    }

    /// The draft of `preview`: [first route point] + waypoints + [last route point], each at 5 dp; nil for an empty
    /// route, which has nothing to save.
    public static func of(_ preview: PlanPreview, budgetMinutes: Int, name: String, createdAt: Int64) -> SavedDraft? {
        guard let first = preview.route.first, let last = preview.route.last else { return nil }
        let points = ([first] + preview.waypoints + [last]).map {
            Coordinate(latitude: fiveDecimals($0.latitude), longitude: fiveDecimals($0.longitude))
        }
        return SavedDraft(name: name, points: points, lambda: fiveDecimals(preview.lambda), budgetMinutes: budgetMinutes,
                          createdAt: createdAt)
    }

    /// THE rounding site: the nearest 1e-5, half away from zero.
    public static func fiveDecimals(_ value: Double) -> Double {
        (value * scale).rounded() / scale
    }
}
