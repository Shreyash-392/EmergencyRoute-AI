import logging
from typing import Any, Dict, List, Optional
import networkx as nx

from app.integrations.traffic.mock_traffic import MockTrafficProvider, SCENARIOS
from app.integrations.traffic.traffic_models import TrafficScenario

logger = logging.getLogger(__name__)


class TrafficSimulator:
    """
    Simulation coordinator generating deterministic traffic conditions across
    the Phagwara road network for testing and algorithm benchmarking.
    """

    def __init__(self, seed: int = 42):
        self.mock_provider = MockTrafficProvider(seed=seed)

    def get_available_scenarios(self) -> List[TrafficScenario]:
        return self.mock_provider.get_available_scenarios()

    def generate_snapshot_for_graph(
        self,
        graph: nx.MultiDiGraph,
        scenario_id: str = "morning_peak",
        extra_congestion_factors: Optional[Dict[str, float]] = None
    ) -> List[Dict[str, Any]]:
        """
        Generates a complete list of observation dicts for all edges in the graph
        under the requested scenario.
        """
        observations = []
        extra_factors = extra_congestion_factors or {}

        for u, v, k, data in graph.edges(keys=True, data=True):
            length = float(data.get("length", 10.0))
            base_spd = float(data.get("speed_kph", 30.0))
            hwy = str(data.get("highway", "unclassified"))
            name = str(data.get("name", ""))

            obs = self.mock_provider.generate_observation_for_edge(
                u=u, v=v, key=k,
                length=length,
                baseline_speed_kph=base_spd,
                highway_class=hwy,
                name=name,
                scenario_id=scenario_id
            )

            # Apply any extra corridor congestion factor if provided
            current_spd = obs.current_speed_kph
            for corridor, factor in extra_factors.items():
                if corridor.lower() in name.lower():
                    current_spd = max(5.0, round(current_spd / factor, 1))

            observations.append({
                "u": u,
                "v": v,
                "key": k,
                "length_meters": length,
                "baseline_speed_kph": base_spd,
                "current_speed_kph": current_spd,
                "highway": hwy,
                "name": name,
                "source": "synthetic_simulation",
                "timestamp": obs.timestamp.isoformat(),
                "confidence": 0.92,
            })

        return observations

