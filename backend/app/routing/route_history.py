from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

from app.algorithms.algorithm_metrics import AlgorithmResult


class RerouteEvent(BaseModel):
    event_id: str
    route_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    trigger_reason: str
    decision: str
    old_travel_time_seconds: float
    new_travel_time_seconds: float
    time_saved_seconds: float
    old_node_count: int
    new_node_count: int


class ActiveRouteRecord(BaseModel):
    route_id: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    source_node: int
    target_node: int
    current_route: AlgorithmResult
    reroute_history: List[RerouteEvent] = Field(default_factory=list)


class RouteHistoryManager:
    """
    Manages active emergency dispatch routes and their dynamic rerouting audit history.
    """

    def __init__(self):
        self._routes: Dict[str, ActiveRouteRecord] = {}

    def register_route(self, route_id: str, route: AlgorithmResult) -> ActiveRouteRecord:
        record = ActiveRouteRecord(
            route_id=route_id,
            source_node=route.source_node,
            target_node=route.target_node,
            current_route=route
        )
        self._routes[route_id] = record
        return record

    def get_route(self, route_id: str) -> Optional[ActiveRouteRecord]:
        return self._routes.get(route_id)

    def record_reroute(
        self,
        route_id: str,
        new_route: AlgorithmResult,
        reason: str,
        decision: str,
        event_id: str
    ) -> Optional[RerouteEvent]:
        record = self._routes.get(route_id)
        if not record:
            return None

        old_tt = record.current_route.estimated_travel_time_seconds
        new_tt = new_route.estimated_travel_time_seconds

        event = RerouteEvent(
            event_id=event_id,
            route_id=route_id,
            trigger_reason=reason,
            decision=decision,
            old_travel_time_seconds=old_tt,
            new_travel_time_seconds=new_tt,
            time_saved_seconds=round(old_tt - new_tt, 2),
            old_node_count=len(record.current_route.node_path),
            new_node_count=len(new_route.node_path)
        )
        record.reroute_history.append(event)
        record.current_route = new_route
        return event

    def list_routes(self) -> List[ActiveRouteRecord]:
        return list(self._routes.values())

