import ScenicKit
import Testing

/// T-0309 acceptance 2: the closed vehicle enum (R3). Only `.standard` can be chosen; every other case is present and
/// says why it is not, word for word; a stored raw value never reads back as a disabled case.
@Suite("VehicleProfileTests")
struct VehicleProfileTests {
    struct Row: Equatable {
        let profile: VehicleProfile
        let raw: String
        let name: String
        let isEnabled: Bool
        let disabledReason: String?
    }

    static let table: [Row] = [
        Row(profile: .standard, raw: "standard", name: "Standard car", isEnabled: true, disabledReason: nil),
        Row(profile: .lowClearance, raw: "lowClearance", name: "Low-clearance car", isEnabled: false,
            disabledReason: "Not yet. The map has no ground-clearance data, so it cannot steer you around rough roads."),
        Row(profile: .motorcycle, raw: "motorcycle", name: "Motorcycle", isEnabled: false,
            disabledReason: "Not yet. Two wheels need their own road rules, and those are still being written."),
        Row(profile: .trailer, raw: "trailer", name: "Towing a trailer", isEnabled: false,
            disabledReason: "Not yet. The map has no weight or grade limits, so it cannot plan around them."),
        Row(profile: .rv, raw: "rv", name: "RV or camper", isEnabled: false,
            disabledReason: "Not yet. The map has no height or length limits, so it cannot plan around them."),
    ]

    @Test("only standard is enabled; every other case is present with its reason, whole")
    func profileTable() {
        #expect(VehicleProfile.allCases == Self.table.map(\.profile))
        for row in Self.table {
            let p = row.profile
            let got = Row(profile: p, raw: p.rawValue, name: p.name, isEnabled: p.isEnabled,
                          disabledReason: p.disabledReason)
            #expect(got == row)
        }
        #expect(VehicleProfile.storageKey == "vehicle.profile.v1")
    }

    @Test("stored: absent, unknown and disabled raw values read back as standard")
    func storedReadsBackEnabled() {
        let rows: [(String?, VehicleProfile)] = [
            (nil, .standard), ("", .standard), ("Standard", .standard), ("truck", .standard),
            ("standard", .standard), ("lowClearance", .standard), ("motorcycle", .standard),
            ("trailer", .standard), ("rv", .standard),
        ]
        #expect(rows.count == VehicleProfile.allCases.count + 4)
        for (raw, expected) in rows {
            #expect(VehicleProfile.stored(raw) == expected, "\(raw ?? "nil")")
        }
    }
}
