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


MIN_CASES = 26          # exactly the 26 present. At 20, six could be deleted with the floor still green.
MIN_LENGTH_PROBES = 2   # at least one under the cap and one over it; a floor on the probes actually RUN.


def check_length_probes(cases, bad):
    """Bound the MAGNITUDE of MAX_SQL_LENGTH against fixed literals. Returns how many assertions ran.

    The two length cases this replaces were built from the cap itself - "SELECT " + "1," * shared_cap and
    "SELECT " + "1" * (shared_cap - 10) - so they were longer/shorter than the cap for EVERY value of it and
    could not fail. Raising the cap 4000 -> 400000 in this file and in ro_cases.json together printed the
    byte-identical "RO-GRAMMAR OK 29 cases" at exit 0 while read_only_problem accepted 100,007 characters.
    The probe lengths now come from ro_cases.json, which is data: JSON cannot compute, so they cannot be
    re-derived from the value they bound. Equality with ro_cases.json's cap is a separate assertion; it
    catches drift between the mirrors and cannot catch a coordinated raise of both.
    """
    probes = cases.get("length_probes")
    if not isinstance(probes, list) or len(probes) < MIN_LENGTH_PROBES:
        n = len(probes) if isinstance(probes, list) else 0
        bad.append(f"ro_cases.json carries {n} length probe(s) (expected >= {MIN_LENGTH_PROBES}) - with none "
                   f"of them nothing here bounds the MAGNITUDE of MAX_SQL_LENGTH, only its agreement with "
                   f"ro_cases.json, and a raise applied to both sails through")
        return 0
    for p in probes:
        if not isinstance(p, dict) or not isinstance(p.get("chars"), int) or p["chars"] < 8 \
                or p.get("expect") not in ("accept", "reject"):
            bad.append(f"malformed length probe {p!r} - want {{'chars': <int >= 8>, 'expect': 'accept'|'reject'}}")
            return 0
    under = [p["chars"] for p in probes if p["expect"] == "accept"]
    over = [p["chars"] for p in probes if p["expect"] == "reject"]
    if not under or not over:
        bad.append(f"length probes must bracket the cap: {len(under)} accept and {len(over)} reject probe(s) "
                   f"- probing one side only cannot see the cap move the other way")
        return 0
    ran = 0
    if not max(under) <= MAX_SQL_LENGTH < min(over):
        bad.append(f"MAX_SQL_LENGTH is {MAX_SQL_LENGTH}, outside the fixed probe bracket "
                   f"[{max(under)}, {min(over)}) - the cap's MAGNITUDE moved, not just its spelling")
    ran += 1
    for p in probes:
        sql = "SELECT " + "1" * (p["chars"] - 7)
        problem = read_only_problem(sql)
        if p["expect"] == "reject":
            # "refused for SOME reason" is not the assertion. The probe has to trip the LENGTH rule, or it
            # stays green while that rule is deleted and some other gate happens to catch the statement.
            # services/api/test/ro.test.ts asserts the same thing with toMatch(/longer/).
            if problem is None:
                bad.append(f"should REJECT a statement of exactly {p['chars']} chars but accepted it")
            elif "longer than" not in problem:
                bad.append(f"rejected a {p['chars']}-char statement for the wrong reason: {problem!r} - the "
                           f"length rule is what this probe exists to exercise")
        elif problem is not None:
            bad.append(f"should ACCEPT a statement of exactly {p['chars']} chars but refused: {problem}")
        ran += 1
    return ran


def self_test():
    cases = json.loads((Path(__file__).with_name("ro_cases.json")).read_text(encoding="utf-8"))
    bad = []
    # The population must be non-empty before any of it means anything. Emptying accept/reject printed
    # `RO-GRAMMAR OK 3 cases` and exited 0 - the shared case file is the whole grammar contract, and a run
    # that checked three synthetic length cases is not a run that checked the grammar.
    shared = len(cases.get("accept") or []) + len(cases.get("reject") or [])
    if shared < MIN_CASES:
        bad.append(f"only {shared} shared case(s) in ro_cases.json (expected >= {MIN_CASES}) - the file is "
                   f"the contract both implementations run, and an empty one proves nothing")
    # The cap is the one rule the shared case list could not express, because a case long enough to trip it
    # would be 4000 characters of JSON. So the file carries the NUMBER and both implementations assert their
    # own literal against it - services/api/test/ro.test.ts does the same. Without this the two constants
    # agreed only by luck, and nothing anywhere compared them. This is a DRIFT check only: both sides raised
    # together still satisfy it, which is why check_length_probes() exists.
    shared_cap = cases.get("max_sql_length")
    if shared_cap != MAX_SQL_LENGTH:
        bad.append(f"MAX_SQL_LENGTH is {MAX_SQL_LENGTH} but ro_cases.json says {shared_cap!r} - the "
                   f"TypeScript mirror asserts the same number, so these two have drifted apart")
    # Independent of the drift check, and it must run even when the two caps disagree.
    probes_ran = check_length_probes(cases, bad)
    for sql in cases["accept"]:
        p = read_only_problem(sql)
        if p is not None:
            bad.append(f"should ACCEPT {sql!r} but refused: {p}")
    for sql in cases["reject"]:
        if read_only_problem(sql) is None:
            bad.append(f"should REJECT {sql!r} but accepted")
    # +1 for the drift assertion, plus however many length probes actually RAN. A probe list that is empty,
    # malformed or one-sided runs none, and the denominator has to say so: counting them unconditionally
    # reported 29 for a run in which 27 checks happened.
    n = len(cases["accept"]) + len(cases["reject"]) + 1 + probes_ran
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
