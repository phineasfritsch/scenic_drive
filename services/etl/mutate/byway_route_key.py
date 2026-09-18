"""Mutation sweep and red demonstration for `etl.byway_route_key`'s floor - the check on the checks.

Tracked here rather than in gitignored `.artifacts/` for the reason `ops/mutate/routescore.py` gives: a
harness nobody else can run is red evidence nobody else can see. `ops/mutate/` is outside T-0028's
`touches:`, so it lives beside the code it mutates. Everything it writes goes under `work/` (gitignored):
it copies `services/etl` there, applies ONE textual mutation to the copy, runs the byway test files and
reads the JUnit XML - never a grep of stdout for failure wording - and `services/etl` itself is never
written. A mutation nothing catches is a check that is not there.

Round 5 (R7-01) found the previous harness returning None for an anchor it could not find while the
caller tested `if code == 0`, so a population of zero printed "every mutation was caught" and exited 0.
Here a mutation that does not apply is a hard failure; the applied count must EQUAL the declared
population before any verdict prints; the population is printed in the verdict line; and each mutation
must be killed BY THE TEST THAT NAMES IT - being caught by a neighbour tripping over the same edit is
reported as a failure too, because that neighbour is not the check the label claims exists.

    python mutate/byway_route_key.py                 # from services/etl: the whole population, exit 0 iff
                                                     # every declared mutation applied and was killed by name
    python mutate/byway_route_key.py M07 M09         # only labels containing these; the verdict says so
    python mutate/byway_route_key.py --red e19fd38   # current tests against THAT commit's
                                                     # byway_route_key.py: exit 0 iff pytest FAILED,
                                                     # 1 if it passed (the checks are about nothing),
                                                     # 2 if the tree could not be built or pytest could
                                                     # not run - a collection error is not a red
"""
from __future__ import annotations

import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

SRC = Path(__file__).resolve().parents[1]
MUT = SRC / "work" / "mutate-byway-route-key"
RK = "etl/byway_route_key.py"
BW = "etl/byways.py"
FIXTURE = "tests/fixtures/byway_miskey_fixture.json"
FILES = ["tests/test_byway_route_key.py", "tests/test_byway_miskey.py",
         "tests/test_byway_key_floor.py", "tests/test_byways.py"]
PYTEST = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-p", "no:randomly", "--tb=no"]

