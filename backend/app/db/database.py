from datetime import datetime, timezone
import logging
from pathlib import Path
from typing import Generator
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    create_engine,
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# Fallback to local SQLite database in data directory if PostgreSQL is not specified
DB_FILE = settings.DATA_DIR / "emergency_route.db"
DEFAULT_DB_URL = f"sqlite:///{DB_FILE}"
raw_db_url = getattr(settings, "DATABASE_URL", None) or DEFAULT_DB_URL
if raw_db_url.startswith("postgres://"):
    DATABASE_URL = raw_db_url.replace("postgres://", "postgresql://", 1)
else:
    DATABASE_URL = raw_db_url

# SQLite requires check_same_thread=False for FastAPI concurrency
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class VehicleModel(Base):
    __tablename__ = "vehicles"

    vehicle_id = Column(String(64), primary_key=True)
    call_sign = Column(String(64), nullable=False)
    vehicle_type = Column(String(32), nullable=False)  # ambulance, fire_engine, police
    status = Column(String(32), nullable=False, default="available")  # available, dispatched, in_transit
    current_lat = Column(Float, nullable=False)
    current_lng = Column(Float, nullable=False)
    base_station = Column(String(128), nullable=False)
    assigned_incident_id = Column(String(64), nullable=True)
    last_updated = Column(DateTime, default=lambda: datetime.now(timezone.utc))


class IncidentModel(Base):
    __tablename__ = "emergency_incidents"

    incident_id = Column(String(64), primary_key=True)
    title = Column(String(128), nullable=False)
    description = Column(Text, nullable=True)
    incident_type = Column(String(64), nullable=False)
    priority = Column(String(16), nullable=False)  # critical, high, medium, low
    lat = Column(Float, nullable=False)
    lng = Column(Float, nullable=False)
    status = Column(String(32), nullable=False, default="reported")  # reported, dispatched, resolved
    reported_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    assigned_vehicle_id = Column(String(64), nullable=True)
    resolved_at = Column(DateTime, nullable=True)


class DispatchAssignmentModel(Base):
    __tablename__ = "dispatch_assignments"

    assignment_id = Column(String(64), primary_key=True)
    incident_id = Column(String(64), nullable=False)
    vehicle_id = Column(String(64), nullable=False)
    assigned_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))
    estimated_eta_seconds = Column(Float, nullable=False)
    estimated_distance_km = Column(Float, nullable=False)
    algorithm_used = Column(String(32), default="A_Star")
    route_id = Column(String(64), nullable=True)
    status = Column(String(32), default="active")


class RouteHistoryModel(Base):
    __tablename__ = "route_history"

    route_id = Column(String(64), primary_key=True)
    source_node = Column(Integer, nullable=False)
    target_node = Column(Integer, nullable=False)
    algorithm_name = Column(String(64), nullable=False)
    routing_objective = Column(String(32), nullable=False)
    traffic_scenario = Column(String(64), nullable=False)
    distance_meters = Column(Float, nullable=False)
    travel_time_seconds = Column(Float, nullable=False)
    nodes_explored = Column(Integer, nullable=False)
    execution_time_ms = Column(Float, nullable=False)
    is_optimal = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))


def get_db() -> Generator:
    """Dependency for obtaining a transactional database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db(force_reset: bool = False, seed_test_fixtures: bool = False):
    """Initializes schema. Only seeds test fixtures when explicitly requested by isolated automated tests."""
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if force_reset:
            db.query(DispatchAssignmentModel).delete()
            db.query(IncidentModel).delete()
            db.query(VehicleModel).delete()
            db.commit()

        # Seed test fixtures ONLY when explicitly requested by isolated automated test suites
        if seed_test_fixtures and db.query(VehicleModel).count() == 0:
            logger.info("Loading isolated test fixtures for emergency vehicle fleet...")
            fixture_vehicles = [
                # Ambulances
                VehicleModel(
                    vehicle_id="amb_01",
                    call_sign="EMS-Alpha (ALS)",
                    vehicle_type="ambulance",
                    status="available",
                    current_lat=31.2223,
                    current_lng=75.7672,
                    base_station="Civil Hospital Phagwara",
                ),
                VehicleModel(
                    vehicle_id="amb_02",
                    call_sign="EMS-Bravo (BLS)",
                    vehicle_type="ambulance",
                    status="available",
                    current_lat=31.2536,
                    current_lng=75.7037,
                    base_station="LPU University Health Center",
                ),
                VehicleModel(
                    vehicle_id="amb_03",
                    call_sign="EMS-Charlie (ALS)",
                    vehicle_type="ambulance",
                    status="available",
                    current_lat=31.2201,
                    current_lng=75.7820,
                    base_station="Guru Nanak Bhai Lalo Hospital",
                ),
                VehicleModel(
                    vehicle_id="amb_04",
                    call_sign="EMS-Delta (BLS)",
                    vehicle_type="ambulance",
                    status="available",
                    current_lat=31.2140,
                    current_lng=75.7480,
                    base_station="Hadiabad Primary Health Sub-Center",
                ),
                # Fire Engines
                VehicleModel(
                    vehicle_id="fire_01",
                    call_sign="Tender-1",
                    vehicle_type="fire_engine",
                    status="available",
                    current_lat=31.2290,
                    current_lng=75.7610,
                    base_station="Satnampura Fire Station",
                ),
                VehicleModel(
                    vehicle_id="fire_02",
                    call_sign="Rescue-2",
                    vehicle_type="fire_engine",
                    status="available",
                    current_lat=31.2112,
                    current_lng=75.7891,
                    base_station="NH44 Industrial Substation",
                ),
                # Police Cruisers
                VehicleModel(
                    vehicle_id="pol_01",
                    call_sign="PCR-Hawk",
                    vehicle_type="police",
                    status="available",
                    current_lat=31.2185,
                    current_lng=75.7725,
                    base_station="Phagwara Railway Station Outpost",
                ),
                VehicleModel(
                    vehicle_id="pol_02",
                    call_sign="PCR-Interceptor",
                    vehicle_type="police",
                    status="available",
                    current_lat=31.2241,
                    current_lng=75.7695,
                    base_station="Hanumangarh Traffic Police Chowk",
                ),
            ]
            db.add_all(fixture_vehicles)
            db.commit()
            logger.info("Test fixtures loaded for test runner.")
    finally:
        db.close()

