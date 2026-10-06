"""T-0284's arithmetic: weighted step counts, step conversion, prettier share, and the printed lines.

Input is the validated rows funnel.py hands over - (timestamp, event name, label, weight) tuples, the H3 cell never
among them (R3). Counts are event TOTALS weighted by AE's _sample_interval (R5); there is no device or session key
in the dataset (R1), so W1/W4 return is printed as not computable, never estimated.
"""
from __future__ import annotations

FUNNEL_STEPS = ("plan_requested", "preview_shown", "drive_started", "post_drive_answer")
ANSWERS = ("prettier", "not_prettier")
NO_DEVICE_KEY = "cannot be computed: the dataset carries no per-device key (index1 = blob1 = event name, T-0279 R2)"
WINDOW_LINE = ("FUNNEL scenic_telemetry, window: the last 28 days before the query "
               "(timestamp > NOW() - INTERVAL '28' DAY)")
NAME_WIDTH = 20
COUNT_WIDTH = 6
PERCENT_WIDTH = 6


def percent(num: int, den: int) -> str:
    """num / den as a percent to one decimal, rounded half up in integer arithmetic; n/a when den is 0."""
    if den == 0:
        return "n/a"
    tenths = (2000 * num + den) // (2 * den)
    return f"{tenths // 10}.{tenths % 10}%"


def tally(rows) -> dict:
    """{'steps': {step: weight}, 'answers': {answer: weight}, 'other': weight, 'rows': n, 'weight': total,
    'first': ts or None, 'last': ts or None}."""
    steps = {step: 0 for step in FUNNEL_STEPS}
    answers = {answer: 0 for answer in ANSWERS}
    other = 0
    total = 0
    first = last = None
    for timestamp, name, label, weight in rows:
        total += weight
        if first is None or timestamp < first:
            first = timestamp
        if last is None or timestamp > last:
            last = timestamp
        if name in steps:
            steps[name] += weight
            if name == "post_drive_answer":
                answers[label] += weight
        else:
            other += weight
    return {"steps": steps, "answers": answers, "other": other, "rows": len(rows), "weight": total,
            "first": first, "last": last}


def render(summary: dict) -> list[str]:
    """The whole printed output, one string per line."""
    lines = [WINDOW_LINE,
             f"rows {summary['rows']}, sampled weight {summary['weight']}, "
             f"first {summary['first'] or '-'}, last {summary['last'] or '-'}"]
    steps = summary["steps"]
    previous = None
    for step in FUNNEL_STEPS:
        line = f"{step:<{NAME_WIDTH}}{steps[step]:>{COUNT_WIDTH}}"
        if previous is not None:
            line += f"  {percent(steps[step], steps[previous]):>{PERCENT_WIDTH}} of {previous}"
        lines.append(line)
        previous = step
    prettier, not_prettier = summary["answers"]["prettier"], summary["answers"]["not_prettier"]
    share = percent(prettier, prettier + not_prettier)
    lines.append(f"{'prettier share':<{NAME_WIDTH}}{share:>{COUNT_WIDTH}} "
                 f"(prettier {prettier}, not_prettier {not_prettier})")
    lines.append(f"{'other events':<{NAME_WIDTH}}{summary['other']:>{COUNT_WIDTH}}")
    lines.append(f"{'W1 return':<{NAME_WIDTH}}{NO_DEVICE_KEY}")
    lines.append(f"{'W4 return':<{NAME_WIDTH}}{NO_DEVICE_KEY}")
    return lines
