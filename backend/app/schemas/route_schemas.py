from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from app.algorithms.algorithm_metrics import AlgorithmResult, RoutingObjective


class RouteRequest(BaseModel):
    origin_lat: Optional[float] = Field(None, ge=-90, le=90)
    origin_lng: Optional[float] = Field(None, ge=-180, le=180)
    dest_lat: Optional[float] = Field(None, ge=-90, le=90)
    dest_lng: Optional[float] = Field(None, ge=-180, le=180)
    source_node: Optional[int] = None
    target_node: Optional[int] = None
    algorithm: Optional[str] = "astar"
    objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE
    scenario_id: Optional[str] = "morning_peak"


class CompareRoutesRequest(BaseModel):
    origin_lat: Optional[float] = Field(None, ge=-90, le=90)
    origin_lng: Optional[float] = Field(None, ge=-180, le=180)
    dest_lat: Optional[float] = Field(None, ge=-90, le=90)
    dest_lng: Optional[float] = Field(None, ge=-180, le=180)
    source_node: Optional[int] = None
    target_node: Optional[int] = None
    objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE
    scenario_id: Optional[str] = "morning_peak"


class RerouteRequest(BaseModel):
    route_id: str
    current_route: AlgorithmResult
    new_closures: Optional[List[Dict[str, Any]]] = None
    new_traffic_observations: Optional[List[Dict[str, Any]]] = None
    min_improvement_threshold_pct: float = 12.0
    force_recalculate: bool = False


class TrafficSimulateRequest(BaseModel):
    scenario_id: str
    extra_congestion_factors: Optional[Dict[str, float]] = None


class RoadClosureRequest(BaseModel):
    action: str = Field(..., description="'add', 'remove', or 'clear'")
    closure_id: Optional[str] = None
    u: Optional[int] = None
    v: Optional[int] = None
    key: int = 0
    reason: str = "Road obstruction"
    severity: str = "impassable"


class ReferenceRouteRequest(BaseModel):
    origin_lat: float = Field(..., ge=-90, le=90)
    origin_lng: float = Field(..., ge=-180, le=180)
    dest_lat: float = Field(..., ge=-90, le=90)
    dest_lng: float = Field(..., ge=-180, le=180)

