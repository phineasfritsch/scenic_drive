import Foundation

/// FIPS 180-4 SHA-256 on Foundation alone (T-0300 O6): CryptoKit is Apple-only and this target builds on Linux.
/// It verifies a downloaded corpus against its manifest; SHA256Tests pins it to digests python hashlib computed.
public struct SHA256: Sendable {
    private static let k: [UInt32] = [
        0x428a_2f98, 0x7137_4491, 0xb5c0_fbcf, 0xe9b5_dba5, 0x3956_c25b, 0x59f1_11f1, 0x923f_82a4, 0xab1c_5ed5,
        0xd807_aa98, 0x1283_5b01, 0x2431_85be, 0x550c_7dc3, 0x72be_5d74, 0x80de_b1fe, 0x9bdc_06a7, 0xc19b_f174,
        0xe49b_69c1, 0xefbe_4786, 0x0fc1_9dc6, 0x240c_a1cc, 0x2de9_2c6f, 0x4a74_84aa, 0x5cb0_a9dc, 0x76f9_88da,
        0x983e_5152, 0xa831_c66d, 0xb003_27c8, 0xbf59_7fc7, 0xc6e0_0bf3, 0xd5a7_9147, 0x06ca_6351, 0x1429_2967,
        0x27b7_0a85, 0x2e1b_2138, 0x4d2c_6dfc, 0x5338_0d13, 0x650a_7354, 0x766a_0abb, 0x81c2_c92e, 0x9272_2c85,
        0xa2bf_e8a1, 0xa81a_664b, 0xc24b_8b70, 0xc76c_51a3, 0xd192_e819, 0xd699_0624, 0xf40e_3585, 0x106a_a070,
        0x19a4_c116, 0x1e37_6c08, 0x2748_774c, 0x34b0_bcb5, 0x391c_0cb3, 0x4ed8_aa4a, 0x5b9c_ca4f, 0x682e_6ff3,
        0x748f_82ee, 0x78a5_636f, 0x84c8_7814, 0x8cc7_0208, 0x90be_fffa, 0xa450_6ceb, 0xbef9_a3f7, 0xc671_78f2,
    ]

    private var state: [UInt32] = [0x6a09_e667, 0xbb67_ae85, 0x3c6e_f372, 0xa54f_f53a,
                                   0x510e_527f, 0x9b05_688c, 0x1f83_d9ab, 0x5be0_cd19]
    private var block: [UInt8] = []
    /// Message bytes taken so far.
    public private(set) var count: Int = 0

    public init() {
        block.reserveCapacity(64)
    }

    public mutating func update<S: Sequence>(_ bytes: S) where S.Element == UInt8 {
        for byte in bytes {
            block.append(byte)
            count += 1
            if block.count == 64 {
                compress(block)
                block.removeAll(keepingCapacity: true)
            }
        }
    }

    /// The digest of everything taken so far, as 64 lowercase hex digits. `self` is not changed.
    public func finalize() -> String {
        var tail = block
        tail.append(0x80)
        while tail.count % 64 != 56 {
            tail.append(0)
        }
        let bits = UInt64(count) &* 8
        for shift in stride(from: 56, through: 0, by: -8) {
            tail.append(UInt8(truncatingIfNeeded: bits >> UInt64(shift)))
        }
        var last = self
        for start in stride(from: 0, to: tail.count, by: 64) {
            last.compress(Array(tail[start..<(start + 64)]))
        }
        return last.state.map { word in
            let digits = String(word, radix: 16)
            return String(repeating: "0", count: 8 - digits.count) + digits
        }.joined()
    }

    public static func hex(of data: Data) -> String {
        var hasher = SHA256()
        hasher.update(data)
        return hasher.finalize()
    }

    public static func hex(ofFileAt url: URL, chunk: Int = 1 << 20) throws -> String {
        try digest(ofFileAt: url, chunk: chunk).hex
    }

    /// The file's byte count and digest from ONE read, `chunk` bytes at a time.
    static func digest(ofFileAt url: URL, chunk: Int = 1 << 20) throws -> (count: Int, hex: String) {
        let handle = try FileHandle(forReadingFrom: url)
        defer { try? handle.close() }
        var hasher = SHA256()
        while let data = try handle.read(upToCount: chunk), !data.isEmpty {
            hasher.update(data)
        }
        return (hasher.count, hasher.finalize())
    }

    private static func rotr(_ x: UInt32, _ n: UInt32) -> UInt32 {
        (x >> n) | (x << (32 - n))
    }

    private mutating func compress(_ bytes: [UInt8]) {
        var w = [UInt32](repeating: 0, count: 64)
        for i in 0..<16 {
            let b0 = UInt32(bytes[4 * i]) << 24
            let b1 = UInt32(bytes[4 * i + 1]) << 16
            let b2 = UInt32(bytes[4 * i + 2]) << 8
            w[i] = b0 | b1 | b2 | UInt32(bytes[4 * i + 3])
        }
        for i in 16..<64 {
            let s0 = Self.rotr(w[i - 15], 7) ^ Self.rotr(w[i - 15], 18) ^ (w[i - 15] >> 3)
            let s1 = Self.rotr(w[i - 2], 17) ^ Self.rotr(w[i - 2], 19) ^ (w[i - 2] >> 10)
            w[i] = w[i - 16] &+ s0 &+ w[i - 7] &+ s1
        }
        var a = state[0], b = state[1], c = state[2], d = state[3]
        var e = state[4], f = state[5], g = state[6], h = state[7]
        for i in 0..<64 {
            let bigS1 = Self.rotr(e, 6) ^ Self.rotr(e, 11) ^ Self.rotr(e, 25)
            let choose = (e & f) ^ (~e & g)
            let t1 = h &+ bigS1 &+ choose &+ Self.k[i] &+ w[i]
            let bigS0 = Self.rotr(a, 2) ^ Self.rotr(a, 13) ^ Self.rotr(a, 22)
            let majority = (a & b) ^ (a & c) ^ (b & c)
            let t2 = bigS0 &+ majority
            h = g
            g = f
            f = e
            e = d &+ t1
            d = c
            c = b
            b = a
            a = t1 &+ t2
        }
        state[0] &+= a
        state[1] &+= b
        state[2] &+= c
        state[3] &+= d
        state[4] &+= e
        state[5] &+= f
        state[6] &+= g
        state[7] &+= h
    }
}
