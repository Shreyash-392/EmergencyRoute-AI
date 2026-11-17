import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx

from app.algorithms.graph_adapter import MultiGraphAdapter
from app.traffic.road_closure_manager import RoadClosureManager
from app.traffic.traffic_fusion import TrafficFusionEngine
from app.traffic.traffic_simulator import TrafficSimulator
from app.traffic.traffic_validator import TrafficValidator

logger = logging.getLogger(__name__)


class TrafficService:
    """
    Unified high-level traffic intelligence service.
    Coordinates road closures, multi-source traffic fusion, and dynamic graph adaptation.
    """

    def __init__(self, graph: Optional[nx.MultiDiGraph] = None):
        self._graph = graph
        self.closure_manager = RoadClosureManager()
        self.validator = TrafficValidator(max_stale_seconds=1800)
        self.fusion_engine = TrafficFusionEngine(validator=self.validator)
        self.simulator = TrafficSimulator(seed=42)

        self.active_scenario_id: str = "morning_peak"
        # Current fused traffic updates: (u, v, key) -> weight dict
        self._fused_traffic: Dict[Tuple[int, int, int], Dict[str, Any]] = {}

    def set_graph(self, graph: nx.MultiDiGraph):
        self._graph = graph
        self.refresh_traffic_snapshot()

    def refresh_traffic_snapshot(
        self,
        scenario_id: Optional[str] = None,
        primary_observations: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[Tuple[int, int, int], Dict[str, Any]]:
        """
        Refreshes current edge traffic state by generating baseline synthetic observations
        and fusing any available primary telematics/sensor observations.
        """
        if self._graph is None:
            return {}

        scen = scenario_id or self.active_scenario_id
        self.active_scenario_id = scen

        fallback_obs = self.simulator.generate_snapshot_for_graph(self._graph, scenario_id=scen)
        primaries = primary_observations or []

        self._fused_traffic = self.fusion_engine.fuse_observations(
            primary_observations=primaries,
            fallback_observations=fallback_obs
        )

        logger.info(
            f"Traffic snapshot refreshed for scenario '{scen}': "
            f"{len(self._fused_traffic)} edges updated, {len(self.closure_manager.get_closed_edges())} closures active."
        )
        return self._fused_traffic

    def get_traffic_snapshot(self) -> Dict[Tuple[int, int, int], Dict[str, Any]]:
        if not self._fused_traffic and self._graph is not None:
            self.refresh_traffic_snapshot()
        return self._fused_traffic

    def create_graph_adapter(self, graph: Optional[nx.MultiDiGraph] = None) -> MultiGraphAdapter:
        """
        Builds a MultiGraphAdapter initialized with current closures and fused traffic weights.
        """
        target_graph = graph or self._graph
        if target_graph is None:
            raise ValueError("No road graph available for MultiGraphAdapter.")

        if not self._fused_traffic:
            self.refresh_traffic_snapshot()

        return MultiGraphAdapter(
            graph=target_graph,
            closed_edges=self.closure_manager.get_closed_edges(),
            traffic_updates=self._fused_traffic
        )

