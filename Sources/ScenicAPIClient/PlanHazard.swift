/// One hazard run on the returned route (T-0248 R8): a `surface` that is not paved or a `road_access` that is not
/// open, over route coordinate indices [fromIndex, toIndex).
public struct PlanHazard: Equatable, Sendable, Decodable {
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

    enum CodingKeys: String, CodingKey {
        case kind
        case value
        case fromIndex = "from_index"
        case toIndex = "to_index"
    }
}
