from datetime import datetime, timedelta, timezone
from pathlib import Path
import sys
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.algorithms.algorithm_metrics import RoutingObjective
from app.algorithms.astar import a_star_search
from app.algorithms.graph_adapter import MultiGraphAdapter
from app.core.graph_loader import load_graph_from_graphml
from app.main import app
from app.routing.rerouting_service import ReroutingService
from app.routing.route_comparator import RouteComparator
from app.routing.route_validator import RouteValidator
from app.routing.routing_service import RoutingService
from app.traffic.road_closure_manager import RoadClosureManager
from app.traffic.traffic_fusion import TrafficFusionEngine
from app.traffic.traffic_service import TrafficService
from app.traffic.traffic_validator import TrafficValidator
from app.traffic.traffic_weight_calculator import TrafficWeightCalculator


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


@pytest.fixture(scope="module")
def phagwara_graph():
    return load_graph_from_graphml()


# -------------------------------------------------------------
# 1. Traffic Validation & Weight Calculation Tests
# -------------------------------------------------------------

def test_traffic_validator_sources_and_staleness():
    validator = TrafficValidator(max_stale_seconds=600)
    now = datetime.now(timezone.utc)

    # Valid observation
    valid_obs = {
        "source": "synthetic_simulation",
        "u": 101,
        "v": 102,
        "current_speed_kph": 35.0,
        "confidence": 0.9,
        "timestamp": now.isoformat()
    }
    res = validator.validate_observation(valid_obs, current_time=now)
    assert res.is_valid is True
    assert res.is_stale is False

    # Invalid source
    bad_source_obs = dict(valid_obs, source="untrusted_hack")
    assert validator.validate_observation(bad_source_obs, current_time=now).is_valid is False

    # Implausible speed
    bad_speed_obs = dict(valid_obs, current_speed_kph=250.0)
    assert validator.validate_observation(bad_speed_obs, current_time=now).is_valid is False

    # Stale observation (30 minutes old)
    old_time = now - timedelta(minutes=30)
    stale_obs = dict(valid_obs, timestamp=old_time.isoformat())
    stale_res = validator.validate_observation(stale_obs, current_time=now)
    assert stale_res.is_valid is True
    assert stale_res.is_stale is True


def test_traffic_weight_calculator_clamping_and_tt():
    weight = TrafficWeightCalculator.calculate_edge_weight(
        length_meters=1000.0,
        base_speed_kph=50.0,
        current_speed_kph=25.0
    )
    # At 25 km/h = 6.944 m/s -> 1000m takes ~144 seconds
    assert 143.0 <= weight["dynamic_travel_time"] <= 145.0
    assert weight["speed_ratio"] == 0.5
    assert weight["congestion_level"] == "moderate"

    # Extreme creep speed clamping (0 km/h clamped to min speed 5 km/h)
    creep = TrafficWeightCalculator.calculate_edge_weight(
        length_meters=500.0,
        base_speed_kph=40.0,
        current_speed_kph=0.0
    )
    assert creep["effective_speed_kph"] == 5.0
    assert creep["congestion_level"] == "severe"


# -------------------------------------------------------------
# 2. Road Closures & Traffic Fusion Tests
# -------------------------------------------------------------

def test_road_closure_manager():
    rcm = RoadClosureManager()
    rcm.add_closure("cl_01", u=10, v=20, key=0, reason="Accident")
    assert rcm.is_closed(10, 20, 0) is True
    assert (10, 20, 0) in rcm.get_closed_edges()

    rcm.remove_closure("cl_01")
    assert rcm.is_closed(10, 20, 0) is False


def test_traffic_fusion_engine():
    engine = TrafficFusionEngine()
    
    fallback = [
        {"u": 1, "v": 2, "key": 0, "length_meters": 100.0, "baseline_speed_kph": 40.0, "current_speed_kph": 38.0, "source": "synthetic_simulation"}
    ]
    # Primary telematics with higher confidence overrides
    primary = [
        {"u": 1, "v": 2, "key": 0, "length_meters": 100.0, "baseline_speed_kph": 40.0, "current_speed_kph": 15.0, "source": "delhivery_telematics", "confidence": 0.95}
    ]

    fused = engine.fuse_observations(primary_observations=primary, fallback_observations=fallback)
    assert (1, 2, 0) in fused
    assert fused[(1, 2, 0)]["effective_speed_kph"] == 15.0
    assert fused[(1, 2, 0)]["traffic_source"] == "delhivery_telematics"


# -------------------------------------------------------------
# 3. Dynamic Rerouting Engine Tests
# -------------------------------------------------------------

