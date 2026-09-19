"""Mutation harness for the ETL geometry terms - etl/sinuosity.py, etl/proximity.py, etl/snap.py.

A catch requires a NAMED TEST to fail, and to be the test whose label claims that check exists. Tracked in
ops/ rather than .artifacts/ for the reason ops/mutate/budget.py gives: a harness nobody else can run is red
evidence nobody else can see. The protocol is budget.py's; the subject here is Python, so the verdict comes
from pytest's JUnit XML rather than from a grep of stdout, and the mutant is written into a COPY.

    python ops/mutate/geometry.py                 # the whole population; exit 0 iff every mutation applied
                                                  # and was killed by the test that names it, and every
                                                  # EQUIVALENT entry went MISSED with an identical digest
    python ops/mutate/geometry.py --prove-floor   # the floor, demonstrated rather than asserted. No pytest
    python ops/mutate/geometry.py --non-example   # round 3's retracted "equivalent in the plane" ruling,
                                                  # run through the EQUIVALENT arm's own test and refuted

THE FOUR FILES. This one is the protocol - what a verdict is and what refuses. geometry_mutations.py is the
population that must be CAUGHT, with the CLASS each entry stands for; geometry_arms.py is the arm asserted
the other way round, the EQUIVALENT mutants, each with a reason and a computed witness; geometry_tree.py is
what the run does to the filesystem. Split at the 300-line cap along those boundaries of meaning, exactly as
budget.py is split into budget_mutations.py, budget_arms.py, budget_tree.py and budget_paths.py.

WHAT IS MUTATED, AND WHERE: never the worktree. See geometry_tree.py - `services/etl` is copied into the
gitignored .build-mutate-geometry/, one textual mutation is written into the COPY, pytest runs there, and
`git status` over services/etl is untouched by a full sweep. There is no restore step to race with.

THE FLOOR IS TWO-SIDED, and that is this file's one addition to budget.py's protocol. A count alone would
not have stopped any of the four review rounds PR #94 bought: each round's population was complete by its
own count and empty on the next axis of the segment-pair matrix. So `REQUIRED_CLASSES` in
geometry_mutations.py is a literal list of the six classes and every one of them must be populated - a
population that has lost its last banded-subset entry REFUSES, naming the class, instead of reporting a
clean sheet over five sixths of the failure space.
"""
from __future__ import annotations

import pathlib
import sys

# The population lives next to this file, not on the caller's sys.path: `python ops/mutate/geometry.py` from
# the repo root and `./ops/mutate/geometry.py` must both find it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))

from geometry_arms import EQUIVALENT, MIN_EQUIVALENT
from geometry_mutations import (INDEXED, MIN_MUTATIONS, MUTATIONS, PAIR_LOOP, PROX, REQUIRED_CLASSES,
                                TEST_FILES)
from geometry_tree import COPY, apply, fingerprint, fingerprint_of_pristine, run_tests

# Round 3's ruling, kept out of MUTATIONS' way so `--non-example` can run the exact edit that was written
# into the PR #94 task file as settled fact. It is also in MUTATIONS, in the interior-interior class.
NON_EXAMPLE = ("round 3: drop the pairs interior to both polylines - 'equivalent in the plane'",
               PROX, PAIR_LOOP, INDEXED % " if i in (0, n - 1) or j in (0, m - 1)")


def red_by_name(killers: list[str], failed: list[str]) -> list[str]:
    """The killers that went red. A parametrised test is named without its `[case]` suffix in the
    population and every parametrisation of it counts - `test_x[a]` is still `test_x` going red."""
    return [k for k in killers if any(f == k or (f or "").startswith(k + "[") for f in failed)]


def population_ok() -> bool:
    """The floor, two-sided. `every mutation was caught` is satisfied by an EMPTY list - 0 of 0, exit 0, the
    cleanest sheet this file can print - so a count is a floor. A count is not enough on its own here: four
    review rounds of PR #94 each had a complete population by its own count and nothing at all on the next
    axis, so every class in REQUIRED_CLASSES must be populated too, and a missing one is named."""
    bad = []
    if len(MUTATIONS) < MIN_MUTATIONS:
        bad.append("MUTATIONS has %d, floor is %d" % (len(MUTATIONS), MIN_MUTATIONS))
    if len(EQUIVALENT) < MIN_EQUIVALENT:
        bad.append("EQUIVALENT has %d, floor is %d" % (len(EQUIVALENT), MIN_EQUIVALENT))
    present = {m[0] for m in MUTATIONS}
    for name in REQUIRED_CLASSES:
        if name not in present:
            bad.append("no mutation left in class '%s' - that whole axis is unmeasured" % name)
    for m in MUTATIONS:
        if m[0] not in REQUIRED_CLASSES:
            bad.append("mutation '%s' is in class '%s', which is not one of the declared classes"
                       % (m[1], m[0]))
    for b in bad:
        sys.stdout.write("POPULATION FLOOR: %s. A shrunken population must never read as a clean sheet.\n" % b)
    return not bad