# (label, rel, old, new, tests that MUST go red). The names are the claim: this edit is what that test is
# for. `old` None is the vacuity mutation, which empties the fixture's ways instead of editing code.
MUTATIONS = [
    ("M01  vote the way's WHOLE length again (undo the along-the-corridor vote)", RK,
     "        reffed_m += along\n        for number in numbers:\n"
     "            out[number] = out.get(number, 0.0) + along",
     "        whole2 = snap.length_m(geom)\n        reffed_m += whole2\n        for number in numbers:\n"
     "            out[number] = out.get(number, 0.0) + whole2",
     ["test_a_way_votes_with_the_part_of_it_that_is_on_this_corridor",
      "test_a_crossing_way_votes_with_the_62_m_of_it_that_is_on_this_corridor"]),
    ("M02  count a concurrency twice into its own denominator", RK,
     "        reffed_m += along\n        for number in numbers:",
     "        for number in numbers:\n            reffed_m += along\n        for number in numbers:",
     ["test_a_concurrency_can_re_key_now_that_the_share_is_a_share_of_the_corridor"]),
    ("M03  drop `m > key_m` from _outvoting (a number that merely TIES takes the key)", RK,
     "if n not in key and m > key_m and _holds(m, reffed_m)",
     "if n not in key and _holds(m, reffed_m)",
     ["test_a_concurrency_that_names_the_key_is_corroborated_and_not_contested"]),
    ("M04  drop the metres floor from _holds (both sides at once)", RK,
     "    return m >= MIN_CONSENSUS_M and m >= MIN_CONSENSUS_SHARE * reffed_m",
     "    return m >= MIN_CONSENSUS_SHARE * reffed_m",
     ["test_a_short_stub_cannot_re_key_a_corridor"]),
    ("M05  drop the share floor from _holds (both sides at once)", RK,
     "    return m >= MIN_CONSENSUS_M and m >= MIN_CONSENSUS_SHARE * reffed_m",
     "    return m >= MIN_CONSENSUS_M",
     ["test_a_corridor_that_cannot_agree_keeps_its_key_and_is_reported"]),
    ("M06  the DEFENDING side loses the METRES floor", RK,
     "    key_holds = _holds(key_m, reffed_m)",
     "    key_holds = key_m >= MIN_CONSENSUS_SHARE * reffed_m",
     ["test_a_key_under_the_floor_is_printed_by_problems_because_reported_is_the_point"]),
    ("M07  the DEFENDING side loses the SHARE floor (round 4's rule: a bare metres floor)", RK,
     "    key_holds = _holds(key_m, reffed_m)",
     "    key_holds = key_m >= MIN_CONSENSUS_M",
     ["test_a_key_over_the_metres_floor_but_under_the_share_floor_is_re_keyed_not_contested",
      "test_fragments_worth_a_twelfth_of_the_key_evidence_cannot_hold_the_real_corridor"]),
    ("M08  the DEFENDING side back to bare membership (round 3's blocker)", RK,
     "    key_holds = _holds(key_m, reffed_m)",
     "    key_holds = key_m > 0",
     ["test_a_sub_floor_fragment_cannot_corroborate_a_key_no_rival_is_big_enough_to_take",
      "test_a_sub_floor_fragment_cannot_corroborate_a_key_on_a_corridor_that_cannot_agree",
      "test_a_fragment_cannot_silence_a_slice_of_the_real_corridor_no_number_can_win"]),
    ("M09  UNDER_EVIDENCED downgraded back to CORROBORATED, i.e. back to silence", RK,
     "        return (bw.KEY_UNDER_EVIDENCED if key_m > 0 else bw.KEY_UNCLAIMED), key",
     "        return (bw.KEY_CORROBORATED if key_m > 0 else bw.KEY_UNCLAIMED), key",
     ["test_a_key_under_the_floor_is_printed_by_problems_because_reported_is_the_point",
      "test_an_under_evidenced_key_is_not_the_same_verdict_as_one_nothing_claims_at_all",
      "test_mis_tagged_fragments_worth_a_fifth_of_the_evidence_stop_any_number_holding_it"]),
    ("M10  UNDER_EVIDENCED collapsed into UNCLAIMED (one verdict for two repairs)", RK,
     "        return (bw.KEY_UNDER_EVIDENCED if key_m > 0 else bw.KEY_UNCLAIMED), key",
     "        return bw.KEY_UNCLAIMED, key",
     ["test_an_under_evidenced_key_is_not_the_same_verdict_as_one_nothing_claims_at_all"]),
    ("M11  problems() stops printing the under-evidenced line", BW,
     "    thin = [b for b in byways if b.get(KEY_VERDICT) == KEY_UNDER_EVIDENCED]",
     "    thin = []",
     ["test_a_key_under_the_floor_is_printed_by_problems_because_reported_is_the_point"]),
    ("M12  problems() counts distinct route-key STRINGS again (RV7-5)", BW,
     '        out.append(f"{len(rekeyed_entries)} byway(s) carrying route key(s) {keys} were claimed',
     '        out.append(f"{len(keys)} byway(s) carrying route key(s) {keys} were claimed',
     ["test_problems_counts_the_byways_affected_not_the_distinct_route_numbers"]),
    ("M13  key_claim_m stamped only on the loud verdicts again (RV7-3)", RK,
     "        if key:\n            fixed[\"key_claim_m\"]",
     "        if verdict in (bw.KEY_REKEYED, bw.KEY_CONTESTED):\n            fixed[\"key_claim_m\"]",
     ["test_every_keyed_entry_records_what_the_key_held_and_what_it_was_a_share_of"]),
    ("M14  _holds becomes a bare membership test for BOTH sides", RK,
     "    return m >= MIN_CONSENSUS_M and m >= MIN_CONSENSUS_SHARE * reffed_m",
     "    return m > 0",
     ["test_the_key_and_a_rival_are_judged_by_the_same_function_on_the_same_evidence"]),
    ("M15  cap each vote at the corridor length (RV7-4's tempting repair)", RK,
     "        along, whole = snap.overlap_m(geom, line, tolerance_m)\n"
     "        if whole <= 0 or along / whole < min_overlap:\n            continue",
     "        along, whole = snap.overlap_m(geom, line, tolerance_m)\n"
     "        if whole <= 0 or along / whole < min_overlap:\n            continue\n"
     "        along = min(along, snap.length_m(line))",
     ["test_a_way_doubling_back_votes_more_metres_than_the_corridor_is_long"]),
    ("M16  problems() stops printing the contested line", BW,
     "    contested_entries = [b for b in byways if b.get(KEY_VERDICT) == KEY_CONTESTED]",
     "    contested_entries = []",
     ["test_a_key_that_holds_its_corridor_and_is_still_outvoted_is_reported_not_guessed_about"]),
    ("M17  CONTESTED never happens - re-key whenever anything outvotes the key", RK,
     "    return bw.KEY_CONTESTED, key",
     "    return bw.KEY_REKEYED, outvoting",
     ["test_a_key_that_holds_its_corridor_and_is_still_outvoted_is_reported_not_guessed_about"]),
    ("M18  nothing under the bar is ever reported - corroborate it all", RK,
     "        return (bw.KEY_UNDER_EVIDENCED if key_m > 0 else bw.KEY_UNCLAIMED), key",
     "        return bw.KEY_CORROBORATED, key",
     ["test_a_short_stub_cannot_re_key_a_corridor",
      "test_a_key_under_the_floor_is_printed_by_problems_because_reported_is_the_point"]),
    ("V1   the fixture carries no ways at all (a census measured on nothing)", FIXTURE, None, None,
     ["test_the_census_the_re_key_argument_rests_on_is_reproduced_by_the_code"]),
]
# The EXACT declared population, two-sided: below it something was deleted, above it a mutation was added
# and this number was not raised with it. Adding one costs one more edited line in the same commit.
EXPECTED_MUTATIONS = 19


