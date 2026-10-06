#!/usr/bin/env python3
"""T-0284: ops/funnel, through its shipping entry point funnel.run - the function ops/funnel's main() calls.

    python ops/lib/funnel_test.py

Every expected output below is written by hand from the fixture rows (T-0284 R5), never computed by the module.
No test touches the network: --live runs against a stub HTTP callable (R6).
"""
from __future__ import annotations

import copy
import io
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

import funnel  # noqa: E402

ROOT = pathlib.Path(__file__).resolve().parents[2]
FIXTURE = ROOT / "Tests" / "Fixtures" / "t0284" / "ae_response.json"

NO_KEY = "cannot be computed: the dataset carries no per-device key (index1 = blob1 = event name, T-0279 R2)"
WINDOW = "FUNNEL scenic_telemetry, window: the last 28 days before the query (timestamp > NOW() - INTERVAL '28' DAY)"

# plan 1+3+1+1 = 6; preview 1+2+1+1 = 5 (5/6 = 83.33); drive 1+1+1 = 3 (3/5 = 60.0); answer 1+1+2 = 4
# (4/3 = 133.33); prettier 1+2 = 3 of 4 (75.0); other events: plan_result, drive_completed, handoff_tapped,
# surprise_shown, paywall_shown = 1+1+2+1+1 = 6 (handoff_tapped weighs 2); weight 6+5+3+4+6 = 24 over 19 rows.
EXPECTED = "\n".join([
    WINDOW,
    "rows 19, sampled weight 24, first 2026-09-08 09:00:00, last 2026-10-05 21:00:00",
    "plan_requested" + " " * 11 + "6",
    "preview_shown" + " " * 12 + "5" + "   83.3% of plan_requested",
    "drive_started" + " " * 12 + "3" + "   60.0% of preview_shown",
    "post_drive_answer" + " " * 8 + "4" + "  133.3% of drive_started",
    "prettier share" + " " * 7 + "75.0% (prettier 3, not_prettier 1)",
    "other events" + " " * 13 + "6",
    "W1 return" + " " * 11 + NO_KEY,
    "W4 return" + " " * 11 + NO_KEY,
]) + "\n"

EMPTY = "\n".join([
    WINDOW,
    "rows 0, sampled weight 0, first -, last -",
    "plan_requested" + " " * 11 + "0",
    "preview_shown" + " " * 12 + "0" + "     n/a of plan_requested",
    "drive_started" + " " * 12 + "0" + "     n/a of preview_shown",
    "post_drive_answer" + " " * 8 + "0" + "     n/a of drive_started",
    "prettier share" + " " * 9 + "n/a (prettier 0, not_prettier 0)",
    "other events" + " " * 13 + "0",
    "W1 return" + " " * 11 + NO_KEY,
    "W4 return" + " " * 11 + NO_KEY,
]) + "\n"

SQL = ("SELECT timestamp, index1, blob1, blob2, double1, double2, _sample_interval FROM scenic_telemetry "
       "WHERE timestamp > NOW() - INTERVAL '28' DAY ORDER BY timestamp FORMAT JSON")
ENV = {"ACCOUNT_ID": "acct0123", "AE_READ_TOKEN": "tok-SECRET-5678"}


def fixture() -> dict:
    return json.loads(FIXTURE.read_text(encoding="utf-8"))


def run(argv, env=None, http=None):
    out, err = io.StringIO(), io.StringIO()
    code = funnel.run(argv, env if env is not None else {}, http, out, err)
    return code, out.getvalue(), err.getvalue()


def run_body(body: dict, tmp: pathlib.Path):
    tmp.write_text(json.dumps(body), encoding="utf-8")
    return run(["--fixture", str(tmp)])


class StubHttp:
    def __init__(self, status: int, body: bytes):
        self.status, self.body, self.calls = status, body, []

    def __call__(self, url, headers, data):
        self.calls.append((url, headers, data))
        return self.status, self.body


