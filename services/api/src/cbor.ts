/**
 * A minimal CBOR (RFC 8949) decoder for the App Attest attestation object (T-0278 R8). No dependency: it reads
 * exactly what the attestation needs - unsigned integers, byte strings, text strings, arrays and text-keyed maps,
 * all with definite lengths - and refuses everything else: negative integers, tags, floats and simple values,
 * indefinite lengths, a non-text or duplicate map key, nesting deeper than MAX_DEPTH and trailing bytes.
 */

export type Cbor = number | string | Uint8Array | Cbor[] | Map<string, Cbor>;

export class CborError extends Error {}

export const MAX_DEPTH = 8;

function fail(why: string): never {
  throw new CborError(why);
}

function item(bytes: Uint8Array, at: number, depth: number): { value: Cbor; next: number } {
  if (depth > MAX_DEPTH) fail("nested too deep");
  if (at >= bytes.length) fail("truncated item");
  const major = bytes[at]! >> 5;
  const info = bytes[at]! & 0x1f;
  let next = at + 1;
  let arg = info;
  if (info >= 24) {
    if (info > 27) fail("indefinite or reserved length");
    const size = 1 << (info - 24);
    if (next + size > bytes.length) fail("truncated argument");
    arg = 0;
    for (let i = 0; i < size; i++) arg = arg * 256 + bytes[next + i]!;
    if (!Number.isSafeInteger(arg)) fail("argument too large");
    next += size;
  }
  switch (major) {
    case 0:
      return { value: arg, next };
    case 2:
    case 3: {
      const end = next + arg;
      if (end > bytes.length) fail("string runs past the end");
      const raw = bytes.slice(next, end);
      if (major === 2) return { value: raw, next: end };
      try {
        return { value: new TextDecoder("utf-8", { fatal: true }).decode(raw), next: end };
      } catch {
        return fail("text is not UTF-8");
      }
    }
    case 4: {
      const out: Cbor[] = [];
      for (let i = 0; i < arg; i++) {
        const element = item(bytes, next, depth + 1);
        out.push(element.value);
        next = element.next;
      }
      return { value: out, next };
    }
    case 5: {
      const out = new Map<string, Cbor>();
      for (let i = 0; i < arg; i++) {
        const key = item(bytes, next, depth + 1);
        if (typeof key.value !== "string") fail("map key is not text");
        if (out.has(key.value)) fail("duplicate map key");
        const value = item(bytes, key.next, depth + 1);
        out.set(key.value, value.value);
        next = value.next;
      }
      return { value: out, next };
    }
    default:
      return fail(`major type ${major} is not used here`);
  }
}

/** The single item that is the whole of `bytes`; throws CborError on anything outside the subset. */
export function decodeCbor(bytes: Uint8Array): Cbor {
  const { value, next } = item(bytes, 0, 0);
  if (next !== bytes.length) fail("trailing bytes");
  return value;
}
