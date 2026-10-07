/// One saved drive, exactly what the plan's Saved drives row keeps on the device: segment ids, 5-dp midpoints,
/// lambda, the budget in minutes, a name and when it was saved - and whether the current corpus could not
/// re-resolve it (T-0290 R3). Every stored number is an integer; there is no origin, destination, address,
/// breadcrumb or speed, and P-PRIV-05 binds a test that walks every field (SavedDriveFieldsTests).
public struct SavedDrive: Equatable, Sendable {
    /// The store's row id; nil until `SavedDriveStore.save(_:)` returns the stored value.
    public internal(set) var id: Int64?
    public internal(set) var name: String
    public internal(set) var segments: [SavedSegment]
    /// Lambda in fixed point 1e-5.
    public let lambdaE5: Int
    public let budgetMinutes: Int
    /// Unix seconds, whole: a Date is a Double and would carry sub-second digits.
    public let createdAt: Int64
    /// The last re-resolve found a saved segment with no replacement within 25 m (R5).
    public internal(set) var needsReplan: Bool

    /// The storage bound on lambda (R4a): 125 times LambdaSearch.maxLambda, so no plan's lambda is refused, and
    /// small enough that lambda * 1e5 always fits an Int.
    public static let maxLambda: Double = 1000

    public init(id: Int64? = nil, name: String, segments: [SavedSegment], lambda: Double, budgetMinutes: Int,
                createdAt: Int64, needsReplan: Bool = false) throws {
        self.lambdaE5 = try FiveDecimals.fixedPoint(lambda, in: 0...Self.maxLambda, field: .lambda)
        self.id = id
        self.name = name
        self.segments = segments
        self.budgetMinutes = budgetMinutes
        self.createdAt = createdAt
        self.needsReplan = needsReplan
    }

    /// A row the store wrote; its CHECK constraint holds lambda_e5 in [0, 100000000] (R3a).
    init(id: Int64, name: String, segments: [SavedSegment], lambdaE5: Int, budgetMinutes: Int, createdAt: Int64,
         needsReplan: Bool) {
        self.id = id
        self.name = name
        self.segments = segments
        self.lambdaE5 = lambdaE5
        self.budgetMinutes = budgetMinutes
        self.createdAt = createdAt
        self.needsReplan = needsReplan
    }

    public var lambda: Double { FiveDecimals.degrees(lambdaE5) }
}
