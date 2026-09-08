"""segment_id = fnv1a64(way_id, bucket), masked to 63 bits.

Byte level, not string level. `f"{way}:{bucket}"` makes the id depend on int formatting and on a separator
nobody would think to pin; big-endian fixed-width bytes make it depend on nothing about the build host. The
place key is 9 bytes and the segment key 12, so a node and a way with the same numeric id cannot collide by
construction rather than by luck.

Masked to 63 bits, not 64. Ids are always positive: they cross JSON, they are stored inside saved drives on
the device, and Swift reads them as Int64 with no unsigned juggling. Collision probability at 63 bits with
1.5 M segments is about 6e-8. That deletes the "bind a full 64-bit hash to a sqlite INTEGER" round-trip
failure class instead of mapping around it.
"""
from __future__ import annotations

FNV_OFFSET = 0xCBF29CE484222325
FNV_PRIME = 0x00000100000001B3
MASK64 = 0xFFFFFFFFFFFFFFFF
MASK63 = 0x7FFF_FFFF_FFFF_FFFF
MAX_BUCKET = 65535
# A segment that loses its natural id probes this many times before the build fails naming both keys.
# Probing silently is the plausible-but-wrong path: two segments swap identities and every saved drive
# referencing them points at the wrong road, with no error anywhere.
MAX_PROBES = 8


def fnv1a64(data: bytes) -> int:
    """FNV-1a, 64 bit: xor THEN multiply. The reverse order is FNV-1 and gives different numbers."""
    h = FNV_OFFSET
    for b in data:
        h ^= b
        h = (h * FNV_PRIME) & MASK64
    return h


def natural_id(way_id: int, bucket: int) -> int:
    """The id a segment owns by derivation: the bucket-th 100 m of way way_id."""
    if way_id <= 0:
        raise ValueError(f"way_id must be positive, got {way_id}")
    if not 0 <= bucket <= MAX_BUCKET:
        raise ValueError(f"bucket out of range: {bucket}")
    key = way_id.to_bytes(8, "big", signed=False) + bucket.to_bytes(4, "big", signed=False)
    sid = fnv1a64(key) & MASK63
    return sid or 1  # 0 is reserved for "unset" on device


def place_id(osm_type: str, osm_id: int) -> int:
    if osm_type not in ("n", "w", "r"):
        raise ValueError(f"osm_type must be n, w or r, got {osm_type!r}")
    if osm_id <= 0:
        raise ValueError(f"osm_id must be positive, got {osm_id}")
    key = osm_type.encode("ascii") + osm_id.to_bytes(8, "big", signed=False)  # 9 bytes
    return (fnv1a64(key) & MASK63) or 1


def probe(sid: int, n: int) -> int:
    """The n-th alternative for a colliding id. n >= 1."""
    if n < 1:
        raise ValueError(f"probe number must be >= 1, got {n}")
    return (fnv1a64(sid.to_bytes(8, "big") + bytes([n])) & MASK63) or 1
