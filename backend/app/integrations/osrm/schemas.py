from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class OSRMStep(BaseModel):
    name: str = ""
    distance_meters: float = 0.0
    duration_seconds: float = 0.0
    mode: Optional[str] = "driving"
    maneuver: Optional[Dict[str, Any]] = None
    instruction: str = ""


class OSRMLeg(BaseModel):
    distance_meters: float = 0.0
    duration_seconds: float = 0.0
    summary: str = ""
    steps: List[OSRMStep] = []


class OSRMRoute(BaseModel):
    distance_meters: float
    duration_seconds: float
    distance_km: float
    duration_minutes: float
    geometry: Dict[str, Any]  # GeoJSON LineString
    coordinates: List[List[float]] = []  # Leaflet-ready [[lat, lng], ...]
    legs: List[OSRMLeg] = []
    turn_by_turn: List[str] = []


class OSRMRouteResponse(BaseModel):
    success: bool
    provider: str = "osrm"
    code: str  # "Ok", "NoRoute", "InvalidCoordinates", "Timeout", "HTTPError", etc.
    message: str
    origin: Dict[str, float]
    destination: Dict[str, float]
    distance_km: Optional[float] = None
    duration_minutes: Optional[float] = None
    is_live_traffic: bool = False
    disclaimer: str = (
        "Routing engine estimate based on standard road speeds; "
        "not real-time live traffic."
    )
    route: Optional[OSRMRoute] = None
    alternatives_count: int = 0
    alternatives: List[OSRMRoute] = []

