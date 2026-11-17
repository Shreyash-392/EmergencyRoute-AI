from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.websocket_manager import websocket_manager
from app.db.database import init_db
from app.demo.demo_service import JudgeDemoService
from app.dispatch.dispatch_models import CreateIncidentRequest, DispatchExecutionRequest
from app.dispatch.dispatch_service import DispatchService
from app.main import app, get_demo_service, get_dispatch_service, get_routing_service


@pytest.fixture(scope="module", autouse=True)
def test_environment_lifecycle():
    init_db(force_reset=True, seed_test_fixtures=True)
    yield
    # Always tear down test fixtures after tests complete to strictly maintain Zero Fabricated Data policy in production database
    init_db(force_reset=True, seed_test_fixtures=False)


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


# -------------------------------------------------------------
# 1. Database & Fleet Management Tests
# -------------------------------------------------------------

def test_database_init_and_seed():
    init_db(force_reset=True, seed_test_fixtures=True)
    ds = get_dispatch_service()
    vehicles = ds.get_all_vehicles()
    assert len(vehicles) >= 8, f"Expected >= 8 seeded vehicles, found {len(vehicles)}"
    
    types = {v.vehicle_type for v in vehicles}
    assert "ambulance" in types
    assert "fire_engine" in types
    assert "police" in types


def test_incident_creation_and_listing():
    ds = get_dispatch_service()
    inc = ds.create_incident(
        CreateIncidentRequest(
            title="Test Cardiac Event at Hanumangarh Chowk",
            description="Patient needs emergency resuscitation.",
            incident_type="cardiac_arrest",
            priority="critical",
            lat=31.2241,
            lng=75.7695
        )
    )
    assert inc.incident_id.startswith("inc_")
    assert inc.status == "reported"

    all_incidents = ds.get_all_incidents()
    assert any(i.incident_id == inc.incident_id for i in all_incidents)


# -------------------------------------------------------------
# 2. Intelligent Vehicle Ranking & Dispatch Execution
# -------------------------------------------------------------

def test_vehicle_ranking_for_cardiac_arrest():
    ds = get_dispatch_service()
    # Rank available vehicles for the newly created incident
    incidents = ds.get_all_incidents()
    cardiac_inc = next(i for i in incidents if i.incident_type == "cardiac_arrest")

    ranking_resp = ds.rank_vehicles_for_incident(cardiac_inc.incident_id, scenario_id="morning_peak")
    assert ranking_resp.candidates_count > 0
    top_candidate = ranking_resp.ranked_candidates[0]

    assert top_candidate.rank == 1
    assert top_candidate.vehicle.vehicle_type == "ambulance"
    assert top_candidate.estimated_travel_time_seconds > 0
    assert top_candidate.distance_km > 0
    assert top_candidate.route_preview is not None
    assert top_candidate.route_preview.success is True


def test_dispatch_execution_workflow():
    ds = get_dispatch_service()
    incidents = ds.get_all_incidents()
    available_inc = next(i for i in incidents if i.status == "reported")
    
    ranking = ds.rank_vehicles_for_incident(available_inc.incident_id)
    top_veh = ranking.ranked_candidates[0].vehicle

    exec_resp = ds.execute_dispatch(
        DispatchExecutionRequest(
            incident_id=available_inc.incident_id,
            vehicle_id=top_veh.vehicle_id
        )
    )
    assert exec_resp.success is True
    assert exec_resp.assignment_id.startswith("asgn_")
    assert exec_resp.estimated_eta_minutes > 0
    assert exec_resp.dispatch_route.success is True

    # Verify status updates persisted
    updated_inc = next(i for i in ds.get_all_incidents() if i.incident_id == available_inc.incident_id)
    assert updated_inc.status == "dispatched"
    assert updated_inc.assigned_vehicle_id == top_veh.vehicle_id

    updated_veh = next(v for v in ds.get_all_vehicles() if v.vehicle_id == top_veh.vehicle_id)
    assert updated_veh.status == "dispatched"
    assert updated_veh.assigned_incident_id == available_inc.incident_id


