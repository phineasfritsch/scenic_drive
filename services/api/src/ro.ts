/**
 * Read-only SQL grammar for /__ro and ops/prod-read.
 *
 * Mirrored in ops/lib/ro_grammar.py. Both run every case in ops/lib/ro_cases.json and both assert their
 * own MAX_SQL_LENGTH equals that file's `max_sql_length`, so neither the rules nor the cap can drift.
 * The cap needs its own assertion because a case long enough to exercise it would be 4000 characters of
 * JSON - and until T-0083 the Python mirror was run by nothing at all: `ops/test` and `pins/PINS.yaml`
 * had zero references to it, so it could be made to accept `DROP TABLE users` with the suite green.
 * ops/test now runs `ro_grammar.py --self-test`.
 * Allowlist, not denylist: exactly one statement, starting with SELECT / WITH / EXPLAIN, and no write keyword
 * anywhere outside string literals (SQLite allows `WITH ... INSERT`, so the prefix alone is not enough).
 */
const PREFIX = /^\s*(EXPLAIN\s+(QUERY\s+PLAN\s+)?)?(SELECT|WITH)\b/i;
const WRITE_WORDS = /\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|GRANT|TRUNCATE|COPY)\b/i;
export const MAX_SQL_LENGTH = 4000;

/** Strip single- and double-quoted string literals so keywords inside them do not count. */
export function stripStrings(sql: string): string {
  return sql.replace(/'(?:[^']|'')*'/g, "''").replace(/"(?:[^"]|"")*"/g, '""');
}

export function readOnlyProblem(sql: string): string | null {
  if (typeof sql !== "string" || sql.trim().length === 0) return "empty";
  if (sql.length > MAX_SQL_LENGTH) return `longer than ${MAX_SQL_LENGTH} chars`;
  if (!PREFIX.test(sql)) return "must start with SELECT, WITH or EXPLAIN";
  const bare = stripStrings(sql);
  if (bare.includes("--") || bare.includes("/*")) return "comments not allowed";
  const body = bare.trim().replace(/;\s*$/, "");
  if (body.includes(";")) return "exactly one statement";
  const m = WRITE_WORDS.exec(body);
  if (m) return `write keyword ${m[1].toUpperCase()}`;
  return null;
}

export function isReadOnly(sql: string): boolean {
  return readOnlyProblem(sql) === null;
}