def prove_floor() -> int:
    """`--prove-floor`: demonstrate the floor instead of asserting it, at no pytest cost. FOUR arms, because
    they are four different claims - emptied, one entry short (the quiet trim a slack floor never sees), one
    CLASS deleted (the shape this harness exists for), and the real population, which must pass."""
    global MUTATIONS, EQUIVALENT
    real = (list(MUTATIONS), list(EQUIVALENT))
    dropped = REQUIRED_CLASSES[-1]
    try:
        MUTATIONS, EQUIVALENT = [], []
        sys.stdout.write("with the population emptied:\n")
        refused_empty = not population_ok()

        MUTATIONS, EQUIVALENT = real[0][:-1], real[1][:-1]
        sys.stdout.write("with one mutation and one equivalent deleted (%d, %d):\n"
                         % (len(MUTATIONS), len(EQUIVALENT)))
        refused_short = not population_ok()

        # The class arm is only worth having if it refuses something the COUNT arm does not, so the
        # deleted class is traded for copies of a surviving one and the population is left AT the floor:
        # twelve mutations, six classes declared, five measured. That trade is what four review rounds of
        # PR #94 were, one axis at a time, and no count can see it.
        kept = [m for m in real[0] if m[0] != dropped]
        MUTATIONS = kept + [kept[0]] * (MIN_MUTATIONS - len(kept))
        EQUIVALENT = real[1]
        sys.stdout.write("with class '%s' traded for copies of '%s', population still %d:\n"
                         % (dropped, kept[0][0], len(MUTATIONS)))
        refused_class = not population_ok()
    finally:
        MUTATIONS, EQUIVALENT = real
    sys.stdout.write("with the real population (%d mutations over %d classes, %d equivalent):\n"
                     % (len(MUTATIONS), len({m[0] for m in MUTATIONS}), len(EQUIVALENT)))
    restored = population_ok()
    ok = refused_empty and refused_short and refused_class and restored
    sys.stdout.write("FLOOR PROOF %s: emptied -> refused=%s, one deleted -> refused=%s, class '%s' deleted "
                     "-> refused=%s, real -> accepted=%s\n"
                     "  (without the count arm an emptied population reads 0 of 0 and exits 0; without the\n"
                     "   class arm a population complete by its own count can be empty on a whole axis of\n"
                     "   the segment-pair matrix, which is the review round PR #94 bought four times)\n"
                     % ("OK" if ok else "FAILED", refused_empty, refused_short, dropped, refused_class,
                        restored))
    return 0 if ok else 1


def non_example() -> int:
    """`--non-example`: round 3's "equivalent in the plane" ruling, put through the EQUIVALENT arm's own
    test. An entry there passes only on an identical digest AND no named test red; this one fails both."""
    label, rel, old, new = NON_EXAMPLE
    base_digest, base_n, base_out = fingerprint_of_pristine()
    sys.stdout.write("THE NON-EXAMPLE: %s\n  %s\n" % (label, rel))
    if not apply(rel, old, new):
        return 2
    digest, n, out = fingerprint(COPY)
    code, failed = run_tests(COPY, "non-example")
    differ = [(a, b) for a, b in zip(base_out.splitlines(), out.splitlines()) if a != b]
    sys.stdout.write("  pristine digest %s over %d values\n  mutant   digest %s over %d values\n"
                     % (base_digest, base_n, digest, n))
    for a, b in differ[:4]:
        sys.stdout.write("  pristine  %s\n  mutant    %s\n" % (a.strip(), b.strip()))
    sys.stdout.write("  %d of %d fingerprint values differ; %d named test(s) red\n"
                     % (len(differ), base_n, len(failed)))
    for name in failed[:6]:
        sys.stdout.write("    RED  %s\n" % name)
    ok = bool(differ) and code != 0
    sys.stdout.write("NON-EXAMPLE %s: the round-3 ruling is REFUTED by this arm's own test - it is a\n"
                     "  mutation (interior-interior class), not an equivalent mutant.\n"
                     % ("OK" if ok else "FAILED - it now looks equivalent, which would be news"))
    return 0 if ok else 1


