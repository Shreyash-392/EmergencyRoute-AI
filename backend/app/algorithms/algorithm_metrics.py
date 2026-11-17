from enum import Enum
import time
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class RoutingObjective(str, Enum):
    MIN_DISTANCE = "distance"
    MIN_TRAVEL_TIME = "travel_time"
    TRAFFIC_AWARE = "traffic_aware"


class PathSegment(BaseModel):
    u: int = Field(..., description="Start node ID")
    v: int = Field(..., description="End node ID")
    key: int = Field(default=0, description="MultiDiGraph parallel edge key")
    length_meters: float
    travel_time_seconds: float
    speed_kph: float
    name: str = "Unnamed Road"
    highway: str = "unclassified"
    cost: float
    geometry_coords: Optional[List[List[float]]] = None


class AlgorithmResult(BaseModel):
    algorithm_name: str
    source_node: int
    target_node: int
    success: bool
    node_path: List[int] = Field(default_factory=list)
    edge_path: List[PathSegment] = Field(default_factory=list)
    path_distance_meters: float = 0.0
    path_distance_km: float = 0.0
    estimated_travel_time_seconds: float = 0.0
    estimated_travel_time_minutes: float = 0.0
    weighted_path_cost: float = 0.0
    nodes_explored: int = 0
    execution_time_ms: float = 0.0
    routing_objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE
    is_optimal: bool = False
    coordinates: List[List[float]] = Field(default_factory=list, description="[[lat, lon], ...] for map display")
    error_message: Optional[str] = None


class AlgorithmComparisonSummary(BaseModel):
    source_node: int
    target_node: int
    routing_objective: RoutingObjective
    traffic_scenario: str
    results: Dict[str, AlgorithmResult]
    fastest_execution_algorithm: str
    least_nodes_explored_algorithm: str
    lowest_cost_algorithm: str
    shortest_distance_algorithm: str
    lowest_travel_time_algorithm: str

