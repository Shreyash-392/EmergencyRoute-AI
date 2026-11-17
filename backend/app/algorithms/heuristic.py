import math
from typing import Dict, Tuple
from app.algorithms.algorithm_metrics import RoutingObjective

EARTH_RADIUS_METERS = 6371000.0  # WGS-84 mean radius


def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Computes great-circle distance between two geographic coordinates in meters
    using the Haversine formula.
    """
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * (math.sin(delta_lambda / 2.0) ** 2)
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1.0 - a)))
    return EARTH_RADIUS_METERS * c


class HeuristicCalculator:
    """
    Provides admissible and consistent geographic heuristics for road graph search.
    Guarantees h(n) <= h*(n) without arbitrary overestimating multipliers.
    """

    def __init__(
        self,
        node_coords: Dict[int, Tuple[float, float]],
        max_speed_kph: float = 100.0
    ):
        """
        :param node_coords: Mapping of node_id -> (lat, lon)
        :param max_speed_kph: Maximum legal/physical network speed in km/h used for
                              admissible lower-bound travel time estimation.
        """
        self.node_coords = node_coords
        self.max_speed_kph = max_speed_kph
        # Convert max speed to meters per second: (100 * 1000) / 3600 = 27.7778 m/s
        self.max_speed_mps = (max_speed_kph * 1000.0) / 3600.0

    def estimate(
        self,
        current_node: int,
        target_node: int,
        objective: RoutingObjective
    ) -> float:
        """
        Computes admissible heuristic h(n) based on routing objective:
        - MIN_DISTANCE: Great-circle distance (meters).
        - MIN_TRAVEL_TIME / TRAFFIC_AWARE: Admissible lower-bound travel time (seconds)
          equal to great_circle_distance / max_network_speed.
        """
        if current_node == target_node:
            return 0.0

        coord_curr = self.node_coords.get(current_node)
        coord_target = self.node_coords.get(target_node)

        if not coord_curr or not coord_target:
            return 0.0

        dist_meters = haversine_distance(
            coord_curr[0], coord_curr[1],
            coord_target[0], coord_target[1]
        )

        if objective == RoutingObjective.MIN_DISTANCE:
            # Admissible distance heuristic (meters)
            return dist_meters
        else:
            # Admissible travel time heuristic (seconds): dist / max_speed_mps
            # Because actual path distance >= dist_meters and road speed <= max_speed_mps,
            # actual time = sum(d_i / v_i) >= (sum d_i) / v_max >= dist_meters / v_max.
            return dist_meters / self.max_speed_mps

