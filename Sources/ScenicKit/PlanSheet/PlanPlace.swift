/// A corpus place the plan sheet can plan from or to (T-0294): its `place_id`, the name the search showed, and its
/// coordinate as the corpus holds it. Only the destination's id and the start's coordinate, at 2 dp, leave the device.
public struct PlanPlace: Equatable, Sendable {
    public let id: Int64
    public let name: String
    public let coordinate: Coordinate

    public init(id: Int64, name: String, coordinate: Coordinate) {
        self.id = id
        self.name = name
        self.coordinate = coordinate
    }
}
