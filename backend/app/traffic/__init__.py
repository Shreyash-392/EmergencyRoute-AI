from app.traffic.traffic_service import TrafficService
from app.traffic.road_closure_manager import RoadClosureManager, ActiveRoadClosure
from app.traffic.traffic_weight_calculator import TrafficWeightCalculator
from app.traffic.traffic_fusion import TrafficFusionEngine
from app.traffic.traffic_validator import TrafficValidator
from app.traffic.traffic_simulator import TrafficSimulator
from app.traffic.traffic_profiles import BASE_HIGHWAY_SPEEDS, CONGESTION_THRESHOLDS

__all__ = [
    "TrafficService",
    "RoadClosureManager",
    "ActiveRoadClosure",
    "TrafficWeightCalculator",
    "TrafficFusionEngine",
    "TrafficValidator",
    "TrafficSimulator",
    "BASE_HIGHWAY_SPEEDS",
    "CONGESTION_THRESHOLDS",
]