def sweep() -> int:
    if not population_ok():
        return 2
    base_digest, base_n, _ = fingerprint_of_pristine()
    code, failed = run_tests(COPY, "baseline")
    sys.stdout.write("BASELINE  %d test files, pytest exit=%d, %d failed; fingerprint %s over %d values\n"
                     % (len(TEST_FILES), code, len(failed), base_digest, base_n))
    if code != 0:
        sys.stdout.write("REFUSED: the baseline is not green; nothing below would mean anything\n")
        return 2

    unapplied, survivors, wrong_killer = [], [], []
    sys.stdout.write("\nMUTATIONS - each must be killed BY THE TEST THAT NAMES IT\n")
    for mclass, label, rel, old, new, killers in MUTATIONS:
        sys.stdout.write("%-18s %s\n" % (mclass, label))
        if not apply(rel, old, new):
            unapplied.append(label)
            continue
        digest, _, _ = fingerprint(COPY)
        code, failed = run_tests(COPY, "mutant")
        red = red_by_name(killers, failed)
        sys.stdout.write("    exit=%d  %2d red  fingerprint %s (%s)  named red: %s\n"
                         % (code, len(failed), digest,
                            "differs" if digest != base_digest else "IDENTICAL", red))
        if code == 0:
            survivors.append(label)
        elif len(red) != len(killers):
            wrong_killer.append(label)
            sys.stdout.write("    NAMED TEST DID NOT GO RED: %s\n    (red instead: %s)\n"
                             % ([k for k in killers if k not in red], sorted(set(failed))[:6]))

    caught_eq, moved_eq = [], []
    sys.stdout.write("\nEQUIVALENT - must go MISSED, with a digest identical to the pristine one\n")
    for label, rel, old, new, reason in EQUIVALENT:
        sys.stdout.write("%-18s %s\n" % ("equivalent", label))
        if not apply(rel, old, new):
            unapplied.append(label)
            continue
        digest, n, _ = fingerprint(COPY)
        code, failed = run_tests(COPY, "equivalent")
        same = digest == base_digest
        sys.stdout.write("    exit=%d  %2d red  fingerprint %s over %d values (%s)\n"
                         % (code, len(failed), digest, n, "IDENTICAL" if same else "DIFFERS"))
        if code != 0:
            caught_eq.append((label, sorted(set(failed))[:4]))
        if not same:
            moved_eq.append(label)
            sys.stdout.write("    WITNESS FAILED: %s\n" % reason.split(".")[0])

    return verdict(unapplied, survivors, wrong_killer, caught_eq, moved_eq)


def verdict(unapplied, survivors, wrong_killer, caught_eq, moved_eq) -> int:
    sys.stdout.write("\nPOPULATION %d mutations over %d classes (floor %d), %d equivalent (floor %d)\n"
                     % (len(MUTATIONS), len({m[0] for m in MUTATIONS}), MIN_MUTATIONS, len(EQUIVALENT),
                        MIN_EQUIVALENT))
    bad = False
    for title, items in (("NEVER APPLIED - a verdict over a smaller population than this file declares "
                          "says nothing:", unapplied),
                         ("SURVIVED (nothing objected - this is a check that is not there):", survivors),
                         ("CAUGHT, BUT NOT BY THE TEST THAT NAMES IT:", wrong_killer),
                         ("EQUIVALENT BUT CAUGHT - a test with an opinion about how the code is WRITTEN:",
                          caught_eq),
                         ("EQUIVALENT BUT THE FINGERPRINT MOVED - the ruling is false, like round 3's:",
                          moved_eq)):
        if items:
            bad = True
            sys.stdout.write("%s\n" % title)
            for item in items:
                sys.stdout.write("    %s\n" % (item,))
    if bad:
        return 1
    sys.stdout.write("every one of the %d mutations was killed by the test that names it, and every one of\n"
                     "the %d equivalent mutants went MISSED with a byte-identical fingerprint\n"
                     % (len(MUTATIONS), len(EQUIVALENT)))
    return 0


def main(argv) -> int:
    if "--prove-floor" in argv:
        return prove_floor()
    if "--non-example" in argv:
        return non_example()
    return sweep()


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
