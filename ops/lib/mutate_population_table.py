"""P-PROC-06's data tables, imported by ops/lib/check-mutate-population.py and read nowhere else.

The tables moved here from the gate in T-0208's merge of origin/main: main's DRIVERS (plan.py, straightline.py)
and this branch's (normalise.py) as a union took the gate to 302 lines against CLAUDE.md's 300-line cap, and a
data table moves before a gate is squeezed. Their meaning is unchanged - the gate's docstring says how each
is read, and the gate's --prove-red runs its shipping entry point over them.
"""

# The WHITELIST of population drivers: any other ops/mutate/*.py with a `__main__` block is a refusal until
# it is classified here (ruling R3).
DRIVERS = ("budget.py", "extractadapter.py", "gates.py", "geometry.py", "guidance.py", "handoff.py",
           "hazards.py", "menu.py", "normalise.py", "plan.py", "retrace.py", "routescore.py", "scenic_tags.py",
           "segmentscore.py", "straightline.py", "surfacecoverage.py")
PROBES = {"geometry_probe.py": "a probe over geometry.py's population; it declares no subject of its own"}

# The literal floor: every module a driver declares today. Losing one is a refusal (ruling R4 ii).
COVERED_FLOOR = (
    "services/etl/etl/accessrule.py", "services/etl/etl/extractadapter.py",
    "services/etl/etl/normalise.py", "services/etl/etl/proximity.py",
    "services/etl/etl/region_reference.py", "services/etl/etl/scenecheck.py",
    "services/etl/etl/sinuosity.py",
    "services/etl/etl/snap.py", "services/etl/etl/surfacecoverage.py", "services/etl/etl/tagwriter.py",
    "Sources/Handoff/AppleMapsDirections.swift", "Sources/Handoff/HandoffError.swift",
    "Sources/Handoff/StraightLineDistance.swift",
    "Sources/ScenicKit/Budget/BudgetError.swift", "Sources/ScenicKit/Budget/BudgetOutcome.swift",
    "Sources/ScenicKit/Budget/LambdaSearch.swift", "Sources/ScenicKit/Gates/ConsideredTags.swift",
    "Sources/ScenicKit/Gates/GateDecision.swift", "Sources/ScenicKit/Gates/GateReason.swift",
    "Sources/ScenicKit/Gates/Gates.swift", "Sources/ScenicKit/Guidance/GuidanceMapping.swift",
    "Sources/ScenicKit/Plan/LambdaCustomModel.swift", "Sources/ScenicKit/Plan/PlanTable.swift",
    "Sources/ScenicKit/Plan/PlanWaypoints.swift", "Sources/ScenicKit/Plan/RouteDifference.swift",
    "Sources/ScenicKit/Plan/RoutePath.swift", "Sources/ScenicKit/Plan/ScenicPlan.swift",
    "Sources/ScenicKit/Plan/ScenicPlanner.swift", "Sources/ScenicPlanCLI/PlanArguments.swift",
    "Sources/ScenicKit/Guidance/GuidanceSign.swift", "Sources/ScenicKit/Hazards/HazardFlag.swift",
    "Sources/ScenicKit/Hazards/HazardStrip.swift", "Sources/ScenicKit/Loop/RetraceDetector.swift",
    "Sources/ScenicKit/Scoring/RouteScore.swift", "Sources/ScenicKit/Scoring/SegmentScore.swift",
    "Sources/ScenicKit/Scoring/SegmentTerms.swift",
    "Sources/ScenicKit/Menu/RouteMenu.swift", "Sources/ScenicKit/Menu/MenuRow.swift",
    "Sources/ScenicPlanCLI/MenuArguments.swift",
)