def fresh_copy() -> None:
    """A copy of services/etl under work/, minus the 1.3 GB `inputs` none of these tests read."""
    if MUT.exists():
        shutil.rmtree(MUT)
    shutil.copytree(SRC, MUT, ignore=shutil.ignore_patterns("__pycache__", "work", ".pytest_cache",
                                                            "inputs", "mutate"))


def apply(rel: str, old: str | None, new: str | None) -> bool:
    """Write one mutant into the copy. False when the anchor is not there exactly once - a hard failure."""
    fresh_copy()
    target = MUT / rel
    text = target.read_text(encoding="utf-8")
    if old is None:                                    # the vacuity mutation: empty the fixture's ways
        text2 = re.sub(r'"ways": \[.*?\n \],', '"ways": [],', text, count=1, flags=re.S)
    elif text.count(old) != 1:
        print(f"    DID NOT APPLY - anchor appears {text.count(old)} times, not once")
        return False
    else:
        text2 = text.replace(old, new)
    if text2 == text:
        print("    DID NOT APPLY - the replacement left the file unchanged")
        return False
    target.write_text(text2, encoding="utf-8", newline="\n")
    return True


def failures(xml: Path) -> list[str]:
    """The test NAMES that failed or errored, read from the JUnit XML rather than grepped from stdout."""
    if not xml.exists():
        return []
    return [tc.get("name") for tc in ET.parse(xml).getroot().iter("testcase")
            if tc.find("failure") is not None or tc.find("error") is not None]


