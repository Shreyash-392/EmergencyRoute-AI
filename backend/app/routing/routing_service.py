import logging
from typing import Any, Dict, List, Optional
import networkx as nx
import osmnx as ox

from app.algorithms.algorithm_metrics import (
    AlgorithmComparisonSummary,
    AlgorithmResult,
    RoutingObjective,
)
from app.algorithms.astar import a_star_search
from app.algorithms.bfs import breadth_first_search
from app.algorithms.dfs import depth_first_search
from app.algorithms.graph_adapter import MultiGraphAdapter
from app.algorithms.greedy_best_first import greedy_best_first_search
from app.core.graph_loader import load_graph_from_graphml
from app.traffic.traffic_service import TrafficService

logger = logging.getLogger(__name__)


class RoutingService:
    """
    Central routing service orchestrating all four search algorithms and multi-algorithm benchmarking.
    """

    def __init__(
        self,
        graph: Optional[nx.MultiDiGraph] = None,
        traffic_service: Optional[TrafficService] = None
    ):
        self._graph = graph
        self._traffic_service = traffic_service

    @property
    def graph(self) -> nx.MultiDiGraph:
        if self._graph is None:
            self._graph = load_graph_from_graphml()
        return self._graph

    @property
    def traffic_service(self) -> TrafficService:
        if self._traffic_service is None:
            self._traffic_service = TrafficService(graph=self.graph)
        return self._traffic_service

    def find_nearest_node(self, lat: float, lon: float) -> int:
        """Finds nearest road network intersection node in the connected drivable network."""
        if not hasattr(self, "_routable_subgraph") or self._routable_subgraph is None:
            try:
                largest_wcc = max(nx.weakly_connected_components(self.graph), key=len)
                self._routable_subgraph = self.graph.subgraph(largest_wcc)
            except Exception:
                self._routable_subgraph = self.graph
        return int(ox.distance.nearest_nodes(self._routable_subgraph, X=lon, Y=lat))

    def get_adapter(
        self,
        scenario_id: Optional[str] = None
    ) -> MultiGraphAdapter:
        if scenario_id:
            self.traffic_service.refresh_traffic_snapshot(scenario_id=scenario_id)
        return self.traffic_service.create_graph_adapter(graph=self.graph)

    def run_algorithm(
        self,
        algorithm_name: str,
        source: int,
        target: int,
        objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE,
        scenario_id: Optional[str] = None,
        adapter: Optional[MultiGraphAdapter] = None
    ) -> AlgorithmResult:
        """Executes a specific search algorithm on the road graph."""
        graph_adapter = adapter or self.get_adapter(scenario_id=scenario_id)
        algo_lower = algorithm_name.strip().lower()

        if algo_lower in ("bfs", "breadth_first_search"):
            return breadth_first_search(graph_adapter, source, target, objective)
        elif algo_lower in ("dfs", "depth_first_search"):
            return depth_first_search(graph_adapter, source, target, objective)
        elif algo_lower in ("greedy", "greedy_best_first", "gbfs"):
            return greedy_best_first_search(graph_adapter, source, target, objective)
        elif algo_lower in ("astar", "a*", "a_star", "optimal"):
            return a_star_search(graph_adapter, source, target, objective)
        else:
            raise ValueError(
                f"Unknown algorithm '{algorithm_name}'. Must be one of: 'bfs', 'dfs', 'greedy', 'astar'"
            )

    def compare_all_algorithms(
        self,
        source: int,
        target: int,
        objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE,
        scenario_id: Optional[str] = None
    ) -> AlgorithmComparisonSummary:
        """
        Runs all four algorithms against identical source, destination, graph state,
        traffic snapshot, closures, and objective to generate benchmark comparisons.
        """
        adapter = self.get_adapter(scenario_id=scenario_id)
        active_scen = scenario_id or self.traffic_service.active_scenario_id

        results: Dict[str, AlgorithmResult] = {
            "BFS": breadth_first_search(adapter, source, target, objective),
            "DFS": depth_first_search(adapter, source, target, objective),
            "Greedy_Best_First": greedy_best_first_search(adapter, source, target, objective),
            "A_Star": a_star_search(adapter, source, target, objective),
        }

        successful = {k: v for k, v in results.items() if v.success}

        if not successful:
            fastest_exec = least_nodes = lowest_cost = shortest_dist = lowest_tt = "None"
        else:
            fastest_exec = min(successful.keys(), key=lambda k: successful[k].execution_time_ms)
            least_nodes = min(successful.keys(), key=lambda k: successful[k].nodes_explored)
            lowest_cost = min(successful.keys(), key=lambda k: successful[k].weighted_path_cost)
            shortest_dist = min(successful.keys(), key=lambda k: successful[k].path_distance_meters)
            lowest_tt = min(successful.keys(), key=lambda k: successful[k].estimated_travel_time_seconds)

        return AlgorithmComparisonSummary(
            source_node=source,
            target_node=target,
            routing_objective=objective,
            traffic_scenario=active_scen,
            results=results,
            fastest_execution_algorithm=fastest_exec,
            least_nodes_explored_algorithm=least_nodes,
            lowest_cost_algorithm=lowest_cost,
            shortest_distance_algorithm=shortest_dist,
            lowest_travel_time_algorithm=lowest_tt,
        )

