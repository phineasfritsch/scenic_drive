/// One hazard run on a previewed route, over route coordinate indices [fromIndex, toIndex) - the Worker's hazard,
/// carried below ScenicAPIClient so the preview's strip can read it (T-0294 R6).
public struct PlanHazardRun: Equatable, Sendable {
    public let kind: String
    public let value: String
    public let fromIndex: Int
    public let toIndex: Int

    public init(kind: String, value: String, fromIndex: Int, toIndex: Int) {
        self.kind = kind
        self.value = value
        self.fromIndex = fromIndex
        self.toIndex = toIndex
    }
}
