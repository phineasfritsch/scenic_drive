/**
 * T-0288 rv2 B1: a spelling-independent RUNTIME record of every read a handler makes off an object. The returned proxy
 * logs each property get, `in` test, key enumeration and descriptor lookup as a path ("url", "cf.country",
 * "headers.get", "has:cf", "ownKeys", "descriptor:cf") however the code spells it - `req.cf`, `Reflect.get(arguments[0],
 * "cf")`, `const { cf } = req`, `"cf" in req`, `Object.keys(req)`. Methods are bound to the real target so
 * headers.get / clone / json / text still work; objects read off it (headers, cf, body, signal, ...) are wrapped too and
 * their reads recorded under the parent's path.
 */
export type ReadLog = string[];

const label = (key: PropertyKey): string => (typeof key === "symbol" ? `[${key.description ?? "symbol"}]` : String(key));

export function recordReads<T extends object>(target: T, log: ReadLog, prefix = ""): T {
  const at = (key: PropertyKey) => `${prefix}${label(key)}`;
  return new Proxy(target, {
    get(t, key) {
      log.push(at(key));
      const value: unknown = Reflect.get(t, key);
      if (typeof value === "function") return value.bind(t);
      if (value !== null && typeof value === "object") return recordReads(value as object, log, `${at(key)}.`);
      return value;
    },
    has(t, key) {
      log.push(`${prefix}has:${label(key)}`);
      return Reflect.has(t, key);
    },
    ownKeys(t) {
      log.push(`${prefix}ownKeys`);
      return Reflect.ownKeys(t);
    },
    getOwnPropertyDescriptor(t, key) {
      log.push(`${prefix}descriptor:${label(key)}`);
      return Reflect.getOwnPropertyDescriptor(t, key);
    },
  });
}
