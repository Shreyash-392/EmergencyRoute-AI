from pathlib import Path
import sys
import unittest.mock as mock
import pytest
import networkx as nx
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.core.config import settings
from app.core.graph_loader import load_graph_from_graphml
from app.integrations.delhivery.client import (
    DelhiveryClient,
    DelhiveryAuthError,
    DelhiveryRateLimitError,
    redact_sensitive,
)
from app.integrations.delhivery.geocoding_service import DelhiveryGeocodingService
from app.integrations.delhivery.routing_service import DelhiveryRoutingService
from app.integrations.traffic.mock_traffic import MockTrafficProvider
from app.integrations.traffic.traffic_models import CongestionLevel
from app.main import app
from app.services.graph_service import GraphService
from app.services.validation_service import validate_road_network


@pytest.fixture(scope="module")
def graph():
    """Loads authoritative GraphML for Phagwara."""
    return load_graph_from_graphml()


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


# -------------------------------------------------------------
# 1. Road Network Graph & OSM Extraction Integrity Tests
# -------------------------------------------------------------

def test_graph_structure_and_type(graph):
    assert isinstance(graph, nx.MultiDiGraph), "Graph must be a directed MultiDiGraph"
    assert graph.is_directed(), "Graph must be directed to respect one-way roads"
    assert len(graph.nodes) > 1000, f"Expected >1000 nodes, got {len(graph.nodes)}"
    assert len(graph.edges) > 2000, f"Expected >2000 edges, got {len(graph.edges)}"


def test_edge_attributes_integrity(graph):
    """Verifies lengths, travel times, and speed limit differentiation."""
    for u, v, k, data in graph.edges(keys=True, data=True):
        assert "length" in data and float(data["length"]) > 0, f"Invalid length on edge ({u}, {v}, {k})"
        assert "travel_time" in data and float(data["travel_time"]) > 0, f"Invalid travel_time on edge ({u}, {v}, {k})"
        assert "speed_kph" in data and float(data["speed_kph"]) > 0, f"Invalid speed_kph on edge ({u}, {v}, {k})"
        assert "speed_source" in data, f"Missing speed_source attribution on edge ({u}, {v}, {k})"
        assert data["speed_source"] in ("osm_tag", "imputed_hwy_class")


def test_parallel_edges_preserved(graph):
    """Verifies that parallel edges (multi-edges) are preserved with distinct keys."""
    pairs = {}
    for u, v, k in graph.edges(keys=True):
        pairs[(u, v)] = pairs.get((u, v), 0) + 1

    parallel_pairs = {pair: count for pair, count in pairs.items() if count > 1}
    assert len(parallel_pairs) > 0, "Graph should preserve parallel edge pairs where present in OSM"


def test_connectivity_metrics(graph):
    """Verifies connectivity components and largest WCC coverage."""
    wccs = list(nx.weakly_connected_components(graph))
    assert len(wccs) > 0
    largest_wcc = max(wccs, key=len)
    coverage = len(largest_wcc) / len(graph.nodes)
    assert coverage >= 0.95, f"Largest WCC coverage ({coverage:.2%}) should cover >=95% of road nodes"


def test_validation_service_audit(graph):
    report = validate_road_network(graph)
    assert report["status"] == "PASS"
    assert report["is_valid"] is True
    assert report["graph_type"] == "MultiDiGraph"
    assert report["nodes_count"] == len(graph.nodes)
    assert report["edges_count"] == len(graph.edges)


# -------------------------------------------------------------
# 2. Graph Service & Directed Routing Tests
# -------------------------------------------------------------

def test_graph_service_nearest_node_and_route(graph):
    gs = GraphService(graph=graph)

    # Coordinates near Civil Hospital Phagwara and Railway Station
    hosp_lat, hosp_lng = 31.2223, 75.7672
    rail_lat, rail_lng = 31.2185, 75.7725

    node_hosp = gs.find_nearest_node(hosp_lat, hosp_lng)
    node_rail = gs.find_nearest_node(rail_lat, rail_lng)

    assert isinstance(node_hosp, int)
    assert isinstance(node_rail, int)
    assert node_hosp in graph.nodes
    assert node_rail in graph.nodes

    # Route calculation
    route = gs.calculate_reference_route(hosp_lat, hosp_lng, rail_lat, rail_lng)
    assert route["success"] is True
    assert route["total_distance_meters"] > 0
    assert route["total_travel_time_seconds"] > 0
    assert len(route["route_coordinates"]) >= 2
    assert len(route["segments"]) > 0


# -------------------------------------------------------------
# 3. Traffic Provider & Synthetic Scenario Tests
# -------------------------------------------------------------