def run(cwd: Path, files: list[str], xml: Path) -> tuple[int, list[str]]:
    p = subprocess.run([*PYTEST, f"--junitxml={xml}", *files], cwd=cwd, capture_output=True, text=True)
    return p.returncode, failures(xml)


def sweep(wanted: list[str]) -> int:
    if len(MUTATIONS) != EXPECTED_MUTATIONS:
        print(f"REFUSED: this file declares {EXPECTED_MUTATIONS} mutations and carries {len(MUTATIONS)};"
              f" a population nobody stated is a verdict nobody can read")
        return 1
    population = [m for m in MUTATIONS if not wanted or any(w in m[0] for w in wanted)]
    if not population:
        print("REFUSED: no mutations selected - an empty population cannot demonstrate anything")
        return 1
    (SRC / "work").mkdir(exist_ok=True)
    code, failed = run(SRC, FILES, SRC / "work" / "mutate-byway-route-key-baseline.xml")
    print(f"BASELINE (unmutated)  pytest exit={code}  {len(failed)} failed")
    if code != 0:
        print("REFUSED: baseline is not green - fix that before reading any mutation result")
        return 1
    applied, unapplied, survivors, wrong_killer = 0, [], [], []
    for label, rel, old, new, killers in population:
        print(label)
        if not apply(rel, old, new):
            unapplied.append(label)
            continue
        applied += 1
        code, failed = run(MUT, FILES if rel != FIXTURE else ["tests/test_byway_miskey.py"],
                           MUT / "mut.xml")
        red = [k for k in killers if k in failed]
        print(f"    pytest exit={code}  {len(failed)} failed  named killer(s) red: {red}")
        if code == 0:
            survivors.append(label)
        elif len(red) != len(killers):
            wrong_killer.append(label)
            print(f"    NAMED TEST DID NOT GO RED: {[k for k in killers if k not in failed]}"
                  f"\n    (failed instead: {failed[:6]})")
    print(f"\nPOPULATION {len(population)} of {len(MUTATIONS)} known mutations"
          f"{' (filtered by ' + ' '.join(wanted) + ')' if wanted else ''}; APPLIED {applied}")
    bad = False
    for title, items in [(f"REFUSED: {len(population) - applied} mutation(s) never applied - a verdict "
                          f"over a smaller population than the one this file declares says nothing:",
                          unapplied),
                         ("SURVIVED (nothing catches these):", survivors),
                         ("CAUGHT, BUT NOT BY THE TEST THAT NAMES IT:", wrong_killer)]:
        if items:
            bad = True
            print(title)
            for s in items:
                print("   ", s)
    if bad:
        return 1
    print(f"every one of the {applied} applied mutations was killed by the test that names it")
    return 0


def red(base: str) -> int:
    """The current tests against `base`'s byway_route_key.py. Exit 0 iff they FAIL, which is the point."""
    fresh_copy()
    show = subprocess.run(["git", "show", f"{base}:services/etl/{RK}"], cwd=SRC, capture_output=True,
                          text=True)
    if show.returncode != 0:
        print(f"REFUSED: git show {base}:services/etl/{RK} failed - no tree to be red against")
        return 2
    (MUT / RK).write_text(show.stdout, encoding="utf-8", newline="\n")
    code, failed = run(MUT, FILES[:3], MUT / "red.xml")
    for name in failed:
        print(f"  RED  {name}")
    print(f"PYTEST EXIT={code}  {len(failed)} failed  (base={base})")
    if code == 0:
        print("REFUSED: every check PASSED against the pre-fix code, so none of them is about the fix")
        return 1
    if code > 1:
        print(f"REFUSED: pytest could not run (exit {code}) - a collection error is not a demonstration")
        return 2
    print(f"RED as intended against {base}: {len(failed)} named test(s) fail without the fix")
    return 0


if __name__ == "__main__":
    args = sys.argv[1:]
    if args[:1] == ["--red"]:
        if len(args) != 2:
            raise SystemExit("usage: --red <commit>")
        raise SystemExit(red(args[1]))
    raise SystemExit(sweep(args))
