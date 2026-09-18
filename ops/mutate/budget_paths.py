"""The files ops/mutate/budget.py mutates, and nothing else.

Split out of budget_mutations.py in the fifth fix pass, when the population outgrew the 300-line cap a second
time and the new entries had to live in their own module. That module needs the same three paths, and
importing them back out of budget_mutations.py - which imports the module - is a cycle. Six lines of shared
data in a leaf module is the alternative to either a cycle or a second copy of the paths that can drift.

Every other module in this harness takes its paths from here: budget.py, budget_tree.py, budget_arms.py,
budget_mutations.py and budget_boundaries.py. The list is deliberately not computed by globbing
Sources/ScenicKit/Budget/ - a new file appearing there should make somebody decide whether it is a subject,
not be silently snapshotted and restored by a harness that never had a mutation for it.
"""
from __future__ import annotations

import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[2]
SRC = ROOT / "Sources" / "ScenicKit" / "Budget" / "LambdaSearch.swift"
ERR = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetError.swift"
OUT = ROOT / "Sources" / "ScenicKit" / "Budget" / "BudgetOutcome.swift"

# Every source a mutation may touch. The driver snapshots and restores exactly these, and refuses to run if
# any of them differs from `git show HEAD:`.
SUBJECTS = (SRC, ERR, OUT)
