from typing import Any, Dict, List, Optional, Set, Tuple
from pydantic import BaseModel, Field

from app.algorithms.algorithm_metrics import AlgorithmResult
from app.algorithms.graph_adapter import MultiGraphAdapter


class RouteValidationStatus(BaseModel):
    is_valid: bool
    is_blocked: bool = False
    blocked_edge: Optional[Tuple[int, int, int]] = None
    original_travel_time_seconds: float
    current_travel_time_seconds: float
    travel_time_increase_seconds: float
    travel_time_increase_percentage: float
    reason: str


class RouteValidator:
    """
    Validates active routes against real-time graph updates (closures and severe slowdowns).
    """

    @classmethod
    def validate_active_route(
        cls,
        route_result: AlgorithmResult,
        adapter: MultiGraphAdapter
    ) -> RouteValidationStatus:
        if not route_result.success or not route_result.edge_path:
            return RouteValidationStatus(
                is_valid=False,
                is_blocked=True,
                original_travel_time_seconds=0.0,
                current_travel_time_seconds=0.0,
                travel_time_increase_seconds=0.0,
                travel_time_increase_percentage=0.0,
                reason="Original route was empty or unsuccessful."
            )

        orig_tt = route_result.estimated_travel_time_seconds
        updated_tt = 0.0

        for segment in route_result.edge_path:
            u, v, k = segment.u, segment.v, segment.key

            # 1. Check if road is now closed
            if adapter.is_edge_closed(u, v, k):
                return RouteValidationStatus(
                    is_valid=False,
                    is_blocked=True,
                    blocked_edge=(u, v, k),
                    original_travel_time_seconds=orig_tt,
                    current_travel_time_seconds=float("inf"),
                    travel_time_increase_seconds=float("inf"),
                    travel_time_increase_percentage=float("inf"),
                    reason=f"Road segment {u} -> {v} ({segment.name}) is now completely closed."
                )

            # 2. Check updated edge cost
            edge_data = dict(adapter.graph[u][v][k])
            seg_cost = adapter.get_edge_cost(u, v, k, edge_data, route_result.routing_objective)
            updated_tt += seg_cost

        diff_seconds = round(updated_tt - orig_tt, 2)
        pct_increase = round((diff_seconds / max(1.0, orig_tt)) * 100.0, 2)

        is_valid = True
        reason = "Route remains clear and operational."
        if diff_seconds > 60 and pct_increase > 25.0:
            reason = f"Route is clear but delayed by {diff_seconds:.0f}s (+{pct_increase:.1f}%)."

        return RouteValidationStatus(
            is_valid=is_valid,
            is_blocked=False,
            original_travel_time_seconds=orig_tt,
            current_travel_time_seconds=round(updated_tt, 2),
            travel_time_increase_seconds=diff_seconds,
            travel_time_increase_percentage=pct_increase,
            reason=reason
        )

