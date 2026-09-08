#!/usr/bin/env python3
"""Read-only SQL grammar — Python mirror of services/api/src/ro.ts. Used by ops/prod-read before any request
leaves the machine, and by the Worker again on arrival. Both are tested against ops/lib/ro_cases.json.

  ro_grammar.py --self-test      run every case, exit 1 on any disagreement with the case list
  ro_grammar.py "<sql>"          print OK or the refusal reason (exit 1)
"""
import json
import re
import sys
from pathlib import Path

PREFIX = re.compile(r"^\s*(EXPLAIN\s+(QUERY\s+PLAN\s+)?)?(SELECT|WITH)\b", re.I)
WRITE_WORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|REPLACE|DROP|ALTER|CREATE|ATTACH|DETACH|PRAGMA|VACUUM|REINDEX|GRANT|TRUNCATE|COPY)\b", re.I
)
MAX_SQL_LENGTH = 4000


def strip_strings(sql: str) -> str:
    sql = re.sub(r"'(?:[^']|'')*'", "''", sql)
    return re.sub(r'"(?:[^"]|"")*"', '""', sql)


def read_only_problem(sql):
    if not isinstance(sql, str) or not sql.strip():
        return "empty"
    if len(sql) > MAX_SQL_LENGTH:
        return f"longer than {MAX_SQL_LENGTH} chars"
    if not PREFIX.search(sql):
        return "must start with SELECT, WITH or EXPLAIN"
    bare = strip_strings(sql)
    if "--" in bare or "/*" in bare:
        return "comments not allowed"
    body = re.sub(r";\s*$", "", bare.strip())
    if ";" in body:
        return "exactly one statement"
    m = WRITE_WORDS.search(body)
    if m:
        return f"write keyword {m.group(1).upper()}"
    return None


def self_test():
    cases = json.loads((Path(__file__).with_name("ro_cases.json")).read_text(encoding="utf-8"))
    bad = []
    for sql in cases["accept"]:
        p = read_only_problem(sql)
        if p is not None:
            bad.append(f"should ACCEPT {sql!r} but refused: {p}")
    for sql in cases["reject"]:
        if read_only_problem(sql) is None:
            bad.append(f"should REJECT {sql!r} but accepted")
    n = len(cases["accept"]) + len(cases["reject"])
    if bad:
        print(f"RO-GRAMMAR FAIL {len(bad)}/{n}")
        for b in bad:
            print(" -", b)
        return 1
    print(f"RO-GRAMMAR OK {n} cases")
    return 0


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--self-test":
        sys.exit(self_test())
    problem = read_only_problem(sys.argv[1] if len(sys.argv) > 1 else "")
    print("OK" if problem is None else f"refused: {problem}")
    sys.exit(0 if problem is None else 1)
