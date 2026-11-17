from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import networkx as nx

from app.integrations.traffic.traffic_models import RoadClosure, TrafficObservation, TrafficScenario


class TrafficProvider(ABC):
    """
    Abstract interface for traffic providers in EmergencyRoute AI.
    All providers (synthetic, Delhivery, or future sensors) adhere to this contract.
    """

    @abstractmethod
    def get_observation(self, u: int, v: int, key: int = 0) -> Optional[TrafficObservation]:
        """Returns traffic observation for a specific directed edge."""
        pass

    @abstractmethod
    def get_all_observations(self, scenario_id: Optional[str] = None) -> List[TrafficObservation]:
        """Returns all edge traffic observations for the specified or active scenario."""
        pass

    @abstractmethod
    def get_road_closures(self) -> List[RoadClosure]:
        """Returns currently active impassable road closures."""
        pass

    @abstractmethod
    def get_available_scenarios(self) -> List[TrafficScenario]:
        """Returns available traffic scenarios."""
        pass

    @abstractmethod
    def apply_traffic_to_graph(self, graph: nx.MultiDiGraph, scenario_id: Optional[str] = None) -> nx.MultiDiGraph:
        """
        Updates edge weights ('dynamic_travel_time', 'congestion_level') on the graph in-place or copies.
        """
        pass

