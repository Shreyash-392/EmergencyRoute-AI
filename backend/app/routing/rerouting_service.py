from datetime import datetime, timezone
import logging
import uuid
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field

from app.algorithms.algorithm_metrics import AlgorithmResult, RoutingObjective
from app.routing.route_comparator import RouteComparator, RouteComparisonResult
from app.routing.route_history import RouteHistoryManager, RerouteEvent
from app.routing.route_validator import RouteValidator, RouteValidationStatus
from app.routing.routing_service import RoutingService

logger = logging.getLogger(__name__)


class RerouteResponse(BaseModel):
    reroute_triggered: bool
    decision: str
    reason: str
    active_route: AlgorithmResult
    previous_route: Optional[AlgorithmResult] = None
    comparison: Optional[RouteComparisonResult] = None
    validation: RouteValidationStatus
    event_id: Optional[str] = None


class ReroutingService:
    """
    Orchestrates the 9-step dynamic rerouting engine.
    Ensures vehicles avoid newly formed bottlenecks and road closures without
    unnecessary jitter.
    """

    def __init__(
        self,
        routing_service: RoutingService,
        history_manager: Optional[RouteHistoryManager] = None
    ):
        self.routing_service = routing_service
        self.history_manager = history_manager or RouteHistoryManager()

    def process_dynamic_reroute(
        self,
        route_id: str,
        current_route: AlgorithmResult,
        new_closures: Optional[List[Dict[str, Any]]] = None,
        new_traffic_observations: Optional[List[Dict[str, Any]]] = None,
        min_improvement_threshold_pct: float = 12.0,
        force_recalculate: bool = False
    ) -> RerouteResponse:
        """
        Executes dynamic reroute assessment:
        1. Ingests and validates closure or traffic updates.
        2. Applies updates to TrafficService.
        3. Validates current route integrity against updated network.
        4. Calculates optimal alternative route with A*.
        5. Compares old vs new route.
        6. Commits decision to RouteHistory and returns response.
        """
        traffic_svc = self.routing_service.traffic_service

        # Step 1 & 2: Ingest new closures if provided
        if new_closures:
            for c in new_closures:
                traffic_svc.closure_manager.add_closure(
                    closure_id=c.get("closure_id", str(uuid.uuid4())[:8]),
                    u=int(c["u"]),
                    v=int(c["v"]),
                    key=int(c.get("key", 0)),
                    reason=c.get("reason", "Dynamic closure"),
                    severity=c.get("severity", "impassable")
                )

        # Ingest new traffic observations
        if new_traffic_observations:
            traffic_svc.refresh_traffic_snapshot(primary_observations=new_traffic_observations)

        # Step 3: Get updated MultiGraphAdapter
        adapter = traffic_svc.create_graph_adapter(graph=self.routing_service.graph)

        # Step 4: Validate current route
        validation = RouteValidator.validate_active_route(current_route, adapter)

        # Step 5: Check if recalculation needed
        needs_reroute = validation.is_blocked or force_recalculate or validation.travel_time_increase_percentage > 20.0

        # Calculate alternative optimal route with A*
        new_route = self.routing_service.run_algorithm(
            algorithm_name="astar",
            source=current_route.source_node,
            target=current_route.target_node,
            objective=current_route.routing_objective,
            adapter=adapter
        )

        # Step 6: Compare old and new route
        comparison = RouteComparator.compare_routes(
            old_route=current_route,
            new_route=new_route,
            old_is_blocked=validation.is_blocked,
            min_improvement_threshold_pct=min_improvement_threshold_pct
        )

        should_switch = (
            force_recalculate
            or comparison.decision in ("MANDATORY_REROUTE", "RECOMMENDED_REROUTE")
        )

        event_id = None
        if should_switch and new_route.success:
            event_id = f"reroute_{uuid.uuid4().hex[:8]}"
            self.history_manager.record_reroute(
                route_id=route_id,
                new_route=new_route,
                reason=validation.reason if validation.is_blocked else comparison.explanation,
                decision=comparison.decision,
                event_id=event_id
            )
            final_route = new_route
            prev_route = current_route
            logger.info(f"Rerouting executed for route {route_id}: {comparison.decision} - {comparison.explanation}")
        else:
            final_route = current_route
            prev_route = None

        return RerouteResponse(
            reroute_triggered=should_switch,
            decision=comparison.decision if not force_recalculate else "MANUAL_OVERRIDE",
            reason=comparison.explanation if not force_recalculate else "Manual reroute requested by dispatch.",
            active_route=final_route,
            previous_route=prev_route,
            comparison=comparison,
            validation=validation,
            event_id=event_id
        )

