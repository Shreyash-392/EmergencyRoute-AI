from typing import Any, Dict
from app.algorithms.algorithm_metrics import RoutingObjective
from app.traffic.traffic_profiles import CONGESTION_THRESHOLDS


class TrafficWeightCalculator:
    """
    Computes dynamic edge weights, speeds, travel times, and congestion classifications.
    Formula: travel_time_seconds = length_metres / effective_speed_mps
    """

    MIN_SPEED_KPH = 5.0    # Minimal creep speed in severe jam
    MAX_SPEED_KPH = 120.0  # Urban max speed cap

    @classmethod
    def calculate_edge_weight(
        cls,
        length_meters: float,
        base_speed_kph: float,
        current_speed_kph: float,
        traffic_source: str = "synthetic_simulation"
    ) -> Dict[str, Any]:
        """
        Computes effective travel time and congestion metadata for a single edge.
        """
        # Clamp effective speed to realistic bounds
        effective_speed = max(cls.MIN_SPEED_KPH, min(cls.MAX_SPEED_KPH, current_speed_kph))
        effective_mps = (effective_speed * 1000.0) / 3600.0
        
        dynamic_tt = length_meters / max(0.5, effective_mps)
        
        # Base free-flow travel time
        base_mps = (max(cls.MIN_SPEED_KPH, base_speed_kph) * 1000.0) / 3600.0
        base_tt = length_meters / max(0.5, base_mps)

        # Speed ratio
        speed_ratio = round(effective_speed / max(1.0, base_speed_kph), 3)

        # Determine congestion level
        if speed_ratio >= CONGESTION_THRESHOLDS["free_flow"]:
            congestion = "free_flow"
        elif speed_ratio >= CONGESTION_THRESHOLDS["low"]:
            congestion = "low"
        elif speed_ratio >= CONGESTION_THRESHOLDS["moderate"]:
            congestion = "moderate"
        elif speed_ratio >= CONGESTION_THRESHOLDS["heavy"]:
            congestion = "heavy"
        else:
            congestion = "severe"

        return {
            "length_meters": round(length_meters, 2),
            "base_speed_kph": round(base_speed_kph, 1),
            "effective_speed_kph": round(effective_speed, 1),
            "base_travel_time": round(base_tt, 2),
            "dynamic_travel_time": round(dynamic_tt, 2),
            "speed_ratio": speed_ratio,
            "congestion_level": congestion,
            "traffic_source": traffic_source,
            "is_closed": False,
        }

