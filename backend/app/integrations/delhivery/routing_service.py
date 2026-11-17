import logging
from typing import Optional
from app.integrations.delhivery.client import DelhiveryClient, DelhiveryError
from app.integrations.delhivery.schemas import DelhiveryRouteResponse, DelhiveryRouteSegment
from app.services.graph_service import GraphService

logger = logging.getLogger(__name__)


class DelhiveryRoutingService:
    """
    Routing service integrating external Delhivery routing API with seamless fallback
    to local directed OSMnx graph routing when credentials are not configured or offline.
    """

    def __init__(self, client: Optional[DelhiveryClient] = None, graph_service: Optional[GraphService] = None):
        self.client = client or DelhiveryClient()
        self._graph_service = graph_service

    @property
    def graph_service(self) -> GraphService:
        if self._graph_service is None:
            self._graph_service = GraphService()
        return self._graph_service

    def get_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> DelhiveryRouteResponse:
        """
        Obtains routing details between origin and destination coordinates.
        Uses Delhivery routing API if configured; otherwise uses local OSM directed graph reference.
        """
        # Try live Delhivery API
        if self.client.is_configured:
            try:
                response = self.client.request(
                    method="GET",
                    endpoint="/routing/directions",
                    params={
                        "origin": f"{origin_lat},{origin_lng}",
                        "destination": f"{dest_lat},{dest_lng}",
                        "mode": "driving"
                    }
                )
                data = response.get("data", response)
                dist_m = float(data.get("distance_meters", data.get("distance", 0.0)))
                dur_s = float(data.get("duration_seconds", data.get("duration", 0.0)))
                
                return DelhiveryRouteResponse(
                    success=True,
                    distance_meters=dist_m,
                    duration_seconds=dur_s,
                    distance_km=round(dist_m / 1000.0, 3),
                    duration_minutes=round(dur_s / 60.0, 2),
                    traffic_delay_seconds=float(data.get("traffic_delay", 0.0)),
                    polyline_geometry=data.get("geometry", None),
                    coordinates=data.get("coordinates", None),
                    provider="delhivery",
                    is_fallback=False
                )
            except DelhiveryError as e:
                logger.warning(f"Delhivery routing call failed ({e}). Falling back to local road graph routing.")

        # Fallback to local OSM road graph
        logger.info("Using local OSM directed graph routing as reference.")
        ref_route = self.graph_service.calculate_reference_route(
            origin_lat=origin_lat,
            origin_lng=origin_lng,
            dest_lat=dest_lat,
            dest_lng=dest_lng,
            weight="travel_time"
        )

        if not ref_route.get("success", False):
            return DelhiveryRouteResponse(
                success=False,
                distance_meters=0.0,
                duration_seconds=0.0,
                distance_km=0.0,
                duration_minutes=0.0,
                provider="local_osm_graph",
                is_fallback=True,
                message=ref_route.get("error", "No directed path found.")
            )

        segments = [
            DelhiveryRouteSegment(
                instruction=f"Proceed along {s['name']} ({s['highway']})",
                distance_meters=s["length_meters"],
                duration_seconds=s["travel_time_seconds"],
                road_name=s["name"]
            )
            for s in ref_route.get("segments", [])
        ]

        return DelhiveryRouteResponse(
            success=True,
            distance_meters=ref_route["total_distance_meters"],
            duration_seconds=ref_route["total_travel_time_seconds"],
            distance_km=ref_route["total_distance_km"],
            duration_minutes=ref_route["total_travel_time_minutes"],
            traffic_delay_seconds=0.0,
            coordinates=ref_route.get("route_coordinates"),
            segments=segments,
            provider="local_osm_graph",
            is_fallback=True,
            message="Computed via local OSM directed graph (NetworkX Dijkstra baseline)."
        )

