import copy
from datetime import datetime
import logging
import random
from typing import Dict, List, Optional
import networkx as nx

from app.integrations.traffic.traffic_models import (
    CongestionLevel,
    RoadClosure,
    RoadStatus,
    TrafficObservation,
    TrafficScenario,
)
from app.integrations.traffic.traffic_provider import TrafficProvider

logger = logging.getLogger(__name__)

SCENARIOS: List[TrafficScenario] = [
    TrafficScenario(
        scenario_id="morning_peak",
        name="Morning Rush Hour (08:30 - 10:30)",
        description="Heavy commuter traffic along GT Road, Railway Station Road, and Bus Stand.",
        time_of_day="09:00",
        affected_corridors=["GT Road", "Railway Road", "LPU Corridor", "Station Road"],
        global_congestion_factor=1.65,
        closures_count=0
    ),
    TrafficScenario(
        scenario_id="evening_peak",
        name="Evening Peak & Market Rush (17:30 - 20:30)",
        description="Intense congestion in central bazaars, Model Town, and NH44 interchanges.",
        time_of_day="18:30",
        affected_corridors=["Model Town Road", "Hadiabad Road", "Central Bazaar", "NH44 Bypass"],
        global_congestion_factor=1.80,
        closures_count=0
    ),
    TrafficScenario(
        scenario_id="midday_normal",
        name="Midday Off-Peak (11:00 - 16:00)",
        description="Standard urban flow with moderate delays at major signalized intersections.",
        time_of_day="13:30",
        affected_corridors=["City Center"],
        global_congestion_factor=1.15,
        closures_count=0
    ),
    TrafficScenario(
        scenario_id="night_freeflow",
        name="Night Time Free Flow (22:00 - 05:30)",
        description="Uncongested roadways operating at baseline legal speed limits.",
        time_of_day="01:00",
        affected_corridors=[],
        global_congestion_factor=1.0,
        closures_count=0
    ),
    TrafficScenario(
        scenario_id="emergency_incident",
        name="Emergency Multi-Vehicle Incident on GT Road",
        description="Major incident blocking 2 lanes near Hanumangarh Chowk, triggering severe bottlenecks.",
        time_of_day="17:00",
        affected_corridors=["GT Road", "Hanumangarh Chowk", "Banga Road"],
        global_congestion_factor=2.20,
        closures_count=1
    ),
    TrafficScenario(
        scenario_id="monsoon_flooding",
        name="Monsoon Waterlogging & Railway Underpass Closure",
        description="Severe waterlogging forces complete closure of Phagwara Railway Underpass.",
        time_of_day="14:00",
        affected_corridors=["Railway Road", "Subhash Nagar Underpass"],
        global_congestion_factor=1.95,
        closures_count=2
    ),
]


