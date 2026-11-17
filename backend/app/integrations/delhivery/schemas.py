from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class Coordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90, description="Latitude in decimal degrees")
    longitude: float = Field(..., ge=-180, le=180, description="Longitude in decimal degrees")


class GeocodeResult(BaseModel):
    place_id: Optional[str] = None
    formatted_address: str
    display_name: str
    latitude: float
    longitude: float
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    provider: str = Field(default="delhivery", description="'delhivery' or 'local_fallback'")
    category: Optional[str] = None
    raw_response: Optional[Dict[str, Any]] = None


class GeocodeSearchResponse(BaseModel):
    query: str
    count: int
    results: List[GeocodeResult]
    provider: str
    is_fallback: bool = False


class DelhiveryRouteSegment(BaseModel):
    instruction: Optional[str] = None
    distance_meters: float
    duration_seconds: float
    road_name: Optional[str] = None


class DelhiveryRouteResponse(BaseModel):
    success: bool
    distance_meters: float
    duration_seconds: float
    distance_km: float
    duration_minutes: float
    traffic_delay_seconds: Optional[float] = 0.0
    polyline_geometry: Optional[str] = None
    coordinates: Optional[List[List[float]]] = None
    segments: Optional[List[DelhiveryRouteSegment]] = None
    provider: str = "delhivery"
    is_fallback: bool = False
    message: Optional[str] = None


class MapTileConfig(BaseModel):
    provider: str
    tile_url_template: str
    attribution: str
    max_zoom: int = 19
    min_zoom: int = 1
    subdomains: List[str] = ["a", "b", "c"]
    is_commercial: bool = False

