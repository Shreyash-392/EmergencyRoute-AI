import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.config import settings

client = TestClient(app)


def test_traffic_telemetry_status_does_not_leak_keys():
    """Verify that telemetry status returns safely and never exposes raw secrets."""
    resp = client.get("/api/v1/traffic/telemetry-status")
    assert resp.status_code == 200
    data = resp.json()
    assert "configured" in data
    assert "provider" in data
    assert "proxy_mode" in data
    # Ensure raw secret key is never leaked
    assert "api_key" not in data
    assert "TOMTOM_API_KEY" not in data
    assert "key" not in data


def test_traffic_tile_proxy_safe_fallback():
    """Verify that tile proxy returns 200 with image/png even when key is None."""
    orig_key = settings.TOMTOM_API_KEY
    try:
        settings.TOMTOM_API_KEY = None
        resp = client.get("/api/v1/traffic/tiles/flow/13/5821/3296.png")
        assert resp.status_code == 200
        assert resp.headers["content-type"] == "image/png"
        assert len(resp.content) > 0
    finally:
        settings.TOMTOM_API_KEY = orig_key


def test_traffic_search_without_key():
    """Verify that place search returns empty list without error when unconfigured."""
    orig_key = settings.TOMTOM_API_KEY
    try:
        settings.TOMTOM_API_KEY = None
        resp = client.get("/api/v1/traffic/search?query=Hospital")
        assert resp.status_code == 200
        assert resp.json() == []
    finally:
        settings.TOMTOM_API_KEY = orig_key


def test_set_key_rejects_empty():
    """Verify that submitting an empty key is rejected with HTTP 400."""
    resp = client.post("/api/v1/traffic/set-key", json={"api_key": "   "})
    assert resp.status_code == 400

