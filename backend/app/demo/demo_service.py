import logging
from typing import Any, Dict
from pydantic import BaseModel

from app.algorithms.algorithm_metrics import AlgorithmComparisonSummary, AlgorithmResult, RoutingObjective
from app.integrations.delhivery.routing_service import DelhiveryRoutingService
from app.routing.rerouting_service import RerouteResponse, ReroutingService
from app.routing.routing_service import RoutingService
from app.traffic.traffic_service import TrafficService

logger = logging.getLogger(__name__)

# Predefined Demonstration Coordinates (Model Town -> Civil Hospital Phagwara)
DEMO_ORIGIN_NAME = "Model Town Phagwara"
DEMO_ORIGIN_COORDS = (31.2260, 75.7790)

DEMO_DEST_NAME = "Civil Hospital Phagwara"
DEMO_DEST_COORDS = (31.2223, 75.7672)


class DemoStateResponse(BaseModel):
    step: int
    step_title: str
    description: str
    origin_name: str = DEMO_ORIGIN_NAME
    origin_coords: tuple[float, float] = DEMO_ORIGIN_COORDS
    dest_name: str = DEMO_DEST_NAME
    dest_coords: tuple[float, float] = DEMO_DEST_COORDS
    algorithm_comparison: AlgorithmComparisonSummary
    delhivery_reference: Any
    active_route: AlgorithmResult
    reroute_result: Any = None
    closures_active: int = 0
    scenario_id: str = "morning_peak"


class JudgeDemoService:
    """
    Coordinates the 12-step guided SIH judge demonstration for EmergencyRoute AI.
    """

    def __init__(
        self,
        routing_service: RoutingService,
        traffic_service: TrafficService,
        rerouting_service: ReroutingService,
    ):
        self.routing_service = routing_service
        self.traffic_service = traffic_service
        self.rerouting_service = rerouting_service
        self.delhivery_routing = DelhiveryRoutingService()

    def get_initial_demo_state(self) -> Dict[str, Any]:
        """Runs the initial baseline scenario comparing all 4 algorithms and Delhivery."""
        src_node = self.routing_service.find_nearest_node(DEMO_ORIGIN_COORDS[0], DEMO_ORIGIN_COORDS[1])
        dest_node = self.routing_service.find_nearest_node(DEMO_DEST_COORDS[0], DEMO_DEST_COORDS[1])

        # Step 1-4: Comparison across all 4 algorithms
        comparison = self.routing_service.compare_all_algorithms(
            source=src_node,
            target=dest_node,
            objective=RoutingObjective.TRAFFIC_AWARE,
            scenario_id="morning_peak"
        )

        optimal_route = comparison.results["A_Star"]

        # Step 5: Independent Delhivery reference route
        del_route = self.delhivery_routing.get_route(
            DEMO_ORIGIN_COORDS[0], DEMO_ORIGIN_COORDS[1],
            DEMO_DEST_COORDS[0], DEMO_DEST_COORDS[1]
        )

        return {
            "step": 1,
            "step_title": "Baseline Route Planning & Algorithm Benchmarking",
            "description": "Compares BFS, DFS, Greedy Best-First, and A* on the Phagwara road graph alongside the independent commercial Delhivery reference.",
            "origin": {"name": DEMO_ORIGIN_NAME, "lat": DEMO_ORIGIN_COORDS[0], "lng": DEMO_ORIGIN_COORDS[1], "node_id": src_node},
            "destination": {"name": DEMO_DEST_NAME, "lat": DEMO_DEST_COORDS[0], "lng": DEMO_DEST_COORDS[1], "node_id": dest_node},
            "algorithm_comparison": comparison.model_dump(),
            "active_route": optimal_route.model_dump(),
            "delhivery_reference": del_route.model_dump(),
            "traffic_scenario": "morning_peak",
            "closures_count": len(self.traffic_service.closure_manager.get_closed_edges()),
        }

    def simulate_incident_and_reroute(self) -> Dict[str, Any]:
        """
        Executes Steps 6-10:
        Introduces an accident, closes Hanumangarh Chowk road segment, and triggers dynamic rerouting.
        """
        src_node = self.routing_service.find_nearest_node(DEMO_ORIGIN_COORDS[0], DEMO_ORIGIN_COORDS[1])
        dest_node = self.routing_service.find_nearest_node(DEMO_DEST_COORDS[0], DEMO_DEST_COORDS[1])

        # Baseline route before incident
        adapter = self.traffic_service.create_graph_adapter(self.routing_service.graph)
        initial_route = self.routing_service.run_algorithm("astar", src_node, dest_node, RoutingObjective.TRAFFIC_AWARE, adapter=adapter)

        # Select edge on active route near Hanumangarh Chowk to block
        mid_idx = min(len(initial_route.edge_path) // 2, len(initial_route.edge_path) - 1)
        target_edge = initial_route.edge_path[mid_idx]

        # Trigger dynamic rerouting
        closure_info = {
            "closure_id": "demo_closure_01",
            "u": target_edge.u,
            "v": target_edge.v,
            "key": target_edge.key,
            "reason": f"[SIMULATED CLOSURE] Dispatcher road blockage test on {target_edge.name}",
            "severity": "impassable"
        }

        reroute_resp = self.rerouting_service.process_dynamic_reroute(
            route_id="demo_route_001",
            current_route=initial_route,
            new_closures=[closure_info],
            min_improvement_threshold_pct=10.0
        )

        return {
            "step": 2,
            "step_title": "Simulated Road Closure & Real-Time Rerouting",
            "description": f"Simulated road closure on '{target_edge.name}'. Segment {target_edge.u}->{target_edge.v} closed by dispatcher. Dynamic reroute executed with A*.",
            "blocked_segment": {
                "u": target_edge.u,
                "v": target_edge.v,
                "name": target_edge.name,
                "highway": target_edge.highway,
            },
            "reroute_result": reroute_resp.model_dump(),
            "previous_route": initial_route.model_dump(),
            "new_route": reroute_resp.active_route.model_dump(),
            "closures_count": len(self.traffic_service.closure_manager.get_closed_edges()),
        }

    def reset_demonstration(self) -> Dict[str, Any]:
        """Restores network state and clears all demo closures."""
        self.traffic_service.closure_manager.clear_all()
        self.traffic_service.refresh_traffic_snapshot(scenario_id="morning_peak")
        logger.info("Judge demonstration state reset to clean baseline.")
        return {"status": "success", "message": "Demonstration environment reset to clean baseline."}