class FunnelFixture(unittest.TestCase):
    def test_the_whole_printed_output_over_the_fixture_is_exact(self):
        self.assertEqual(run(["--fixture", str(FIXTURE)]), (0, EXPECTED, ""))

    def test_an_empty_window_prints_n_a_and_zeroes_exactly(self):
        tmp = ROOT / "Tests" / "Fixtures" / "t0284" / ".tmp-empty.json"
        try:
            body = fixture()
            body["data"], body["rows"], body["rows_before_limit_at_least"] = [], 0, 0
            self.assertEqual(run_body(body, tmp), (0, EMPTY, ""))
        finally:
            tmp.unlink(missing_ok=True)

    def test_the_sql_is_the_fixed_literal(self):
        self.assertEqual(funnel.SQL, SQL)

    def test_a_missing_fixture_path_exits_2_with_no_output(self):
        missing = ROOT / "Tests" / "Fixtures" / "t0284" / ".tmp-absent.json"
        missing.unlink(missing_ok=True)
        self.assertEqual(run(["--fixture", str(missing)]),
                         (2, "", "usage: cannot read the fixture (FileNotFoundError)\n"))

    def test_a_body_carrying_statistics_is_accepted_and_prints_the_same_output(self):
        tmp = ROOT / "Tests" / "Fixtures" / "t0284" / ".tmp-statistics.json"
        try:
            body = fixture()
            body["statistics"] = {"elapsed": 0.001, "rows_read": 19, "bytes_read": 1520}
            self.assertEqual(run_body(body, tmp), (0, EXPECTED, ""))
        finally:
            tmp.unlink(missing_ok=True)


class FunnelPercent(unittest.TestCase):
    def test_every_rounding_bound(self):
        table = [((0, 0), "n/a"), ((5, 0), "n/a"), ((0, 1), "0.0%"), ((1, 1), "100.0%"), ((1, 3), "33.3%"),
                 ((2, 3), "66.7%"), ((1, 8), "12.5%"), ((1, 16), "6.3%"), ((3, 16), "18.8%"),
                 ((1, 2000), "0.1%"), ((1, 2001), "0.0%"), ((1999, 2000), "100.0%"), ((3997, 4000), "99.9%"),
                 ((4, 3), "133.3%"), ((5, 6), "83.3%"), ((3, 5), "60.0%"), ((3, 4), "75.0%"),
                 ((7, 1), "700.0%"), ((10, 3), "333.3%")]
        self.assertEqual([(args, funnel.funnel_math.percent(*args)) for args, _ in table], table)


class FunnelRefusals(unittest.TestCase):
    """Each row: one fault in an otherwise valid response -> exit 4, nothing on stdout, a named reason."""

    def edit(self, change):
        body = fixture()
        change(body)
        tmp = ROOT / "Tests" / "Fixtures" / "t0284" / ".tmp-refusal.json"
        try:
            return run_body(body, tmp)
        finally:
            tmp.unlink(missing_ok=True)

    def test_every_fault_is_refused_with_exit_4_and_no_output(self):
        def row(i, **kv):
            return lambda b: b["data"][i].update(kv)

        def add_blob3(b):
            b["meta"].insert(4, {"name": "blob3", "type": "String"})
            for r in b["data"]:
                r["blob3"] = "850dab63fffffff"

        def drop_key(i, k):
            return lambda b: b["data"][i].pop(k)

        cases = {
            "the cell column blob3 in the response": add_blob3,
            "a column missing from meta": lambda b: b["meta"].pop(),
            "meta columns out of order": lambda b: b["meta"].insert(0, b["meta"].pop(1)),
            "a row missing a column": drop_key(0, "double2"),
            "a row with an extra column": row(0, blob3="850dab63fffffff"),
            "rows disagreeing with data": lambda b: b.update(rows=18),
            "an unexpected top-level key": lambda b: b.update(error="x"),
            "data not a list": lambda b: b.update(data={}),
            "meta missing": lambda b: b.pop("meta"),
            "an event name outside the fifteen": row(1, index1="plan_resulted", blob1="plan_resulted"),
            "index1 differing from blob1": row(2, index1="drive_started"),
            "a post_drive_answer label outside the enum": row(5, blob2="maybe"),
            "a post_drive_answer with an empty label": row(5, blob2=""),
            "a preview_shown label that is not empty": row(2, blob2="scenic"),
            "a drive_started label that is not empty": row(3, blob2="x"),
            "a plan_requested label outside the features": row(0, blob2="fastest"),
            "a weight of zero": row(0, _sample_interval=0),
            "a negative weight": row(0, _sample_interval=-1),
            "a fractional weight": row(0, _sample_interval=1.5),
            "a weight sent as a string": row(0, _sample_interval="1"),
            "a weight sent as a boolean": row(0, _sample_interval=True),
            "a double sent as a string": row(0, double1="30"),
            "a double sent as a boolean": row(0, double2=False),
            "a double that is NaN": row(0, double1=float("nan")),
            "a double that is Infinity": row(0, double2=float("inf")),
            "a blob that is not a string": row(2, blob2=0),
            "a timestamp in another format": row(0, timestamp="2026-09-08T09:00:00Z"),
            "a timestamp that is not a string": row(0, timestamp=1757322000),
        }
        got = {name: self.edit(change) for name, change in cases.items()}
        self.assertEqual({n: (c, o) for n, (c, o, _) in got.items()}, {n: (4, "") for n in cases})
        self.assertEqual({n: e.startswith("RESPONSE_REFUSED: ") for n, (_, _, e) in got.items()},
                         {n: True for n in cases})

    def test_a_body_that_is_not_json_is_refused(self):
        tmp = ROOT / "Tests" / "Fixtures" / "t0284" / ".tmp-notjson.json"
        try:
            tmp.write_text("{not json", encoding="utf-8")
            code, out, err = run(["--fixture", str(tmp)])
        finally:
            tmp.unlink(missing_ok=True)
        self.assertEqual((code, out, err.startswith("RESPONSE_REFUSED: ")), (4, "", True))