def test_duplicate_assignment_prevention():
    ds = get_dispatch_service()
    incidents = ds.get_all_incidents()
    dispatched_inc = next(i for i in incidents if i.status == "dispatched")
    vehicles = ds.get_all_vehicles()
    dispatched_veh = next(v for v in vehicles if v.status == "dispatched")
    available_veh = next(v for v in vehicles if v.status == "available")

    # 1. Attempt to dispatch an already dispatched vehicle to a new incident
    new_inc = ds.create_incident(
        CreateIncidentRequest(
            title="Duplicate assignment check",
            description="Testing vehicle locking",
            incident_type="general_medical",
            priority="medium",
            lat=31.2200,
            lng=75.7700
        )
    )
    with pytest.raises(ValueError, match="not available"):
        ds.execute_dispatch(
            DispatchExecutionRequest(
                incident_id=new_inc.incident_id,
                vehicle_id=dispatched_veh.vehicle_id
            )
        )

    # 2. Attempt to assign an already dispatched incident
    with pytest.raises(ValueError, match="already dispatched"):
        ds.execute_dispatch(
            DispatchExecutionRequest(
                incident_id=dispatched_inc.incident_id,
                vehicle_id=available_veh.vehicle_id
            )
        )


# -------------------------------------------------------------
# 3. WebSocket Manager & Polling Buffer
# -------------------------------------------------------------

import asyncio

def test_websocket_broadcast_buffer():
    asyncio.run(websocket_manager.broadcast("test_event", {"message": "Emergency dispatch alert"}))
    recent = websocket_manager.get_recent_events(limit=5)
    assert len(recent) > 0
    last_event = recent[-1]
    assert last_event["type"] == "test_event"
    assert last_event["data"]["message"] == "Emergency dispatch alert"


# -------------------------------------------------------------
# 4. Judge Demonstration Mode Tests
# -------------------------------------------------------------

def test_judge_demo_baseline():
    demo = get_demo_service()
    baseline = demo.get_initial_demo_state()
    assert baseline["step"] == 1
    assert "algorithm_comparison" in baseline
    assert "results" in baseline["algorithm_comparison"]
    assert "delhivery_reference" in baseline
    assert baseline["algorithm_comparison"]["results"]["A_Star"]["is_optimal"] is True


def test_judge_demo_incident_and_reroute():
    demo = get_demo_service()
    reroute_state = demo.simulate_incident_and_reroute()
    assert reroute_state["step"] == 2
    assert "blocked_segment" in reroute_state
    assert reroute_state["reroute_result"]["reroute_triggered"] is True
    assert reroute_state["reroute_result"]["decision"] == "MANDATORY_REROUTE"

    # Reset
    reset_resp = demo.reset_demonstration()
    assert reset_resp["status"] == "success"


# -------------------------------------------------------------
# 5. FastAPI Endpoints Integration
# -------------------------------------------------------------

def test_api_dispatch_vehicles_and_incidents(api_client):
    # GET vehicles
    res_v = api_client.get("/api/v1/dispatch/vehicles")
    assert res_v.status_code == 200
    vehicles = res_v.json()
    assert len(vehicles) >= 8

    # Create an incident via dispatch intake endpoint
    post_res = api_client.post("/api/v1/dispatch/incidents", json={
        "title": "API Verification Call",
        "description": "Verification of intake pipeline",
        "incident_type": "cardiac_arrest",
        "priority": "critical",
        "lat": 31.2215,
        "lng": 75.7738
    })
    assert post_res.status_code == 200

    # GET incidents and verify it is present
    res_i = api_client.get("/api/v1/dispatch/incidents")
    assert res_i.status_code == 200
    incidents = res_i.json()
    assert len(incidents) > 0
    assert any(i["title"] == "API Verification Call" for i in incidents)


def test_api_judge_demo_endpoints(api_client):
    # Baseline
    res_base = api_client.get("/api/v1/demo/baseline")
    assert res_base.status_code == 200
    data_base = res_base.json()
    assert data_base["step"] == 1
    assert "A_Star" in data_base["algorithm_comparison"]["results"]

    # Incident injection
    res_inc = api_client.post("/api/v1/demo/simulate-incident")
    assert res_inc.status_code == 200
    data_inc = res_inc.json()
    assert data_inc["step"] == 2

    # Reset
    res_reset = api_client.post("/api/v1/demo/reset")
    assert res_reset.status_code == 200
