from pathlib import Path
import sys
import unittest.mock as mock
import httpx
import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.integrations.osrm.client import OSRMClient, OSRMClientError
from app.integrations.osrm.service import OSRMService
from app.integrations.osrm.schemas import OSRMRouteResponse
from app.main import app, get_osrm_service


@pytest.fixture(scope="module")
def api_client():
    return TestClient(app)


# Sample Mock OSRM Response for Phagwara (Model Town to Civil Hospital)
MOCK_OSRM_OK_RESPONSE = {
    "code": "Ok",
    "routes": [
        {
            "geometry": {
                "coordinates": [
                    [75.779224, 31.225993],
                    [75.779225, 31.226017],
                    [75.779208, 31.226351],
                    [75.775000, 31.224000],
                    [75.767200, 31.222300],
                ],
                "type": "LineString",
            },
            "legs": [
                {
                    "summary": "GT Road, Banga Road",
                    "weight": 350.5,
                    "duration": 309.2,
                    "steps": [
                        {
                            "name": "Model Town Main Road",
                            "distance": 150.0,
                            "duration": 25.0,
                            "mode": "driving",
                            "maneuver": {
                                "bearing_after": 2,
                                "bearing_before": 0,
                                "location": [75.779224, 31.225993],
                                "modifier": "left",
                                "type": "depart",
                            },
                        },
                        {
                            "name": "Grand Trunk Road (NH44)",
                            "distance": 1800.0,
                            "duration": 180.0,
                            "mode": "driving",
                            "maneuver": {
                                "bearing_after": 270,
                                "bearing_before": 180,
                                "location": [75.775000, 31.224000],
                                "modifier": "right",
                                "type": "turn",
                            },
                        },
                        {
                            "name": "Civil Hospital Approach Road",
                            "distance": 1010.7,
                            "duration": 104.2,
                            "mode": "driving",
                            "maneuver": {
                                "bearing_after": 0,
                                "bearing_before": 270,
                                "location": [75.767200, 31.222300],
                                "type": "arrive",
                            },
                        },
                    ],
                    "distance": 2960.7,
                }
            ],
            "weight_name": "routability",
            "weight": 350.5,
            "duration": 309.2,
            "distance": 2960.7,
        }
    ],
    "waypoints": [
        {"hint": "hint_origin", "distance": 2.5, "name": "Model Town", "location": [75.779224, 31.225993]},
        {"hint": "hint_dest", "distance": 1.2, "name": "Civil Hospital", "location": [75.767200, 31.222300]},
    ],
}


# --------------------------------------------------------------------------
# 1. Coordinate Validation Tests
# --------------------------------------------------------------------------

def test_osrm_coordinate_validation():
    client = OSRMClient()

    # Valid coordinates pass
    client.validate_coordinates(31.2260, 75.7790, 31.2223, 75.7672)

    # Invalid latitude > 90
    with pytest.raises(OSRMClientError) as exc_info:
        client.validate_coordinates(95.0, 75.77, 31.22, 75.76)
    assert exc_info.value.code == "InvalidCoordinates"
    assert "Latitude 95.0 out of range" in exc_info.value.message

    # Invalid longitude < -180
    with pytest.raises(OSRMClientError) as exc_info:
        client.validate_coordinates(31.22, -185.0, 31.22, 75.76)
    assert exc_info.value.code == "InvalidCoordinates"
    assert "Longitude -185.0 out of range" in exc_info.value.message

    # Missing / None coordinate
    with pytest.raises(OSRMClientError) as exc_info:
        client.validate_coordinates(None, 75.77, 31.22, 75.76)  # type: ignore
    assert exc_info.value.code == "InvalidCoordinates"


# --------------------------------------------------------------------------
# 2. Successful OSRM Mocked Response & Extraction Tests
# --------------------------------------------------------------------------

def test_osrm_successful_response_mocked():
    mock_client = mock.MagicMock(spec=OSRMClient)
    mock_client.get_route_raw.return_value = MOCK_OSRM_OK_RESPONSE

    service = OSRMService(client=mock_client)
    res: OSRMRouteResponse = service.get_route(
        origin_lat=31.2260,
        origin_lng=75.7790,
        dest_lat=31.2223,
        dest_lng=75.7672,
    )

    assert res.success is True
    assert res.provider == "osrm"
    assert res.code == "Ok"
    assert res.is_live_traffic is False
    assert "not real-time live traffic" in res.disclaimer

    # Verify route extraction
    route = res.route
    assert route is not None
    assert route.distance_meters == 2960.7
    assert route.distance_km == 2.961
    assert route.duration_seconds == 309.2
    assert route.duration_minutes == 5.15

    # Verify GeoJSON and Leaflet coordinate conversion
    assert route.geometry["type"] == "LineString"
    assert len(route.geometry["coordinates"]) == 5
    # GeoJSON is [lng, lat]
    assert route.geometry["coordinates"][0] == [75.779224, 31.225993]
    # Leaflet is [lat, lng]
    assert len(route.coordinates) == 5
    assert route.coordinates[0] == [31.225993, 75.779224]

    # Verify Legs and Steps
    assert len(route.legs) == 1
    assert len(route.legs[0].steps) == 3
    assert len(route.turn_by_turn) == 3
    assert "Depart heading left onto Model Town Main Road" in route.turn_by_turn[0]
    assert "Turn right onto Grand Trunk Road (NH44)" in route.turn_by_turn[1]
    assert "Arrive at destination" in route.turn_by_turn[2]


# --------------------------------------------------------------------------
# 3. No Route Found Handling
# --------------------------------------------------------------------------

