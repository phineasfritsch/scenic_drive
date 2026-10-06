"""The mutation population for ops/funnel's arithmetic (T-0284 R7). The runner is ops/lib/funnel_mutate.py.

This file is data: no `__main__`, so P-PROC-06's DRIVERS whitelist (ops/lib/mutate_population_table.py) does not
read it. That gate's MODULE_ROOTS are services/etl/etl and Sources only and it refuses a SUBJECT_MODULES entry
outside them, so an ops/lib module cannot be a registered driver; the floor below is enforced by the runner.

Each entry is `(name, path, old, new, killers)`. `old` must occur EXACTLY ONCE, verbatim, in the pristine file or
the run fails (SKIP); no anchor is a comment. `killers` are `Class.test_method` ids in ops/lib/funnel_test.py and
EVERY named killer must go red for the entry to count as caught.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
MATH = ROOT / "ops" / "lib" / "funnel_math.py"
READER = ROOT / "ops" / "lib" / "funnel.py"

MIN_MUTATIONS = 22

WHOLE = "FunnelFixture.test_the_whole_printed_output_over_the_fixture_is_exact"
LIVE = "FunnelLive.test_live_posts_the_fixed_sql_with_the_env_credentials_and_prints_the_same_output"
EMPTY = "FunnelFixture.test_an_empty_window_prints_n_a_and_zeroes_exactly"
BOUNDS = "FunnelPercent.test_every_rounding_bound"
REFUSALS = "FunnelRefusals.test_every_fault_is_refused_with_exit_4_and_no_output"

MUTATIONS = [
    ("percent: the zero-denominator guard moved to 1", MATH,
     "if den == 0:", "if den == 1:", [BOUNDS, EMPTY]),
    ("percent: truncates instead of rounding half up", MATH,
     "(2000 * num + den) // (2 * den)", "(2000 * num) // (2 * den)", [BOUNDS]),
    ("percent: rounds up one step early", MATH,
     "(2000 * num + den) // (2 * den)", "(2000 * num + den + 1) // (2 * den)", [BOUNDS]),
    ("percent: scaled to tenths of a whole, not of a percent", MATH,
     "(2000 * num + den) // (2 * den)", "(200 * num + den) // (2 * den)", [BOUNDS, WHOLE]),
    ("percent: the decimal digit taken mod 9", MATH,
     "{tenths % 10}%", "{tenths % 9}%", [BOUNDS]),
    ("percent: the whole part rounded instead of floored", MATH,
     "{tenths // 10}.", "{round(tenths / 10)}.", [BOUNDS]),
    ("tally: a step counts rows, not their sample weight", MATH,
     "steps[name] += weight", "steps[name] += 1", [WHOLE, LIVE]),
    ("tally: an answer counts rows, not their sample weight", MATH,
     "answers[label] += weight", "answers[label] += 1", [WHOLE]),
    ("tally: other events count rows, not their sample weight", MATH,
     "other += weight", "other += 1", [WHOLE]),
    ("tally: the total weight counts rows", MATH,
     "total += weight", "total += 1", [WHOLE]),
    ("tally: first keeps the latest timestamp", MATH,
     "timestamp < first", "timestamp > first", [WHOLE]),
    ("tally: last keeps the earliest timestamp", MATH,
     "timestamp > last", "timestamp < last", [WHOLE]),
    ("tally: post_drive_answer never reaches the answers", MATH,
     "if name == \"post_drive_answer\":", "if name == \"post_drive_answers\":", [WHOLE]),
    ("tally: the row count is the weight", MATH,
     "\"rows\": len(rows)", "\"rows\": total", [WHOLE]),
    ("render: every step converted against plan_requested", MATH,
     "percent(steps[step], steps[previous])", "percent(steps[step], steps[FUNNEL_STEPS[0]])", [WHOLE]),
    ("render: conversion inverted", MATH,
     "percent(steps[step], steps[previous])", "percent(steps[previous], steps[step])", [WHOLE]),
    ("render: prettier share over prettier twice", MATH,
     "percent(prettier, prettier + not_prettier)", "percent(prettier, prettier + prettier)", [WHOLE]),
    ("render: prettier share of not_prettier", MATH,
     "percent(prettier, prettier + not_prettier)", "percent(not_prettier, prettier + not_prettier)", [WHOLE]),
    ("reader: a weight of zero accepted", READER,
     "weight < 1", "weight < 0", [REFUSALS]),
    ("reader: a boolean weight accepted", READER,
     "not isinstance(weight, int) or isinstance(weight, bool) or", "not isinstance(weight, int) or", [REFUSALS]),
    ("reader: rows larger than data refused only one way", READER,
     "top[\"rows\"] != len(data)", "top[\"rows\"] > len(data)", [REFUSALS]),
    ("reader: a non-finite double accepted", READER,
     "and math.isfinite(value)", "and True", [REFUSALS]),
]
