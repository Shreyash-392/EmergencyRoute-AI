import logging
from typing import Any, Dict, List, Optional
from app.integrations.osrm.client import OSRMClient, OSRMClientError
from app.integrations.osrm.schemas import (
    OSRMLeg,
    OSRMRoute,
    OSRMRouteResponse,
    OSRMStep,
)

logger = logging.getLogger(__name__)


def format_step_instruction(step: Dict[str, Any]) -> str:
    """
    Synthesizes human-readable turn-by-turn instruction from OSRM maneuver and street name.
    """
    name = (step.get("name") or "").strip()
    maneuver = step.get("maneuver", {})
    m_type = maneuver.get("type", "")
    modifier = maneuver.get("modifier", "")

    street = f" onto {name}" if name else ""

    if m_type == "depart":
        if modifier:
            return f"Depart heading {modifier}{street}"
        return f"Depart{street}"
    elif m_type == "arrive":
        return "Arrive at destination"
    elif m_type == "turn":
        if modifier:
            return f"Turn {modifier}{street}"
        return f"Turn{street}"
    elif m_type == "new name":
        return f"Continue{street}"
    elif m_type == "end of road":
        if modifier:
            return f"At end of road, turn {modifier}{street}"
        return f"At end of road, continue{street}"
    elif m_type == "fork":
        if modifier:
            return f"Keep {modifier} at the fork{street}"
        return f"Take the fork{street}"
    elif m_type == "roundabout" or m_type == "rotary":
        exit_num = maneuver.get("exit")
        exit_str = f", take exit {exit_num}" if exit_num else ""
        return f"Enter roundabout{exit_str}{street}"
    elif m_type == "continue":
        return f"Continue{street}"
    else:
        action = f"{m_type} {modifier}".strip()
        return f"{action.capitalize()}{street}" if action else f"Continue{street}"


class OSRMService:
    """
    Service layer for parsing and transforming OSRM responses into structured
    EmergencyRoute AI navigation models.
    """

    def __init__(self, client: Optional[OSRMClient] = None):
        self.client = client or OSRMClient()

    def _parse_single_route(self, raw_route: Dict[str, Any]) -> OSRMRoute:
        dist_m = float(raw_route.get("distance", 0.0))
        dur_s = float(raw_route.get("duration", 0.0))
        dist_km = round(dist_m / 1000.0, 3)
        dur_min = round(dur_s / 60.0, 2)

        geometry = raw_route.get("geometry", {})
        # GeoJSON is [lng, lat]
        geojson_coords = geometry.get("coordinates", [])
        # Leaflet polyline uses [lat, lng]
        leaflet_coords = [[pt[1], pt[0]] for pt in geojson_coords if len(pt) >= 2]

        legs: List[OSRMLeg] = []
        turn_by_turn: List[str] = []

        for raw_leg in raw_route.get("legs", []):
            leg_dist = float(raw_leg.get("distance", 0.0))
            leg_dur = float(raw_leg.get("duration", 0.0))
            summary = raw_leg.get("summary", "")

            steps: List[OSRMStep] = []
            for raw_step in raw_leg.get("steps", []):
                s_dist = float(raw_step.get("distance", 0.0))
                s_dur = float(raw_step.get("duration", 0.0))
                s_name = raw_step.get("name", "")
                s_mode = raw_step.get("mode", "driving")
                s_maneuver = raw_step.get("maneuver")

                instruction = format_step_instruction(raw_step)
                if instruction:
                    turn_by_turn.append(instruction)

                steps.append(
                    OSRMStep(
                        name=s_name,
                        distance_meters=round(s_dist, 1),
                        duration_seconds=round(s_dur, 1),
                        mode=s_mode,
                        maneuver=s_maneuver,
                        instruction=instruction,
                    )
                )

            legs.append(
                OSRMLeg(
                    distance_meters=round(leg_dist, 1),
                    duration_seconds=round(leg_dur, 1),
                    summary=summary,
                    steps=steps,
                )
            )

        return OSRMRoute(
            distance_meters=round(dist_m, 1),
            duration_seconds=round(dur_s, 1),
            distance_km=dist_km,
            duration_minutes=dur_min,
            geometry=geometry,
            coordinates=leaflet_coords,
            legs=legs,
            turn_by_turn=turn_by_turn,
        )

    def get_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
    ) -> OSRMRouteResponse:
        """
        Coordinates in decimal degrees.
        Fetches route from OSRM and returns structured OSRMRouteResponse.
        """
        origin_dict = {"lat": origin_lat, "lng": origin_lng}
        dest_dict = {"lat": dest_lat, "lng": dest_lng}

        try:
            raw_data = self.client.get_route_raw(
                origin_lat=origin_lat,
                origin_lng=origin_lng,
                dest_lat=dest_lat,
                dest_lng=dest_lng,
                overview="full",
                geometries="geojson",
                steps=True,
                alternatives=True,
            )
        except OSRMClientError as e:
            return OSRMRouteResponse(
                success=False,
                code=e.code,
                message=e.message,
                origin=origin_dict,
                destination=dest_dict,
            )
        except Exception as e:
            logger.error(f"Unexpected error in OSRMService: {e}")
            return OSRMRouteResponse(
                success=False,
                code="UnexpectedError",
                message=f"Internal OSRM processing error: {e}",
                origin=origin_dict,
                destination=dest_dict,
            )

        # Inspect OSRM response code
        code = raw_data.get("code", "")
        if code != "Ok":
            msg = raw_data.get("message", f"OSRM error code: {code}")
            return OSRMRouteResponse(
                success=False,
                code=code if code else "NoRoute",
                message=msg,
                origin=origin_dict,
                destination=dest_dict,
            )

        routes_data = raw_data.get("routes", [])
        if not routes_data:
            return OSRMRouteResponse(
                success=False,
                code="NoRoute",
                message="No route found between the specified coordinates.",
                origin=origin_dict,
                destination=dest_dict,
            )

        primary_route = self._parse_single_route(routes_data[0])
        alternatives: List[OSRMRoute] = [
            self._parse_single_route(r) for r in routes_data[1:]
        ]

        return OSRMRouteResponse(
            success=True,
            code="Ok",
            message="OSRM external route generated successfully.",
            origin=origin_dict,
            destination=dest_dict,
            distance_km=primary_route.distance_km,
            duration_minutes=primary_route.duration_minutes,
            is_live_traffic=False,
            disclaimer=(
                "Routing engine estimate based on standard road speeds; "
                "not real-time live traffic."
            ),
            route=primary_route,
            alternatives_count=len(alternatives),
            alternatives=alternatives,
        )