def test_osrm_no_route_response():
    mock_client = mock.MagicMock(spec=OSRMClient)
    mock_client.get_route_raw.return_value = {
        "code": "NoRoute",
        "message": "Impossible route between points",
        "routes": [],
    }

    service = OSRMService(client=mock_client)
    res = service.get_route(31.2260, 75.7790, 31.2223, 75.7672)

    assert res.success is False
    assert res.code == "NoRoute"
    assert res.route is None
    assert "Impossible route" in res.message


# --------------------------------------------------------------------------
# 4. Timeout Handling
# --------------------------------------------------------------------------

def test_osrm_timeout_handling():
    mock_client = mock.MagicMock(spec=OSRMClient)
    mock_client.get_route_raw.side_effect = OSRMClientError(
        code="Timeout",
        message="OSRM server timed out after 8.0 seconds.",
        status_code=504,
    )

    service = OSRMService(client=mock_client)
    res = service.get_route(31.2260, 75.7790, 31.2223, 75.7672)

    assert res.success is False
    assert res.code == "Timeout"
    assert "timed out" in res.message


# --------------------------------------------------------------------------
# 5. HTTP Error Handling
# --------------------------------------------------------------------------

def test_osrm_http_error_handling():
    mock_client = mock.MagicMock(spec=OSRMClient)
    mock_client.get_route_raw.side_effect = OSRMClientError(
        code="HTTPError",
        message="OSRM server returned HTTP 502 Bad Gateway",
        status_code=502,
    )

    service = OSRMService(client=mock_client)
    res = service.get_route(31.2260, 75.7790, 31.2223, 75.7672)

    assert res.success is False
    assert res.code == "HTTPError"
    assert res.route is None


# --------------------------------------------------------------------------
# 6. API Endpoint Integration (/api/v1/routes/osrm)
# --------------------------------------------------------------------------

def test_api_osrm_endpoint_success(api_client, monkeypatch):
    # Mock OSRM client within FastAPI app context
    def mock_get_route_raw(*args, **kwargs):
        return MOCK_OSRM_OK_RESPONSE

    monkeypatch.setattr(get_osrm_service().client, "get_route_raw", mock_get_route_raw)

    resp = api_client.get(
        "/api/v1/routes/osrm",
        params={
            "origin_lat": 31.2260,
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["success"] is True
    assert data["provider"] == "osrm"
    assert data["distance_km"] == 2.961
    assert data["duration_minutes"] == 5.15
    assert len(data["route"]["coordinates"]) == 5


def test_api_osrm_endpoint_invalid_coordinates(api_client):
    # Out of range latitude
    resp = api_client.get(
        "/api/v1/routes/osrm",
        params={
            "origin_lat": 131.2260,  # Invalid > 90
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
        },
    )
    assert resp.status_code == 422 or resp.status_code == 400


def test_api_osrm_endpoint_no_route(api_client, monkeypatch):
    def mock_get_route_raw(*args, **kwargs):
        return {"code": "NoRoute", "message": "No route found", "routes": []}

    monkeypatch.setattr(get_osrm_service().client, "get_route_raw", mock_get_route_raw)

    resp = api_client.get(
        "/api/v1/routes/osrm",
        params={
            "origin_lat": 31.2260,
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
        },
    )
    assert resp.status_code == 404
    assert "No route found" in resp.json()["detail"]


def test_api_osrm_endpoint_timeout(api_client, monkeypatch):
    def mock_get_route_raw(*args, **kwargs):
        raise OSRMClientError(code="Timeout", message="Request timed out", status_code=504)

    monkeypatch.setattr(get_osrm_service().client, "get_route_raw", mock_get_route_raw)

    resp = api_client.get(
        "/api/v1/routes/osrm",
        params={
            "origin_lat": 31.2260,
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
        },
    )
    assert resp.status_code == 504
    assert "timed out" in resp.json()["detail"]


# --------------------------------------------------------------------------
# 7. Local A* Fallback Guarantee (Local A* remains 100% operational)
# --------------------------------------------------------------------------

def test_local_astar_unaffected_when_osrm_fails(api_client, monkeypatch):
    # Simulate OSRM service down
    def mock_broken_osrm(*args, **kwargs):
        raise OSRMClientError(code="NetworkError", message="OSRM cluster offline", status_code=502)

    monkeypatch.setattr(get_osrm_service().client, "get_route_raw", mock_broken_osrm)

    # 1. Verify OSRM endpoint fails cleanly
    osrm_resp = api_client.get(
        "/api/v1/routes/osrm",
        params={
            "origin_lat": 31.2260,
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
        },
    )
    assert osrm_resp.status_code == 502

    # 2. Verify Local A* route calculation remains 100% functional
    astar_resp = api_client.post(
        "/api/v1/routes/optimal",
        json={
            "origin_lat": 31.2260,
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
            "objective": "traffic_aware",
        },
    )
    assert astar_resp.status_code == 200
    astar_data = astar_resp.json()
    assert astar_data["success"] is True
    assert "A*" in astar_data["algorithm_name"]
    assert astar_data["path_distance_km"] > 0
    assert len(astar_data["coordinates"]) > 1

    # 3. Verify comparison endpoint also remains 100% functional
    comp_resp = api_client.post(
        "/api/v1/routes/compare",
        json={
            "origin_lat": 31.2260,
            "origin_lng": 75.7790,
            "dest_lat": 31.2223,
            "dest_lng": 75.7672,
            "objective": "traffic_aware",
        },
    )
    assert comp_resp.status_code == 200
    comp_data = comp_resp.json()
    assert "A_Star" in comp_data["results"]
    assert "BFS" in comp_data["results"]
    assert "DFS" in comp_data["results"]
    assert "Greedy_Best_First" in comp_data["results"]