def test_rerouting_on_road_closure(phagwara_graph):
    ts = TrafficService(graph=phagwara_graph)
    rs = RoutingService(graph=phagwara_graph, traffic_service=ts)
    reroute_svc = ReroutingService(routing_service=rs)

    import osmnx as ox
    src = int(ox.distance.nearest_nodes(phagwara_graph, X=75.7672, Y=31.2223))
    tgt = int(ox.distance.nearest_nodes(phagwara_graph, X=75.7738, Y=31.2215))

    adapter = ts.create_graph_adapter()
    initial_route = a_star_search(adapter, src, tgt, RoutingObjective.TRAFFIC_AWARE)
    assert initial_route.success is True

    # Block an edge that is currently on the path
    segment_to_block = initial_route.edge_path[len(initial_route.edge_path) // 2]
    closure_dict = {
        "closure_id": "test_block_01",
        "u": segment_to_block.u,
        "v": segment_to_block.v,
        "key": segment_to_block.key,
        "reason": "Test vehicle breakdown blocking entire road"
    }

    reroute_resp = reroute_svc.process_dynamic_reroute(
        route_id="route_test_01",
        current_route=initial_route,
        new_closures=[closure_dict]
    )

    # Reroute MUST be triggered because road became impassable
    assert reroute_resp.reroute_triggered is True
    assert reroute_resp.decision == "MANDATORY_REROUTE"
    assert reroute_resp.active_route.success is True
    # The blocked edge must not be in the new route
    new_edge_tuples = [(s.u, s.v, s.key) for s in reroute_resp.active_route.edge_path]
    assert (segment_to_block.u, segment_to_block.v, segment_to_block.key) not in new_edge_tuples


# -------------------------------------------------------------
# 4. Phase 2 FastAPI REST Endpoints Tests
# -------------------------------------------------------------

def test_api_routes_optimal(api_client):
    payload = {
        "origin_lat": 31.2223,
        "origin_lng": 75.7672,
        "dest_lat": 31.2215,
        "dest_lng": 75.7738,
        "objective": "traffic_aware",
        "scenario_id": "morning_peak"
    }
    res = api_client.post("/api/v1/routes/optimal", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["algorithm_name"] == "A* Search"
    assert data["is_optimal"] is True
    assert len(data["node_path"]) >= 2
    assert data["path_distance_km"] > 0


def test_api_routes_compare(api_client):
    payload = {
        "origin_lat": 31.2223,
        "origin_lng": 75.7672,
        "dest_lat": 31.2215,
        "dest_lng": 75.7738,
        "objective": "traffic_aware",
        "scenario_id": "evening_peak"
    }
    res = api_client.post("/api/v1/routes/compare", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "results" in data
    assert "BFS" in data["results"]
    assert "DFS" in data["results"]
    assert "Greedy_Best_First" in data["results"]
    assert "A_Star" in data["results"]
    assert data["results"]["A_Star"]["is_optimal"] is True


def test_api_traffic_get_and_simulate(api_client):
    # GET traffic summary
    res_get = api_client.get("/api/v1/traffic")
    assert res_get.status_code == 200
    data_get = res_get.json()
    assert "active_scenario" in data_get
    assert len(data_get["available_scenarios"]) >= 6

    # POST simulate scenario
    res_sim = api_client.post("/api/v1/traffic/simulate", json={"scenario_id": "evening_peak"})
    assert res_sim.status_code == 200
    data_sim = res_sim.json()
    assert data_sim["status"] == "success"
    assert data_sim["scenario_id"] == "evening_peak"


def test_api_traffic_closures_management(api_client):
    # Add closure
    add_payload = {
        "action": "add",
        "closure_id": "api_test_closure",
        "u": 100,
        "v": 200,
        "key": 0,
        "reason": "Water pipe leak"
    }
    res_add = api_client.post("/api/v1/traffic/closures", json=add_payload)
    assert res_add.status_code == 200

    # Remove closure
    rem_payload = {
        "action": "remove",
        "closure_id": "api_test_closure"
    }
    res_rem = api_client.post("/api/v1/traffic/closures", json=rem_payload)
    assert res_rem.status_code == 200


def test_api_traffic_providers(api_client):
    res = api_client.get("/api/v1/traffic/providers")
    assert res.status_code == 200
    providers = res.json()
    assert len(providers) >= 3
    provider_ids = [p["provider_id"] for p in providers]
    assert "delhivery_telematics" in provider_ids
    assert "synthetic_simulation" in provider_ids


def test_api_algorithms_metrics(api_client):
    res = api_client.get("/api/v1/algorithms/metrics")
    assert res.status_code == 200
    data = res.json()
    assert "algorithms" in data
    assert "BFS" in data["algorithms"]
    assert "A_Star" in data["algorithms"]
    assert data["guarantees"]["admissibility_verified"] is True

