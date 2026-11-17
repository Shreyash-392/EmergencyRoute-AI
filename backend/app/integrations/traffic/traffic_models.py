from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class CongestionLevel(str, Enum):
    FREE_FLOW = "free_flow"
    LOW = "low"
    MODERATE = "moderate"
    HEAVY = "heavy"
    SEVERE = "severe"


class RoadStatus(str, Enum):
    OPEN = "open"
    SLOW = "slow"
    ACCIDENT = "accident"
    ROADWORK = "roadwork"
    CLOSED = "closed"


class TrafficObservation(BaseModel):
    edge_id: str = Field(..., description="Unique edge identifier formatted as 'u_v_key'")
    u: int = Field(..., description="Start node ID")
    v: int = Field(..., description="End node ID")
    key: int = Field(default=0, description="MultiDiGraph parallel edge key")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    baseline_speed_kph: float
    current_speed_kph: float
    speed_ratio: float = Field(..., description="current_speed / baseline_speed (0.0 to 1.5)")
    congestion_level: CongestionLevel
    road_status: RoadStatus = RoadStatus.OPEN
    travel_time_seconds: float
    is_live: bool = False
    source: str = Field(..., description="'synthetic_simulation', 'delhivery_telematics', or 'manual_override'")
    confidence: float = Field(default=0.9, ge=0.0, le=1.0)


class RoadClosure(BaseModel):
    closure_id: str
    edge_id: str
    u: int
    v: int
    key: int = 0
    reason: str
    severity: str = "impassable"
    start_time: Optional[datetime] = None
    expected_end_time: Optional[datetime] = None


class TrafficScenario(BaseModel):
    scenario_id: str
    name: str
    description: str
    time_of_day: str
    affected_corridors: List[str]
    global_congestion_factor: float
    closures_count: int = 0

