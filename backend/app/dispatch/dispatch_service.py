from datetime import datetime, timezone
import logging
import uuid
from typing import List, Optional
from sqlalchemy.orm import Session

from app.algorithms.algorithm_metrics import RoutingObjective
from app.core.websocket_manager import websocket_manager
from app.db.database import DispatchAssignmentModel, IncidentModel, SessionLocal, VehicleModel
from app.dispatch.dispatch_models import (
    CreateIncidentRequest,
    DispatchExecutionRequest,
    DispatchExecutionResponse,
    EmergencyIncident,
    Vehicle,
    VehicleRankingCandidate,
    VehicleRankingResponse,
)
from app.routing.routing_service import RoutingService

logger = logging.getLogger(__name__)

SUITABILITY_MAP = {
    "cardiac_arrest": ["ambulance"],
    "general_medical": ["ambulance"],
    "road_hazard": ["ambulance", "fire_engine", "police"],
    "road_accident": ["ambulance", "fire_engine", "police"],
    "fire_emergency": ["fire_engine"],
    "crime_in_progress": ["police"],
}


class DispatchService:
    """
    Emergency vehicle fleet management and intelligent dispatch service.
    Ranks vehicles based on true A* network travel time and operational suitability.
    """

    def __init__(self, routing_service: RoutingService):
        self.routing_service = routing_service

    def get_all_vehicles(self) -> List[Vehicle]:
        db: Session = SessionLocal()
        try:
            records = db.query(VehicleModel).all()
            return [
                Vehicle(
                    vehicle_id=r.vehicle_id,
                    call_sign=r.call_sign,
                    vehicle_type=r.vehicle_type,
                    status=r.status,
                    current_lat=r.current_lat,
                    current_lng=r.current_lng,
                    base_station=r.base_station,
                    assigned_incident_id=r.assigned_incident_id,
                    last_updated=r.last_updated,
                )
                for r in records
            ]
        finally:
            db.close()

    def get_all_incidents(self) -> List[EmergencyIncident]:
        db: Session = SessionLocal()
        try:
            records = db.query(IncidentModel).order_by(IncidentModel.reported_at.desc()).all()
            return [
                EmergencyIncident(
                    incident_id=r.incident_id,
                    title=r.title,
                    description=r.description,
                    incident_type=r.incident_type,
                    priority=r.priority,
                    lat=r.lat,
                    lng=r.lng,
                    status=r.status,
                    reported_at=r.reported_at,
                    assigned_vehicle_id=r.assigned_vehicle_id,
                    resolved_at=r.resolved_at,
                )
                for r in records
            ]
        finally:
            db.close()

    def create_incident(self, req: CreateIncidentRequest) -> EmergencyIncident:
        db: Session = SessionLocal()
        try:
            inc_id = f"inc_{uuid.uuid4().hex[:6]}"
            model = IncidentModel(
                incident_id=inc_id,
                title=req.title,
                description=req.description,
                incident_type=req.incident_type,
                priority=req.priority,
                lat=req.lat,
                lng=req.lng,
                status="reported",
                reported_at=datetime.now(timezone.utc),
            )
            db.add(model)
            db.commit()

            incident = EmergencyIncident(
                incident_id=model.incident_id,
                title=model.title,
                description=model.description,
                incident_type=model.incident_type,
                priority=model.priority,
                lat=model.lat,
                lng=model.lng,
                status=model.status,
                reported_at=model.reported_at,
            )
            return incident
        finally:
            db.close()

    def rank_vehicles_for_incident(
        self,
        incident_id: str,
        scenario_id: Optional[str] = "morning_peak"
    ) -> VehicleRankingResponse:
        """
        Ranks candidate vehicles for an incident using A* Search on the road network.
        """
        db: Session = SessionLocal()
        try:
            inc_model = db.query(IncidentModel).filter(IncidentModel.incident_id == incident_id).first()
            if not inc_model:
                raise ValueError(f"Incident '{incident_id}' not found.")

            incident = EmergencyIncident(
                incident_id=inc_model.incident_id,
                title=inc_model.title,
                description=inc_model.description,
                incident_type=inc_model.incident_type,
                priority=inc_model.priority,
                lat=inc_model.lat,
                lng=inc_model.lng,
                status=inc_model.status,
                reported_at=inc_model.reported_at,
                assigned_vehicle_id=inc_model.assigned_vehicle_id,
            )

            # Find matching vehicle types
            allowed_types = SUITABILITY_MAP.get(inc_model.incident_type, ["ambulance", "fire_engine", "police"])
            candidates = db.query(VehicleModel).filter(
                VehicleModel.status == "available",
                VehicleModel.vehicle_type.in_(allowed_types)
            ).all()

            dest_node = self.routing_service.find_nearest_node(inc_model.lat, inc_model.lng)
            ranked_list: List[VehicleRankingCandidate] = []

            for veh in candidates:
                src_node = self.routing_service.find_nearest_node(veh.current_lat, veh.current_lng)
                
                # Compute route with A* Search
                route = self.routing_service.run_algorithm(
                    algorithm_name="astar",
                    source=src_node,
                    target=dest_node,
                    objective=RoutingObjective.TRAFFIC_AWARE,
                    scenario_id=scenario_id
                )

                if route.success:
                    tt_sec = route.estimated_travel_time_seconds
                    dist_km = route.path_distance_km
                    # Score: lower is better
                    score = tt_sec + (dist_km * 10.0)
                else:
                    tt_sec = 9999.0
                    dist_km = 999.0
                    score = 999999.0

                v_obj = Vehicle(
                    vehicle_id=veh.vehicle_id,
                    call_sign=veh.call_sign,
                    vehicle_type=veh.vehicle_type,
                    status=veh.status,
                    current_lat=veh.current_lat,
                    current_lng=veh.current_lng,
                    base_station=veh.base_station,
                )

                ranked_list.append(
                    VehicleRankingCandidate(
                        vehicle=v_obj,
                        estimated_travel_time_seconds=round(tt_sec, 1),
                        estimated_travel_time_minutes=round(tt_sec / 60.0, 2),
                        distance_km=dist_km,
                        suitability_score=round(score, 1),
                        rank=0,
                        route_preview=route if route.success else None
                    )
                )

            # Sort by score ascending
            ranked_list.sort(key=lambda x: x.suitability_score)
            for idx, item in enumerate(ranked_list):
                item.rank = idx + 1

            return VehicleRankingResponse(
                incident=incident,
                candidates_count=len(ranked_list),
                ranked_candidates=ranked_list,
            )
        finally:
            db.close()

    def execute_dispatch(
        self,
        req: DispatchExecutionRequest,
        scenario_id: Optional[str] = "morning_peak"
    ) -> DispatchExecutionResponse:
        """
        Locks vehicle assignment, updates vehicle status to 'dispatched',
        generates the authoritative response route, and commits assignment to database.
        """
        db: Session = SessionLocal()
        try:
            inc = db.query(IncidentModel).filter(IncidentModel.incident_id == req.incident_id).first()
            veh = db.query(VehicleModel).filter(VehicleModel.vehicle_id == req.vehicle_id).first()

            if not inc or not veh:
                raise ValueError("Invalid incident or vehicle identifier.")

            if inc.status == "dispatched":
                raise ValueError(f"Incident '{inc.title}' is already dispatched to vehicle '{inc.assigned_vehicle_id}'.")

            if veh.status != "available":
                raise ValueError(f"Vehicle '{veh.call_sign}' is currently '{veh.status}', not available.")

            # Compute route
            src_node = self.routing_service.find_nearest_node(veh.current_lat, veh.current_lng)
            dest_node = self.routing_service.find_nearest_node(inc.lat, inc.lng)

            route = self.routing_service.run_algorithm(
                algorithm_name="astar",
                source=src_node,
                target=dest_node,
                objective=RoutingObjective.TRAFFIC_AWARE,
                scenario_id=scenario_id
            )

            # Update statuses
            veh.status = "dispatched"
            veh.assigned_incident_id = inc.incident_id
            inc.status = "dispatched"
            inc.assigned_vehicle_id = veh.vehicle_id

            asgn_id = f"asgn_{uuid.uuid4().hex[:6]}"
            assignment = DispatchAssignmentModel(
                assignment_id=asgn_id,
                incident_id=inc.incident_id,
                vehicle_id=veh.vehicle_id,
                assigned_at=datetime.now(timezone.utc),
                estimated_eta_seconds=route.estimated_travel_time_seconds,
                estimated_distance_km=route.path_distance_km,
                algorithm_used="A_Star",
                status="active"
            )
            db.add(assignment)
            db.commit()

            return DispatchExecutionResponse(
                success=True,
                assignment_id=asgn_id,
                incident_id=inc.incident_id,
                vehicle_id=veh.vehicle_id,
                assigned_at=assignment.assigned_at.isoformat(),
                estimated_eta_minutes=route.estimated_travel_time_minutes,
                distance_km=route.path_distance_km,
                dispatch_route=route,
                message=f"Vehicle '{veh.call_sign}' dispatched to '{inc.title}' with ETA {route.estimated_travel_time_minutes} mins."
            )
        finally:
            db.close()

