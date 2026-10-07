import Foundation
import PlaceStore
import Testing

/// `SHA256` (T-0300 O6) against digests python hashlib computed (Log): the NIST examples, and runs of "a" at every
/// padding boundary - 55 bytes is the last single-block message, 56 the first that needs a second block, 63/64/65
/// straddle one block, 119/120/128 the next.
struct SHA256Tests {
    static let vectors: [(Data, String)] = [
        (Data(), "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"),
        (Data("abc".utf8), "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
        (Data("abcdbcdecdefdefgefghfghighijhijkijkljklmklmnlmnomnopnopq".utf8),
         "248d6a61d20638b8e5c026930c3e6039a33ce45964ff2167f6ecedd419db06c1"),
        (Data(("abcdefghbcdefghicdefghijdefghijkefghijklfghijklmghijklmnhijklmno"
               + "ijklmnopjklmnopqklmnopqrlmnopqrsmnopqrstnopqrstu").utf8),
         "cf5b16a778af8380036ce59e7b0492370b249b11e8f07a51afac45037afee9d1"),
        (a(55), "9f4390f8d30c2dd92ec9f095b65e2b9ae9b0a925a5258e241c9f1e910f734318"),
        (a(56), "b35439a4ac6f0948b6d6f9e3c6af0f5f590ce20f1bde7090ef7970686ec6738a"),
        (a(63), "7d3e74a05d7db15bce4ad9ec0658ea98e3f06eeecf16b4c6fff2da457ddc2f34"),
        (a(64), "ffe054fe7ae0cb6dc65c3af9b61d5209f439851db43d0ba5997337df154668eb"),
        (a(65), "635361c48bb9eab14198e76ea8ab7f1a41685d6ad62aa9146d301d4f17eb0ae0"),
        (a(119), "31eba51c313a5c08226adf18d4a359cfdfd8d2e816b13f4af952f7ea6584dcfb"),
        (a(120), "2f3d335432c70b580af0e8e1b3674a7c020d683aa5f73aaaedfdc55af904c21c"),
        (a(128), "6836cf13bac400e9105071cd6af47084dfacad4e5e302c94bfed24e013afb73e"),
    ]
    static let million = "cdc76e5c9914fb9281a1c7e284d73e67f1809a48a497200e046d39ccc7112cd0"

    static func a(_ n: Int) -> Data {
        Data(repeating: UInt8(ascii: "a"), count: n)
    }

    @Test func digestsEqualHashlib() {
        for (data, hex) in Self.vectors {
            #expect(SHA256.hex(of: data) == hex, "\(data.count) bytes")
        }
    }

    @Test func everySplitOfTheTwoBlockVectorEqualsTheWhole() {
        let (data, hex) = Self.vectors[3]
        for cut in 0...data.count {
            var hasher = SHA256()
            hasher.update(data.prefix(cut))
            hasher.update(data.dropFirst(cut))
            #expect(hasher.finalize() == hex, "split at \(cut)")
        }
    }

    @Test func aFileHashedInChunksEqualsHashlib() throws {
        let slots = try CorpusSlotState.scratch()
        try Self.a(1_000_000).write(to: slots.active)
        for chunk in [1 << 20, 64, 63, 1000] {
            #expect(try SHA256.hex(ofFileAt: slots.active, chunk: chunk) == Self.million, "chunk \(chunk)")
        }
    }
}