class MockTrafficProvider(TrafficProvider):
    """
    Synthetic Traffic Provider delivering deterministic, reproducible traffic conditions
    for testing and algorithm development.
    
    IMPORTANT: All outputs are explicitly marked with source='synthetic_simulation'
    and is_live=False.
    """

    def __init__(self, seed: int = 42):
        self.seed = seed
        self._rng = random.Random(seed)
        self.active_scenario_id = "morning_peak"

    def get_available_scenarios(self) -> List[TrafficScenario]:
        return SCENARIOS

    def get_road_closures(self, scenario_id: Optional[str] = None) -> List[RoadClosure]:
        scen = scenario_id or self.active_scenario_id
        closures = []
        if scen == "emergency_incident":
            closures.append(
                RoadClosure(
                    closure_id="closure_acc_01",
                    edge_id="incident_gt_road",
                    u=1001,
                    v=1002,
                    key=0,
                    reason="Multi-vehicle collision near Hanumangarh Chowk (GT Road)",
                    severity="impassable"
                )
            )
        elif scen == "monsoon_flooding":
            closures.extend([
                RoadClosure(
                    closure_id="closure_flood_01",
                    edge_id="railway_underpass_01",
                    u=2001,
                    v=2002,
                    key=0,
                    reason="Railway Underpass submerged by 1.2m flood water",
                    severity="impassable"
                ),
                RoadClosure(
                    closure_id="closure_flood_02",
                    edge_id="railway_underpass_02",
                    u=2002,
                    v=2001,
                    key=0,
                    reason="Railway Underpass submerged by 1.2m flood water (Opposite Direction)",
                    severity="impassable"
                ),
            ])
        return closures

    def generate_observation_for_edge(
        self,
        u: int,
        v: int,
        key: int,
        length: float,
        baseline_speed_kph: float,
        highway_class: str,
        name: str = "",
        scenario_id: Optional[str] = None
    ) -> TrafficObservation:
        scen = scenario_id or self.active_scenario_id
        edge_id = f"{u}_{v}_{key}"

        # Deterministic pseudo-randomness based on edge_id and seed
        edge_rng = random.Random(f"{self.seed}_{scen}_{edge_id}")

        # Baseline congestion factor by scenario
        scen_obj = next((s for s in SCENARIOS if s.scenario_id == scen), SCENARIOS[0])
        factor = scen_obj.global_congestion_factor

        # Major roads and transit corridors suffer higher slowdowns during peaks
        is_corridor = any(corr.lower() in name.lower() for corr in scen_obj.affected_corridors)
        if is_corridor:
            factor += edge_rng.uniform(0.3, 0.7)

        # Highway class vulnerability to congestion
        if highway_class in ("primary", "trunk", "secondary"):
            speed_ratio = max(0.25, min(1.1, (1.0 / factor) * edge_rng.uniform(0.85, 1.05)))
        elif highway_class in ("residential", "living_street", "service"):
            speed_ratio = max(0.40, min(1.0, (1.0 / (factor * 0.85)) * edge_rng.uniform(0.9, 1.1)))
        else:
            speed_ratio = max(0.35, min(1.05, (1.0 / factor) * edge_rng.uniform(0.88, 1.02)))

        current_speed = round(baseline_speed_kph * speed_ratio, 1)
        speed_mps = (current_speed * 1000.0) / 3600.0
        tt_seconds = round(length / max(speed_mps, 1.0), 2)

        # Determine Congestion Level
        if speed_ratio >= 0.85:
            congestion = CongestionLevel.FREE_FLOW
        elif speed_ratio >= 0.65:
            congestion = CongestionLevel.LOW
        elif speed_ratio >= 0.45:
            congestion = CongestionLevel.MODERATE
        elif speed_ratio >= 0.30:
            congestion = CongestionLevel.HEAVY
        else:
            congestion = CongestionLevel.SEVERE

        # Road Status
        road_status = RoadStatus.OPEN
        if congestion == CongestionLevel.SEVERE:
            road_status = RoadStatus.SLOW
        if scen == "emergency_incident" and is_corridor and edge_rng.random() < 0.15:
            road_status = RoadStatus.ACCIDENT

        return TrafficObservation(
            edge_id=edge_id,
            u=u,
            v=v,
            key=key,
            timestamp=datetime.utcnow(),
            baseline_speed_kph=round(baseline_speed_kph, 1),
            current_speed_kph=current_speed,
            speed_ratio=round(speed_ratio, 3),
            congestion_level=congestion,
            road_status=road_status,
            travel_time_seconds=tt_seconds,
            is_live=False,
            source="synthetic_simulation",
            confidence=0.92,
        )

    def get_observation(self, u: int, v: int, key: int = 0) -> Optional[TrafficObservation]:
        # Minimal mock for a single queried edge
        return self.generate_observation_for_edge(
            u=u,
            v=v,
            key=key,
            length=150.0,
            baseline_speed_kph=40.0,
            highway_class="secondary",
            name="Urban Corridor",
            scenario_id=self.active_scenario_id
        )

    def get_all_observations(self, scenario_id: Optional[str] = None) -> List[TrafficObservation]:
        return []

    def apply_traffic_to_graph(self, graph: nx.MultiDiGraph, scenario_id: Optional[str] = None) -> nx.MultiDiGraph:
        """
        Applies synthetic traffic speeds and travel times to the graph edges.
        Adds:
        - dynamic_speed_kph
        - dynamic_travel_time
        - congestion_level
        - road_status
        - traffic_source ('synthetic_simulation')
        """
        scen = scenario_id or self.active_scenario_id
        logger.info(f"Applying synthetic traffic scenario '{scen}' to graph ({len(graph.edges)} edges)...")

        for u, v, k, data in graph.edges(keys=True, data=True):
            length = float(data.get("length", 10.0))
            base_spd = float(data.get("speed_kph", 30.0))
            hwy = str(data.get("highway", "unclassified"))
            name = str(data.get("name", ""))

            obs = self.generate_observation_for_edge(
                u=u, v=v, key=k,
                length=length,
                baseline_speed_kph=base_spd,
                highway_class=hwy,
                name=name,
                scenario_id=scen
            )

            data["dynamic_speed_kph"] = obs.current_speed_kph
            data["dynamic_travel_time"] = obs.travel_time_seconds
            data["congestion_level"] = obs.congestion_level.value
            data["road_status"] = obs.road_status.value
            data["traffic_source"] = obs.source
            data["is_live_traffic"] = False

        return graph