class FunnelLive(unittest.TestCase):
    def test_live_posts_the_fixed_sql_with_the_env_credentials_and_prints_the_same_output(self):
        stub = StubHttp(200, FIXTURE.read_bytes())
        self.assertEqual(run(["--live"], ENV, stub), (0, EXPECTED, ""))
        self.assertEqual(stub.calls, [(
            "https://api.cloudflare.com/client/v4/accounts/acct0123/analytics_engine/sql",
            {"Authorization": "Bearer tok-SECRET-5678"},
            SQL.encode("utf-8"))])

    def test_absent_or_empty_credentials_exit_3_naming_which_and_never_call_http(self):
        cases = {
            "both absent": ({}, "CREDENTIALS_ABSENT: ACCOUNT_ID, AE_READ_TOKEN not set in the environment\n"),
            "no account": ({"AE_READ_TOKEN": "t"}, "CREDENTIALS_ABSENT: ACCOUNT_ID not set in the environment\n"),
            "no token": ({"ACCOUNT_ID": "a"}, "CREDENTIALS_ABSENT: AE_READ_TOKEN not set in the environment\n"),
            "empty token": ({"ACCOUNT_ID": "a", "AE_READ_TOKEN": ""},
                            "CREDENTIALS_ABSENT: AE_READ_TOKEN not set in the environment\n"),
        }
        stub = StubHttp(200, FIXTURE.read_bytes())
        got = {name: run(["--live"], env, stub) for name, (env, _) in cases.items()}
        self.assertEqual(got, {name: (3, "", err) for name, (_, err) in cases.items()})
        self.assertEqual(stub.calls, [])

    def test_a_non_200_exits_5_with_the_status_only(self):
        stub = StubHttp(403, b'{"errors":[{"message":"tok-SECRET-5678 denied"}]}')
        self.assertEqual(run(["--live"], ENV, stub), (5, "", "HTTP_FAILED: status 403\n"))

    def test_credentials_are_never_taken_from_argv(self):
        for argv in (["--live", "--token", "x"], ["--live", "--account-id", "a"], ["--live", "x"], [],
                     ["--live", "--fixture", str(FIXTURE)]):
            code, out, _ = run(argv, ENV, StubHttp(200, FIXTURE.read_bytes()))
            self.assertEqual((argv, code, out), (argv, 2, ""))

    def test_the_token_is_never_printed(self):
        stub = StubHttp(200, FIXTURE.read_bytes())
        code, out, err = run(["--live"], ENV, stub)
        self.assertEqual((code, "tok-SECRET-5678" in out + err, "acct0123" in out + err), (0, False, False))


if __name__ == "__main__":
    unittest.main()
