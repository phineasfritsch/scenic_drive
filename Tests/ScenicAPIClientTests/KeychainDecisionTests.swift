import Foundation
import ScenicAPIClient
import Testing

/// T-0310 acceptance 4 (R5, R6): the Keychain write decision and the install id's decision as pure functions over
/// {absent, valid, malformed, read failure}, each whole answer by full equality, and the session item's exact shape.
@Suite("KeychainDecisionTests") struct KeychainDecisionTests {
    static let kept = UUID(uuidString: "11111111-2222-4333-8444-555555555555")!
    static let migrated = UUID(uuidString: "66666666-7777-4888-9999-AAAAAAAAAAAA")!
    static let fresh = UUID(uuidString: "BBBBBBBB-CCCC-4DDD-AEEE-FFFFFFFFFFFF")!

    @Test("An item that exists is replaced - valid or malformed - an absent one added, a failed read left alone")
    func replacing() {
        let reads: [KeychainRead<UUID>] = [.absent, .valid(Self.kept), .malformed, .failed(-25308)]
        #expect(reads.map { KeychainWrite.replacing(over: $0) } == [.add, .update, .update, .skip])
    }

    struct Row: Sendable, CustomTestStringConvertible {
        let keychain: KeychainRead<UUID>
        let defaults: UUID?
        let expected: InstallIDDecision
        var testDescription: String { "\(keychain) defaults \(defaults?.uuidString ?? "none")" }
    }

    static let rows: [Row] = [
        Row(keychain: .absent, defaults: migrated, expected: InstallIDDecision(id: migrated, write: .add)),
        Row(keychain: .absent, defaults: nil, expected: InstallIDDecision(id: fresh, write: .add)),
        Row(keychain: .valid(kept), defaults: migrated, expected: InstallIDDecision(id: kept, write: .skip)),
        Row(keychain: .valid(kept), defaults: nil, expected: InstallIDDecision(id: kept, write: .skip)),
        Row(keychain: .malformed, defaults: migrated, expected: InstallIDDecision(id: migrated, write: .update)),
        Row(keychain: .malformed, defaults: nil, expected: InstallIDDecision(id: fresh, write: .update)),
        Row(keychain: .failed(-25308), defaults: migrated, expected: InstallIDDecision(id: migrated, write: .skip)),
        Row(keychain: .failed(-25308), defaults: nil, expected: InstallIDDecision(id: fresh, write: .skip)),
    ]

    @Test("The install id's decision over every Keychain state, with and without a UserDefaults copy", arguments: rows)
    func installID(_ row: Row) {
        #expect(InstallIDDecision.decide(keychain: row.keychain, defaults: row.defaults, fresh: Self.fresh)
                == row.expected)
    }

    static let record = SessionRecord(keyId: AttestWire.newKey, token: AttestWire.newToken,
                                      expiresAt: Date(timeIntervalSince1970: 1_791_428_400))
    static let canonical = "{\"expires_at\":1791428400,\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\(AttestWire.newToken)\"}"

    @Test("The session item is exactly {expires_at, key_id, token} and reads back as the record it was written from")
    func sessionItem() {
        #expect(Self.record.data == Data(Self.canonical.utf8))
        #expect(SessionRecord(data: Data(Self.canonical.utf8)) == Self.record)
    }

    static let malformed: [String] = [
        "",
        "not json",
        "{\"expires_at\":1791428400,\"key_id\":\"\(AttestWire.newKey)\"}",
        "{\"expires_at\":1791428400,\"token\":\"\(AttestWire.newToken)\"}",
        "{\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\(AttestWire.newToken)\"}",
        "{\"expires_at\":\"1791428400\",\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\(AttestWire.newToken)\"}",
        "{\"expires_at\":1791428400.5,\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\(AttestWire.newToken)\"}",
        "{\"expires_at\":1791428400,\"key_id\":\"\",\"token\":\"\(AttestWire.newToken)\"}",
        "{\"expires_at\":1791428400,\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\"}",
        "{\"expires_at\":1791428400,\"extra\":1,\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\(AttestWire.newToken)\"}",
        "{\"token\":\"\(AttestWire.newToken)\",\"key_id\":\"\(AttestWire.newKey)\",\"expires_at\":1791428400}",
        "{\"expires_at\":1791428400,\"key_id\":\"\(AttestWire.newKey)\",\"token\":\"\(AttestWire.newToken)\"} ",
    ]

    @Test("Any other item is malformed", arguments: malformed)
    func malformedItem(_ text: String) {
        #expect(SessionRecord(data: Data(text.utf8)) == nil)
    }
}
