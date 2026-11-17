import json
import logging
from typing import Any, Dict, Optional, Tuple
import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OSRMClientError(Exception):
    """Base exception for OSRM client issues."""
    def __init__(self, code: str, message: str, status_code: int = 400):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code


class OSRMClient:
    """
    Dedicated client for querying the Open Source Routing Machine (OSRM) HTTP API.
    Uses the driving profile and extracts GeoJSON geometry, steps, and alternatives.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        timeout: Optional[float] = None,
        user_agent: Optional[str] = None,
    ):
        self.base_url = (base_url or getattr(settings, "OSRM_BASE_URL", "https://router.project-osrm.org")).rstrip("/")
        self.timeout = timeout or getattr(settings, "OSRM_REQUEST_TIMEOUT_SECONDS", 8.0)
        self.user_agent = user_agent or getattr(
            settings, "OSRM_USER_AGENT", "EmergencyRoute-AI/1.0 (academic SIH testing)"
        )

    def validate_coordinates(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> None:
        """
        Validates latitude and longitude ranges.
        Raises OSRMClientError if any coordinate is invalid.
        """
        for name, lat in [("origin_lat", origin_lat), ("dest_lat", dest_lat)]:
            if lat is None or not isinstance(lat, (int, float)):
                raise OSRMClientError(
                    code="InvalidCoordinates",
                    message=f"Missing or non-numeric {name}.",
                    status_code=400,
                )
            if not (-90.0 <= lat <= 90.0):
                raise OSRMClientError(
                    code="InvalidCoordinates",
                    message=f"Latitude {lat} out of range [-90, 90] for {name}.",
                    status_code=400,
                )

        for name, lng in [("origin_lng", origin_lng), ("dest_lng", dest_lng)]:
            if lng is None or not isinstance(lng, (int, float)):
                raise OSRMClientError(
                    code="InvalidCoordinates",
                    message=f"Missing or non-numeric {name}.",
                    status_code=400,
                )
            if not (-180.0 <= lng <= 180.0):
                raise OSRMClientError(
                    code="InvalidCoordinates",
                    message=f"Longitude {lng} out of range [-180, 180] for {name}.",
                    status_code=400,
                )

    def get_route_raw(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        overview: str = "full",
        geometries: str = "geojson",
        steps: bool = True,
        alternatives: bool = True,
    ) -> Dict[str, Any]:
        """
        Executes HTTP GET against OSRM Route API:
        GET /route/v1/driving/{origin_lng},{origin_lat};{dest_lng},{dest_lat}
        """
        self.validate_coordinates(origin_lat, origin_lng, dest_lat, dest_lng)

        # OSRM coordinate syntax: longitude,latitude
        coords_str = f"{origin_lng:.6f},{origin_lat:.6f};{dest_lng:.6f},{dest_lat:.6f}"
        url = f"{self.base_url}/route/v1/driving/{coords_str}"

        params = {
            "overview": overview,
            "geometries": geometries,
            "steps": "true" if steps else "false",
            "alternatives": "true" if alternatives else "false",
        }

        headers = {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

        logger.info(f"Querying OSRM Route API: {url} params={params}")

        try:
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(url, params=params, headers=headers)
                response.raise_for_status()
                data = response.json()
                return data

        except httpx.TimeoutException as e:
            logger.warning(f"OSRM request timed out after {self.timeout}s: {e}")
            raise OSRMClientError(
                code="Timeout",
                message=f"OSRM server timed out after {self.timeout} seconds.",
                status_code=504,
            ) from e

        except httpx.HTTPStatusError as e:
            status = e.response.status_code
            text = e.response.text[:200]
            logger.warning(f"OSRM HTTP error {status}: {text}")
            raise OSRMClientError(
                code="HTTPError",
                message=f"OSRM server returned HTTP {status}: {text}",
                status_code=502 if status >= 500 else 400,
            ) from e

        except httpx.RequestError as e:
            logger.warning(f"OSRM network request failed: {e}")
            raise OSRMClientError(
                code="NetworkError",
                message=f"Failed to connect to OSRM server: {e}",
                status_code=503,
            ) from e

        except json.JSONDecodeError as e:
            logger.error(f"OSRM invalid JSON response: {e}")
            raise OSRMClientError(
                code="InvalidJSON",
                message="OSRM server returned invalid JSON response.",
                status_code=502,
            ) from e

