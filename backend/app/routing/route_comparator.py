from typing import Any, Dict, List, Set, Tuple
from pydantic import BaseModel, Field

from app.algorithms.algorithm_metrics import AlgorithmResult


class RouteComparisonResult(BaseModel):
    decision: str = Field(..., description="'MANDATORY_REROUTE', 'RECOMMENDED_REROUTE', or 'MAINTAIN_CURRENT'")
    old_travel_time_seconds: float
    new_travel_time_seconds: float
    time_saved_seconds: float
    percentage_time_saved: float
    old_distance_meters: float
    new_distance_meters: float
    distance_delta_meters: float
    path_similarity_jaccard: float
    identical_path: bool
    explanation: str


class RouteComparator:
    """
    Compares existing route against newly calculated alternative route.
    Applies decision thresholding to prevent unnecessary rerouting jitter.
    """

    @classmethod
    def compare_routes(
        cls,
        old_route: AlgorithmResult,
        new_route: AlgorithmResult,
        old_is_blocked: bool = False,
        min_improvement_threshold_pct: float = 12.0
    ) -> RouteComparisonResult:
        if old_is_blocked:
            return RouteComparisonResult(
                decision="MANDATORY_REROUTE",
                old_travel_time_seconds=float("inf"),
                new_travel_time_seconds=new_route.estimated_travel_time_seconds,
                time_saved_seconds=float("inf"),
                percentage_time_saved=100.0,
                old_distance_meters=old_route.path_distance_meters,
                new_distance_meters=new_route.path_distance_meters,
                distance_delta_meters=round(new_route.path_distance_meters - old_route.path_distance_meters, 2),
                path_similarity_jaccard=0.0,
                identical_path=False,
                explanation="Original route is physically blocked by road closure. Immediate reroute mandatory."
            )

        old_tt = old_route.estimated_travel_time_seconds
        new_tt = new_route.estimated_travel_time_seconds
        saved_tt = round(old_tt - new_tt, 2)
        pct_saved = round((saved_tt / max(1.0, old_tt)) * 100.0, 2)

        # Compute Jaccard edge overlap
        old_edges: Set[Tuple[int, int, int]] = {(s.u, s.v, s.key) for s in old_route.edge_path}
        new_edges: Set[Tuple[int, int, int]] = {(s.u, s.v, s.key) for s in new_route.edge_path}

        union_size = len(old_edges | new_edges)
        intersection_size = len(old_edges & new_edges)
        jaccard = round(intersection_size / max(1, union_size), 3)
        identical = (old_route.node_path == new_route.node_path)

        if identical:
            decision = "MAINTAIN_CURRENT"
            explanation = "Alternative route is identical to current route. No change needed."
        elif pct_saved >= min_improvement_threshold_pct:
            decision = "RECOMMENDED_REROUTE"
            explanation = f"Alternative route saves {saved_tt:.0f}s ({pct_saved:.1f}% improvement), exceeding the {min_improvement_threshold_pct}% threshold."
        elif pct_saved > 0:
            decision = "MAINTAIN_CURRENT"
            explanation = f"Alternative route saves only {saved_tt:.0f}s ({pct_saved:.1f}%), below the {min_improvement_threshold_pct}% reroute threshold. Maintaining current trajectory to avoid driver disorientation."
        else:
            decision = "MAINTAIN_CURRENT"
            explanation = "Current route remains faster than or equal to alternative options."

        return RouteComparisonResult(
            decision=decision,
            old_travel_time_seconds=old_tt,
            new_travel_time_seconds=new_tt,
            time_saved_seconds=saved_tt,
            percentage_time_saved=pct_saved,
            old_distance_meters=old_route.path_distance_meters,
            new_distance_meters=new_route.path_distance_meters,
            distance_delta_meters=round(new_route.path_distance_meters - old_route.path_distance_meters, 2),
            path_similarity_jaccard=jaccard,
            identical_path=identical,
            explanation=explanation
        )

