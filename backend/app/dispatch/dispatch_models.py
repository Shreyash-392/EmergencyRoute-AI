from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field

from app.algorithms.algorithm_metrics import AlgorithmResult


class Vehicle(BaseModel):
    vehicle_id: str
    call_sign: str
    vehicle_type: str
    status: str
    current_lat: float
    current_lng: float
    base_station: str
    assigned_incident_id: Optional[str] = None
    last_updated: Optional[datetime] = None


class EmergencyIncident(BaseModel):
    incident_id: str
    title: str
    description: Optional[str] = None
    incident_type: str
    priority: str
    lat: float
    lng: float
    status: str
    reported_at: Optional[datetime] = None
    assigned_vehicle_id: Optional[str] = None
    resolved_at: Optional[datetime] = None


class CreateIncidentRequest(BaseModel):
    title: str
    description: Optional[str] = None
    incident_type: str
    priority: str = "high"
    lat: float
    lng: float


class VehicleRankingCandidate(BaseModel):
    vehicle: Vehicle
    estimated_travel_time_seconds: float
    estimated_travel_time_minutes: float
    distance_km: float
    suitability_score: float
    rank: int
    route_preview: Optional[AlgorithmResult] = None


class VehicleRankingResponse(BaseModel):
    incident: EmergencyIncident
    candidates_count: int
    ranked_candidates: List[VehicleRankingCandidate]


class DispatchExecutionRequest(BaseModel):
    incident_id: str
    vehicle_id: str
    routing_objective: str = "traffic_aware"


class DispatchExecutionResponse(BaseModel):
    success: bool
    assignment_id: str
    incident_id: str
    vehicle_id: str
    assigned_at: str
    estimated_eta_minutes: float
    distance_km: float
    dispatch_route: AlgorithmResult
    message: str

