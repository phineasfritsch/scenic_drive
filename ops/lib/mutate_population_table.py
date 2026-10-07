"""P-PROC-06's data tables, imported by ops/lib/check-mutate-population.py and read nowhere else.

The tables moved here from the gate in T-0208's merge of origin/main: main's DRIVERS (plan.py, straightline.py)
and this branch's (normalise.py) as a union took the gate to 302 lines against CLAUDE.md's 300-line cap, and a
data table moves before a gate is squeezed. Their meaning is unchanged - the gate's docstring says how each
is read, and the gate's --prove-red runs its shipping entry point over them.
"""

# The WHITELIST of population drivers: any other ops/mutate/*.py with a `__main__` block is a refusal until
# it is classified here (ruling R3).
DRIVERS = ("budget.py", "corpusfetch.py", "corpusota.py", "extractadapter.py", "fallback.py", "gates.py", "geometry.py", "guidance.py", "handoff.py",
           "hazards.py", "menu.py", "normalise.py", "placeallow.py", "plan.py", "plansheet.py", "retrace.py", "roadtrip.py", "routescore.py",
           "saveddrive.py",
           "scenic_tags.py",
           "segmentgeometry.py", "segmentscore.py", "straightline.py", "surfacecoverage.py", "surprise.py",
           "telemetry.py")
PROBES = {"geometry_probe.py": "a probe over geometry.py's population; it declares no subject of its own"}

# The literal floor: every module a driver declares today. Losing one is a refusal (ruling R4 ii).
COVERED_FLOOR = (
    "Sources/ScenicAPIClient/URLSessionCorpusFetcher.swift", "Sources/ScenicAPIClient/CorpusDownloadDelegate.swift",
    "Sources/PlaceStore/LaunchCorpus.swift",
    "Sources/PlaceStore/CorpusManifest.swift", "Sources/PlaceStore/CorpusUpdater.swift",
    "Sources/PlaceStore/CorpusSlots.swift", "Sources/PlaceStore/SHA256.swift",
    "Sources/PlaceStore/DriveSessionLock.swift", "Sources/PlaceStore/DriveSessionToken.swift",
    "Sources/ScenicKit/Surprise/Surprise.swift", "Sources/ScenicKit/Surprise/SurpriseCandidate.swift",
    "Sources/ScenicKit/Surprise/SurpriseCategory.swift", "Sources/ScenicKit/Surprise/SurpriseReach.swift",
    "Sources/ScenicKit/Surprise/SurpriseHistory.swift", "Sources/ScenicKit/Surprise/SurpriseFeedback.swift",
    "Sources/ScenicKit/Surprise/SurpriseContext.swift", "Sources/ScenicKit/Surprise/SurpriseReason.swift",
    "Sources/ScenicKit/Surprise/SurprisePick.swift",
    "Sources/ScenicKit/PlanSheet/PlanSheet.swift", "Sources/ScenicKit/PlanSheet/PlanFailureCopy.swift",
    "Sources/ScenicAPIClient/ClientPlanner.swift",
    "services/etl/etl/accessrule.py", "services/etl/etl/extractadapter.py", "services/etl/etl/fallback.py",
    "services/etl/etl/normalise.py", "services/etl/etl/placeallow.py", "services/etl/etl/proximity.py",
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
    "Sources/ScenicPlanCLI/MenuArguments.swift", "Sources/ScenicPlanCLI/MenuCommand.swift",
    "Sources/ScenicKit/Menu/RecordedAlternatives.swift",
    "Sources/ScenicKit/RoadTrip/RoadTrip.swift", "Sources/ScenicKit/RoadTrip/RoadTripDay.swift",
    "Sources/ScenicKit/RoadTrip/RoadTripEdge.swift", "Sources/ScenicKit/RoadTrip/RoadTripLimits.swift",
    "Sources/ScenicKit/RoadTrip/RoadTripPlace.swift",
    "Sources/PlaceStore/Segment.swift", "Sources/PlaceStore/SegmentVertex.swift",
    "Sources/PlaceStore/FiveDecimals.swift", "Sources/PlaceStore/SavedMidpoint.swift",
    "Sources/PlaceStore/SavedDrive.swift", "Sources/PlaceStore/SavedDriveResolver.swift",
    "Sources/Telemetry/H3CoordIJK.swift", "Sources/Telemetry/H3FaceProjection.swift",
    "Sources/Telemetry/H3BaseCells.swift", "Sources/Telemetry/H3IndexBuilder.swift",
    "Sources/Telemetry/H3Cell.swift", "Sources/Telemetry/CompletionPercent.swift",
    "Sources/Telemetry/TelemetryDataPoint.swift", "Sources/Telemetry/TelemetryEvent.swift",
)
