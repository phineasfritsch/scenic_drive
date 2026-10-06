/**
 * A minimal DER reader for the X.509 certificates in an App Store notification's x5c chain (T-0267 R3). It reads
 * one tag-length-value at a time, definite lengths only (DER forbids indefinite), and refuses anything that runs
 * past its parent. No new dependency: the Worker parses exactly what it verifies.
 */

export interface Tlv {
  tag: number;
  /** The whole element, header included - what a signature or a name comparison covers. */
  raw: Uint8Array;
  /** The content octets. */
  value: Uint8Array;
}

export class DerError extends Error {}

/** Reads the element starting at `offset` of `bytes`; returns it and the offset just past it. */
export function readTlv(bytes: Uint8Array, offset = 0): { tlv: Tlv; next: number } {
  if (offset + 2 > bytes.length) throw new DerError("truncated header");
  const tag = bytes[offset]!;
  if ((tag & 0x1f) === 0x1f) throw new DerError("multi-byte tags are not used here");
  let length = bytes[offset + 1]!;
  let header = 2;
  if (length & 0x80) {
    const count = length & 0x7f;
    if (count === 0 || count > 4) throw new DerError("unsupported length");
    if (offset + 2 + count > bytes.length) throw new DerError("truncated length");
    length = 0;
    for (let i = 0; i < count; i++) length = length * 256 + bytes[offset + 2 + i]!;
    header += count;
  }
  const end = offset + header + length;
  if (end > bytes.length) throw new DerError("element runs past its parent");
  return { tlv: { tag, raw: bytes.subarray(offset, end), value: bytes.subarray(offset + header, end) }, next: end };
}

/** The children of a constructed element, in order; the content must be consumed exactly. */
export function children(parent: Tlv): Tlv[] {
  const out: Tlv[] = [];
  let at = 0;
  while (at < parent.value.length) {
    const { tlv, next } = readTlv(parent.value, at);
    out.push(tlv);
    at = next;
  }
  return out;
}

/** The single element that is the whole of `bytes` - trailing garbage is refused. */
export function readOnly(bytes: Uint8Array): Tlv {
  const { tlv, next } = readTlv(bytes, 0);
  if (next !== bytes.length) throw new DerError("trailing bytes");
  return tlv;
}

export function expectTag(tlv: Tlv | undefined, tag: number): Tlv {
  if (!tlv || tlv.tag !== tag) throw new DerError(`expected tag 0x${tag.toString(16)}`);
  return tlv;
}

/** Dotted-decimal text of an OBJECT IDENTIFIER's content octets. */
export function oidText(value: Uint8Array): string {
  if (value.length === 0) throw new DerError("empty OID");
  const first = value[0]!;
  const parts = [Math.min(2, Math.floor(first / 40)), first - 40 * Math.min(2, Math.floor(first / 40))];
  let n = 0;
  for (let i = 1; i < value.length; i++) {
    n = n * 128 + (value[i]! & 0x7f);
    if (!(value[i]! & 0x80)) {
      parts.push(n);
      n = 0;
    }
  }
  return parts.join(".");
}

/** UTCTime (YYMMDDHHMMSSZ, 50-99 -> 19xx) or GeneralizedTime (YYYYMMDDHHMMSSZ) -> epoch ms. */
export function timeMs(tlv: Tlv): number {
  const text = new TextDecoder().decode(tlv.value);
  const match = tlv.tag === 0x17 ? /^(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z$/.exec(text)
    : tlv.tag === 0x18 ? /^(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})Z$/.exec(text) : null;
  if (!match) throw new DerError("bad time");
  let year = Number(match[1]);
  if (tlv.tag === 0x17) year += year < 50 ? 2000 : 1900;
  return Date.UTC(year, Number(match[2]) - 1, Number(match[3]), Number(match[4]), Number(match[5]), Number(match[6]));
}

/** A DER ECDSA-Sig-Value SEQUENCE { r INTEGER, s INTEGER } -> the raw r||s WebCrypto verifies, each `size` bytes. */
export function ecdsaRaw(der: Uint8Array, size: number): Uint8Array {
  const [r, s] = children(expectTag(readOnly(der), 0x30)).map((x) => expectTag(x, 0x02).value);
  if (!r || !s) throw new DerError("ECDSA signature needs r and s");
  const out = new Uint8Array(2 * size);
  for (const [i, int] of [r, s].entries()) {
    let v = int;
    while (v.length > 1 && v[0] === 0) v = v.subarray(1);
    if (v.length > size) throw new DerError("ECDSA integer too long");
    out.set(v, i * size + size - v.length);
  }
  return out;
}