def test_mock_traffic_provider_determinism():
    prov1 = MockTrafficProvider(seed=42)
    prov2 = MockTrafficProvider(seed=42)

    obs1 = prov1.generate_observation_for_edge(
        u=10, v=20, key=0, length=200.0, baseline_speed_kph=40.0,
        highway_class="primary", name="GT Road", scenario_id="morning_peak"
    )
    obs2 = prov2.generate_observation_for_edge(
        u=10, v=20, key=0, length=200.0, baseline_speed_kph=40.0,
        highway_class="primary", name="GT Road", scenario_id="morning_peak"
    )

    assert obs1.current_speed_kph == obs2.current_speed_kph
    assert obs1.speed_ratio == obs2.speed_ratio
    assert obs1.is_live is False
    assert obs1.source == "synthetic_simulation"


def test_traffic_application_to_graph(graph):
    prov = MockTrafficProvider(seed=42)
    G_copy = graph.copy()
    
    prov.apply_traffic_to_graph(G_copy, scenario_id="evening_peak")

    sample_edge = list(G_copy.edges(keys=True, data=True))[0]
    data = sample_edge[3]

    assert "dynamic_speed_kph" in data
    assert "dynamic_travel_time" in data
    assert "congestion_level" in data
    assert data["traffic_source"] == "synthetic_simulation"
    assert data["is_live_traffic"] is False


# -------------------------------------------------------------
# 4. Delhivery Maps Integration & Resilience Tests
# -------------------------------------------------------------

def test_credential_redaction():
    text = "Authorization: Bearer secret_delhivery_token_12345; key=abc123456789"
    redacted = redact_sensitive(text)
    assert "secret_delhivery_token_12345" not in redacted
    assert "abc123456789" not in redacted
    assert "[REDACTED]" in redacted


def test_delhivery_client_unconfigured_fallback():
    client = DelhiveryClient(api_key=None)
    assert client.is_configured is False
    with pytest.raises(DelhiveryAuthError):
        client.request("GET", "/test/endpoint")


def test_delhivery_geocoding_fallback():
    client = DelhiveryClient(api_key=None)
    geo_svc = DelhiveryGeocodingService(client=client)

    res = geo_svc.search_locations("Civil Hospital", limit=3)
    assert res.count > 0
    assert res.is_fallback is True
    assert "Hospital" in res.results[0].display_name


def test_delhivery_routing_fallback(graph):
    client = DelhiveryClient(api_key=None)
    gs = GraphService(graph=graph)
    routing_svc = DelhiveryRoutingService(client=client, graph_service=gs)

    res = routing_svc.get_route(31.2223, 75.7672, 31.2185, 75.7725)
    assert res.success is True
    assert res.is_fallback is True
    assert res.distance_meters > 0
    assert res.duration_seconds > 0


def test_delhivery_client_retry_and_rate_limit():
    client = DelhiveryClient(api_key="mock_key_12345678", max_retries=2)
    
    mock_resp = mock.MagicMock()
    mock_resp.status_code = 429

    with mock.patch("httpx.Client.request", return_value=mock_resp):
        with pytest.raises(DelhiveryRateLimitError):
            client.request("GET", "/test/endpoint")


# -------------------------------------------------------------
# 5. FastAPI Endpoints Integration Tests
# -------------------------------------------------------------

def test_api_health(api_client):
    res = api_client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert data["service"] == "EmergencyRoute AI"
    assert data["graph_loaded"] is True
    assert data["graph_nodes"] > 1000


def test_api_map_config(api_client):
    res = api_client.get("/api/v1/map/config")
    assert res.status_code == 200
    data = res.json()
    assert "tile_url_template" in data
    assert "attribution" in data


def test_api_location_search(api_client):
    res = api_client.get("/api/v1/map/locations/search?q=LPU&limit=2")
    assert res.status_code == 200
    data = res.json()
    assert data["count"] > 0
    assert "LPU" in data["results"][0]["display_name"] or "University" in data["results"][0]["display_name"]


def test_api_road_statistics(api_client):
    res = api_client.get("/api/v1/roads/statistics")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "PASS"
    assert data["is_multidigraph"] is True
    assert data["nodes_count"] > 1000


def test_api_traffic_status(api_client):
    res = api_client.get("/api/v1/traffic/status?scenario=morning_peak")
    assert res.status_code == 200
    data = res.json()
    assert data["active_scenario"]["scenario_id"] == "morning_peak"
    assert len(data["available_scenarios"]) >= 6
    assert data["is_live_data"] is False


def test_api_routes_reference(api_client):
    res = api_client.get(
        "/api/v1/routes/reference?origin_lat=31.2223&origin_lng=75.7672&dest_lat=31.2185&dest_lng=75.7725"
    )
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["distance_km"] > 0
    assert data["duration_minutes"] > 0

