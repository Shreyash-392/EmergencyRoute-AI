from contextlib import asynccontextmanager
import logging
from typing import Any, Dict, List, Optional
import urllib.parse
import httpx
from fastapi import FastAPI, HTTPException, Query, Response, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.algorithms.algorithm_metrics import (
    AlgorithmComparisonSummary,
    AlgorithmResult,
    RoutingObjective,
)
from app.core.config import settings
from app.core.graph_loader import get_cached_graph, load_graph_from_graphml
from app.core.websocket_manager import websocket_manager
from app.db.database import init_db
from app.demo.demo_service import JudgeDemoService
from app.dispatch.dispatch_models import (
    CreateIncidentRequest,
    DispatchExecutionRequest,
    DispatchExecutionResponse,
    EmergencyIncident,
    Vehicle,
    VehicleRankingResponse,
)
from app.dispatch.dispatch_service import DispatchService
from app.integrations.delhivery.client import DelhiveryClient
from app.integrations.delhivery.geocoding_service import DelhiveryGeocodingService
from app.integrations.delhivery.maps_service import DelhiveryMapsService
from app.integrations.delhivery.routing_service import DelhiveryRoutingService
from app.integrations.delhivery.schemas import (
    DelhiveryRouteResponse,
    GeocodeSearchResponse,
    MapTileConfig,
)
from app.integrations.osrm.schemas import OSRMRouteResponse
from app.integrations.osrm.service import OSRMService
from app.routing.rerouting_service import RerouteResponse, ReroutingService
from app.routing.routing_service import RoutingService
from app.schemas.route_schemas import (
    CompareRoutesRequest,
    ReferenceRouteRequest,
    RerouteRequest,
    RoadClosureRequest,
    RouteRequest,
    TrafficSimulateRequest,
)
from app.services.graph_service import GraphService
from app.services.validation_service import validate_road_network
from app.traffic.traffic_service import TrafficService

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("emergency_route_api")

# Services Singletons
delhivery_client = DelhiveryClient()
geocoding_service = DelhiveryGeocodingService(client=delhivery_client)
maps_service = DelhiveryMapsService(client=delhivery_client)
delhivery_routing = DelhiveryRoutingService(client=delhivery_client)
osrm_service = OSRMService()

traffic_service: Optional[TrafficService] = None
routing_service: Optional[RoutingService] = None
rerouting_service: Optional[ReroutingService] = None
dispatch_service: Optional[DispatchService] = None
demo_service: Optional[JudgeDemoService] = None


def get_osrm_service() -> OSRMService:
    return osrm_service


def get_routing_service() -> RoutingService:
    global routing_service, traffic_service, rerouting_service, dispatch_service, demo_service
    if routing_service is None:
        graph = get_cached_graph()
        if graph is None:
            graph = load_graph_from_graphml(settings.GRAPHML_PATH)
        traffic_service = TrafficService(graph=graph)
        routing_service = RoutingService(graph=graph, traffic_service=traffic_service)
        rerouting_service = ReroutingService(routing_service=routing_service)
        dispatch_service = DispatchService(routing_service=routing_service)
        demo_service = JudgeDemoService(
            routing_service=routing_service,
            traffic_service=traffic_service,
            rerouting_service=rerouting_service
        )
    return routing_service


def get_traffic_service() -> TrafficService:
    get_routing_service()
    assert traffic_service is not None
    return traffic_service


def get_rerouting_service() -> ReroutingService:
    get_routing_service()
    assert rerouting_service is not None
    return rerouting_service


def get_dispatch_service() -> DispatchService:
    get_routing_service()
    assert dispatch_service is not None
    return dispatch_service


def get_demo_service() -> JudgeDemoService:
    get_routing_service()
    assert demo_service is not None
    return demo_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing EmergencyRoute AI API Server...")
    try:
        init_db()
        if settings.GRAPHML_PATH.exists():
            load_graph_from_graphml(settings.GRAPHML_PATH)
            get_routing_service()
            logger.info("Authoritative road network graph loaded successfully.")
    except Exception as e:
        logger.warning(f"Startup initialization notice: {e}")
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="EmergencyRoute AI - Professional Emergency Route Planning Platform (SIH)",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan
)

# Configurable CORS for production deployment
cors_origins = [o.strip() for o in settings.CORS_ORIGINS.split(",") if o.strip()]
is_wildcard = "*" in cors_origins or not cors_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins if cors_origins else ["*"],
    allow_credentials=not is_wildcard,
    allow_methods=["*"],
    allow_headers=["*"],
)

if settings.MAPS_OUTPUT_DIR.exists():
    app.mount("/maps", StaticFiles(directory=str(settings.MAPS_OUTPUT_DIR)), name="maps")


# -------------------------------------------------------------
# WebSockets & Real-Time Polling Fallback
# -------------------------------------------------------------

@app.websocket("/ws/events")
async def websocket_endpoint(websocket: WebSocket):
    await websocket_manager.connect(websocket)
    try:
        while True:
            # Keep-alive heartbeat listener
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
    except Exception as e:
        logger.warning(f"WebSocket session error: {e}")
        websocket_manager.disconnect(websocket)


@app.get("/api/v1/events/poll")
def poll_recent_events(limit: int = Query(20, ge=1, le=100)) -> List[Dict[str, Any]]:
    """Polling fallback for environments where WebSocket connections are blocked."""
    return websocket_manager.get_recent_events(limit=limit)


# -------------------------------------------------------------
# System & Diagnostic Endpoints
# -------------------------------------------------------------

@app.get("/api/v1/health")
def health_check() -> Dict[str, Any]:
    cached_graph = get_cached_graph()
    if cached_graph is None:
        try:
            rs = get_routing_service()
            cached_graph = rs.graph
        except Exception:
            pass
    has_graph = cached_graph is not None

    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "phase": 3,
        "city": settings.CITY,
        "graph_loaded": has_graph,
        "graph_nodes": len(cached_graph.nodes) if has_graph else 0,
        "graph_edges": len(cached_graph.edges) if has_graph else 0,
        "delhivery_configured": delhivery_client.is_configured,
        "traffic_provider_mode": settings.TRAFFIC_PROVIDER_MODE,
        "websocket_active_clients": len(websocket_manager.active_connections),
        "algorithms": ["BFS", "DFS", "Greedy_Best_First", "A_Star"],
    }


@app.get("/api/v1/map/config", response_model=MapTileConfig)
def get_map_config() -> MapTileConfig:
    return maps_service.get_tile_configuration()


@app.get("/api/v1/map/locations/search", response_model=GeocodeSearchResponse)
def search_locations(
    q: str = Query(..., min_length=1, description="Address or landmark query"),
    limit: int = Query(5, ge=1, le=20)
) -> GeocodeSearchResponse:
    return geocoding_service.search_locations(query=q, limit=limit)


@app.get("/api/v1/roads/statistics")
def get_road_statistics() -> Dict[str, Any]:
    try:
        rs = get_routing_service()
        return validate_road_network(rs.graph)
    except Exception as e:
        logger.error(f"Error computing road network statistics: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# -------------------------------------------------------------
# Core Algorithm & Routing Endpoints
# -------------------------------------------------------------

def resolve_nodes(rs: RoutingService, req: Any) -> tuple[int, int]:
    src = req.source_node
    tgt = req.target_node

    if src is None:
        if req.origin_lat is not None and req.origin_lng is not None:
            src = rs.find_nearest_node(req.origin_lat, req.origin_lng)
        else:
            raise HTTPException(status_code=400, detail="Must provide source_node or origin_lat/origin_lng.")

    if tgt is None:
        if req.dest_lat is not None and req.dest_lng is not None:
            tgt = rs.find_nearest_node(req.dest_lat, req.dest_lng)
        else:
            raise HTTPException(status_code=400, detail="Must provide target_node or dest_lat/dest_lng.")

    return int(src), int(tgt)


@app.post("/api/v1/routes/optimal", response_model=AlgorithmResult)
def calculate_optimal_route(req: RouteRequest) -> AlgorithmResult:
    rs = get_routing_service()
    src, tgt = resolve_nodes(rs, req)
    
    result = rs.run_algorithm(
        algorithm_name="astar",
        source=src,
        target=tgt,
        objective=req.objective,
        scenario_id=req.scenario_id
    )
    if not result.success:
        raise HTTPException(status_code=404, detail=result.error_message or "No route found.")
    return result


@app.post("/api/v1/routes/compare", response_model=AlgorithmComparisonSummary)
def compare_routes(req: CompareRoutesRequest) -> AlgorithmComparisonSummary:
    rs = get_routing_service()
    src, tgt = resolve_nodes(rs, req)
    
    return rs.compare_all_algorithms(
        source=src,
        target=tgt,
        objective=req.objective,
        scenario_id=req.scenario_id
    )


@app.post("/api/v1/routes/reroute", response_model=RerouteResponse)
async def dynamic_reroute(req: RerouteRequest) -> RerouteResponse:
    reroute_svc = get_rerouting_service()
    resp = reroute_svc.process_dynamic_reroute(
        route_id=req.route_id,
        current_route=req.current_route,
        new_closures=req.new_closures,
        new_traffic_observations=req.new_traffic_observations,
        min_improvement_threshold_pct=req.min_improvement_threshold_pct,
        force_recalculate=req.force_recalculate
    )
    if resp.reroute_triggered:
        await websocket_manager.broadcast("route_rerouted", {
            "route_id": req.route_id,
            "decision": resp.decision,
            "reason": resp.reason,
            "new_travel_time_minutes": resp.active_route.estimated_travel_time_minutes
        })
    return resp


@app.post("/api/v1/routes/reference", response_model=DelhiveryRouteResponse)
def get_commercial_reference_route(req: ReferenceRouteRequest) -> DelhiveryRouteResponse:
    return delhivery_routing.get_route(
        origin_lat=req.origin_lat,
        origin_lng=req.origin_lng,
        dest_lat=req.dest_lat,
        dest_lng=req.dest_lng
    )


@app.get("/api/v1/routes/reference", response_model=DelhiveryRouteResponse)
def get_reference_route_get(
    origin_lat: float = Query(...),
    origin_lng: float = Query(...),
    dest_lat: float = Query(...),
    dest_lng: float = Query(...),
) -> DelhiveryRouteResponse:
    return delhivery_routing.get_route(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng
    )


@app.get("/api/v1/routes/osrm", response_model=OSRMRouteResponse)
def get_osrm_route(
    origin_lat: float = Query(..., ge=-90.0, le=90.0, description="Origin latitude [-90, 90]"),
    origin_lng: float = Query(..., ge=-180.0, le=180.0, description="Origin longitude [-180, 180]"),
    dest_lat: float = Query(..., ge=-90.0, le=90.0, description="Destination latitude [-90, 90]"),
    dest_lng: float = Query(..., ge=-180.0, le=180.0, description="Destination longitude [-180, 180]"),
) -> OSRMRouteResponse:
    """
    Computes an external route using the Open Source Routing Machine (OSRM) Route API.
    Provides distance in metres/km, duration in seconds/minutes, GeoJSON geometry,
    and turn-by-turn instructions.
    """
    svc = get_osrm_service()
    res = svc.get_route(
        origin_lat=origin_lat,
        origin_lng=origin_lng,
        dest_lat=dest_lat,
        dest_lng=dest_lng,
    )

    if not res.success:
        if res.code == "InvalidCoordinates":
            raise HTTPException(status_code=400, detail=res.message)
        elif res.code == "NoRoute":
            raise HTTPException(status_code=404, detail=res.message)
        elif res.code == "Timeout":
            raise HTTPException(status_code=504, detail=res.message)
        elif res.code in ("HTTPError", "NetworkError", "InvalidJSON"):
            raise HTTPException(status_code=502, detail=res.message)
        else:
            raise HTTPException(status_code=500, detail=res.message)

    return res


@app.post("/api/v1/routes/osrm", response_model=OSRMRouteResponse)
def get_osrm_route_post(req: ReferenceRouteRequest) -> OSRMRouteResponse:
    """POST alias for OSRM Route retrieval."""
    return get_osrm_route(
        origin_lat=req.origin_lat,
        origin_lng=req.origin_lng,
        dest_lat=req.dest_lat,
        dest_lng=req.dest_lng,
    )


# -------------------------------------------------------------
# Traffic Intelligence Endpoints
# -------------------------------------------------------------

@app.get("/api/v1/traffic")
def get_active_traffic(scenario: Optional[str] = Query(None)) -> Dict[str, Any]:
    ts = get_traffic_service()
    scen = scenario or ts.active_scenario_id
    scenarios = ts.simulator.get_available_scenarios()
    active_scen = next((s for s in scenarios if s.scenario_id == scen), scenarios[0])
    closures = ts.closure_manager.list_closures()
    snapshot = ts.get_traffic_snapshot()

    return {
        "active_scenario": active_scen.model_dump(),
        "available_scenarios": [s.model_dump() for s in scenarios],
        "closures_count": len(closures),
        "closures": [c.model_dump() for c in closures],
        "total_edges_with_traffic": len(snapshot),
        "traffic_provider_mode": settings.TRAFFIC_PROVIDER_MODE,
        "is_live_data": False,
        "data_source": "synthetic_simulation",
    }


@app.get("/api/v1/traffic/status")
def get_traffic_status_alias(scenario: Optional[str] = Query("morning_peak")) -> Dict[str, Any]:
    return get_active_traffic(scenario=scenario)


@app.post("/api/v1/traffic/simulate")
async def simulate_traffic_scenario(req: TrafficSimulateRequest) -> Dict[str, Any]:
    ts = get_traffic_service()
    snapshot = ts.refresh_traffic_snapshot(scenario_id=req.scenario_id)
    await websocket_manager.broadcast("traffic_update", {
        "scenario_id": req.scenario_id,
        "edges_updated": len(snapshot)
    })
    return {
        "status": "success",
        "scenario_id": req.scenario_id,
        "edges_updated": len(snapshot),
        "closures_active": len(ts.closure_manager.get_closed_edges()),
        "message": f"Simulated traffic scenario '{req.scenario_id}' activated."
    }


@app.post("/api/v1/traffic/closures")
async def manage_road_closures(req: RoadClosureRequest) -> Dict[str, Any]:
    ts = get_traffic_service()
    if req.action == "add":
        if req.u is None or req.v is None:
            raise HTTPException(status_code=400, detail="Must provide node IDs (u, v) to add closure.")
        closure_id = req.closure_id or f"closure_{req.u}_{req.v}_{req.key}"
        added = ts.closure_manager.add_closure(
            closure_id=closure_id,
            u=req.u,
            v=req.v,
            key=req.key,
            reason=req.reason,
            severity=req.severity
        )
        await websocket_manager.broadcast("road_closure", {"action": "add", "closure": added.model_dump()})
        return {"status": "success", "action": "add", "closure": added.model_dump()}

    elif req.action == "remove":
        if not req.closure_id:
            raise HTTPException(status_code=400, detail="Must provide closure_id to remove.")
        removed = ts.closure_manager.remove_closure(req.closure_id)
        if not removed:
            raise HTTPException(status_code=404, detail=f"Closure '{req.closure_id}' not found.")
        await websocket_manager.broadcast("road_closure", {"action": "remove", "closure_id": req.closure_id})
        return {"status": "success", "action": "remove", "closure_id": req.closure_id}

    elif req.action == "clear":
        ts.closure_manager.clear_all()
        await websocket_manager.broadcast("road_closure", {"action": "clear"})
        return {"status": "success", "action": "clear", "message": "All active closures cleared."}

    else:
        raise HTTPException(status_code=400, detail="Invalid action. Must be 'add', 'remove', or 'clear'.")


@app.get("/api/v1/traffic/providers")
def get_traffic_providers() -> List[Dict[str, Any]]:
    return [
        {
            "provider_id": "delhivery_telematics",
            "name": "Delhivery Location Intelligence",
            "status": "configured" if delhivery_client.is_configured else "fallback_mode",
            "resolution": "corridor_eta",
            "is_live": delhivery_client.is_configured,
            "description": "Logistics fleet telematics ETA adjustments and commercial routing reference."
        },
        {
            "provider_id": "synthetic_simulation",
            "name": "Deterministic Synthetic Simulator",
            "status": "active",
            "resolution": "edge_level",
            "is_live": False,
            "description": "Deterministic edge-level speed and congestion simulation calibrated on OSM classifications."
        },
        {
            "provider_id": "mock_sensor",
            "name": "Mock Test Ingestion Provider",
            "status": "standby",
            "resolution": "edge_level",
            "is_live": False,
            "description": "Controlled unit testing and dynamic incident injection harness."
        }
    ]


@app.get("/api/v1/algorithms/metrics")
def get_algorithms_metrics() -> Dict[str, Any]:
    return {
        "algorithms": {
            "BFS": {
                "name": "Breadth-First Search",
                "time_complexity": "O(V + E)",
                "space_complexity": "O(V)",
                "optimality": "Hop-count optimal only (unweighted)",
                "frontier_type": "Queue (FIFO)",
                "heuristic": "None",
            },
            "DFS": {
                "name": "Depth-First Search",
                "time_complexity": "O(V + E)",
                "space_complexity": "O(V)",
                "optimality": "Non-optimal",
                "frontier_type": "Stack (LIFO)",
                "heuristic": "None",
            },
            "Greedy_Best_First": {
                "name": "Greedy Best-First Search",
                "time_complexity": "O(b^m)",
                "space_complexity": "O(V)",
                "optimality": "Non-optimal (heuristic-only)",
                "frontier_type": "Priority Queue (heapq)",
                "heuristic": "f(n) = h(n)",
            },
            "A_Star": {
                "name": "A* (A-Star) Search",
                "time_complexity": "O(E + V log V)",
                "space_complexity": "O(V)",
                "optimality": "Provably optimal under admissible heuristic",
                "frontier_type": "Priority Queue (heapq)",
                "heuristic": "f(n) = g(n) + h(n)",
            }
        },
        "guarantees": {
            "admissibility_verified": True,
            "lower_bound_heuristic": "Haversine / max_network_speed ensures h(n) <= h*(n)",
            "multigraph_parallel_edge_preservation": True,
            "one_way_compliance": True
        }
    }


# -------------------------------------------------------------
# Phase 3 Emergency Dispatch Simulation Endpoints
# -------------------------------------------------------------

@app.get("/api/v1/dispatch/vehicles", response_model=List[Vehicle])
def list_vehicles() -> List[Vehicle]:
    ds = get_dispatch_service()
    return ds.get_all_vehicles()


@app.get("/api/v1/dispatch/incidents", response_model=List[EmergencyIncident])
def list_incidents() -> List[EmergencyIncident]:
    ds = get_dispatch_service()
    return ds.get_all_incidents()


@app.post("/api/v1/dispatch/incidents", response_model=EmergencyIncident)
async def create_incident(req: CreateIncidentRequest) -> EmergencyIncident:
    ds = get_dispatch_service()
    inc = ds.create_incident(req)
    await websocket_manager.broadcast("incident_created", inc.model_dump())
    return inc


@app.post("/api/v1/dispatch/rank", response_model=VehicleRankingResponse)
def rank_vehicles(incident_id: str = Query(...), scenario_id: str = Query("morning_peak")) -> VehicleRankingResponse:
    ds = get_dispatch_service()
    try:
        return ds.rank_vehicles_for_incident(incident_id=incident_id, scenario_id=scenario_id)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.post("/api/v1/dispatch/assign", response_model=DispatchExecutionResponse)
async def assign_vehicle_to_incident(req: DispatchExecutionRequest) -> DispatchExecutionResponse:
    ds = get_dispatch_service()
    try:
        resp = ds.execute_dispatch(req)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await websocket_manager.broadcast("vehicle_dispatched", {
        "incident_id": req.incident_id,
        "vehicle_id": req.vehicle_id,
        "eta_minutes": resp.estimated_eta_minutes
    })
    return resp


# -------------------------------------------------------------
# Phase 3 Judge Demonstration Mode Endpoints
# -------------------------------------------------------------

@app.get("/api/v1/demo/baseline")
def get_judge_demo_baseline() -> Dict[str, Any]:
    demo = get_demo_service()
    return demo.get_initial_demo_state()


@app.post("/api/v1/demo/simulate-incident")
async def trigger_demo_incident() -> Dict[str, Any]:
    demo = get_demo_service()
    res = demo.simulate_incident_and_reroute()
    await websocket_manager.broadcast("road_closure", res.get("blocked_segment"))
    await websocket_manager.broadcast("route_rerouted", res.get("reroute_result"))
    return res


@app.post("/api/v1/demo/reset")
async def reset_demo_mode() -> Dict[str, Any]:
    demo = get_demo_service()
    res = demo.reset_demonstration()
    await websocket_manager.broadcast("road_closure", {"action": "clear"})
    return res


# -------------------------------------------------------------
# Secure Server-Side TomTom Traffic & Mapping Reverse Proxy
# Protects credentials from client-side inspection, scraping or fraud.
# -------------------------------------------------------------

EMPTY_TILE_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000000020001486166a00000000049454e44ae426082"
)


class KeyConfigRequest(BaseModel):
    api_key: str


@app.get("/api/v1/traffic/telemetry-status")
def get_traffic_telemetry_status() -> Dict[str, Any]:
    """Returns telemetry provider status without ever exposing secret keys."""
    configured = bool(settings.TOMTOM_API_KEY and settings.TOMTOM_API_KEY.strip())
    return {
        "configured": configured,
        "provider": "TomTom Telemetry & Live Traffic",
        "proxy_mode": "secure_server_side",
        "description": "API credentials stored securely on server; direct client exposure disabled."
    }


@app.api_route("/api/v1/traffic/tiles/{layer}/{z}/{x}/{y}.png", methods=["GET", "HEAD"])
async def proxy_traffic_tile(layer: str, z: int, x: int, y: int):
    """
    Reverse proxies raster map & traffic tiles directly from TomTom servers.
    Zero secret keys are leaked to the client browser.
    """
    key = settings.TOMTOM_API_KEY
    if not key or not key.strip():
        return Response(content=EMPTY_TILE_PNG, media_type="image/png")

    layer_url_map = {
        "flow": f"https://api.tomtom.com/traffic/map/4/tile/flow/relative0/{z}/{x}/{y}.png?key={key}",
        "incidents": f"https://api.tomtom.com/traffic/map/4/tile/incidents/s0/{z}/{x}/{y}.png?key={key}",
        "light": f"https://api.tomtom.com/map/1/tile/basic/main/{z}/{x}/{y}.png?key={key}",
        "night": f"https://api.tomtom.com/map/1/tile/basic/night/{z}/{x}/{y}.png?key={key}",
        "sat": f"https://api.tomtom.com/map/1/tile/sat/main/{z}/{x}/{y}.jpg?key={key}",
    }

    upstream_url = layer_url_map.get(layer)
    if not upstream_url:
        return Response(content=EMPTY_TILE_PNG, media_type="image/png")

    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(upstream_url)
            if resp.status_code == 200:
                media_type = resp.headers.get("content-type", "image/png")
                return Response(
                    content=resp.content,
                    media_type=media_type,
                    headers={"Cache-Control": "public, max-age=300"}
                )
            else:
                return Response(content=EMPTY_TILE_PNG, media_type="image/png")
    except Exception as exc:
        logger.warning(f"Error fetching tile {layer}/{z}/{x}/{y}: {exc}")
        return Response(content=EMPTY_TILE_PNG, media_type="image/png")


@app.get("/api/v1/traffic/flow-segment")
async def get_traffic_flow_segment(lat: float = Query(...), lon: float = Query(...)):
    """
    Fetches real-time traffic flow telemetry for any coordinate point.
    """
    key = settings.TOMTOM_API_KEY
    if not key or not key.strip():
        return JSONResponse(status_code=503, content={"error": "TomTom API key not configured on server"})

    url = (
        f"https://api.tomtom.com/traffic/services/4/flowSegmentData/relative0/10/json"
        f"?key={key}&point={lat},{lon}&unit=KMPH"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                return resp.json()
            else:
                return JSONResponse(status_code=resp.status_code, content={"error": "TomTom upstream error"})
    except Exception as exc:
        logger.warning(f"Flow segment error: {exc}")
        return JSONResponse(status_code=500, content={"error": str(exc)})


@app.get("/api/v1/traffic/incident-details")
async def get_traffic_incidents():
    """
    Fetches real-time accident, closure, and road hazard details.
    """
    key = settings.TOMTOM_API_KEY
    if not key or not key.strip():
        return []

    bbox = "75.60,31.15,75.85,31.30"
    fields = "{incidents{type,geometry{type,coordinates},properties{id,iconCategory,magnitudeOfDelay,events{description,code},startTime,endTime,from,to,length,delay}}}"
    url = (
        f"https://api.tomtom.com/traffic/services/5/incidentDetails"
        f"?key={key}&bbox={bbox}&fields={urllib.parse.quote(fields)}"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("incidents", [])
            return []
    except Exception as exc:
        logger.warning(f"Incident details error: {exc}")
        return []


@app.get("/api/v1/traffic/search")
async def search_traffic_places(query: str = Query(...), limit: int = Query(6)):
    """
    Fuzzy POI and Landmark search biased to Phagwara emergency jurisdiction.
    """
    key = settings.TOMTOM_API_KEY
    if not key or not key.strip() or not query.strip():
        return []

    url = (
        f"https://api.tomtom.com/search/2/search/{urllib.parse.quote(query.strip())}.json"
        f"?key={key}&lat=31.2231&lon=75.7708&radius=35000&countrySet=IN&limit={limit}"
    )
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("results", [])
            return []
    except Exception as exc:
        logger.warning(f"Place search error: {exc}")
        return []


@app.post("/api/v1/traffic/set-key")
async def configure_server_traffic_key(req: KeyConfigRequest):
    """
    Secure server-side API key configuration endpoint.
    Verifies key validity before updating server settings and writing to .env.
    NEVER sends key back to client.
    """
    candidate_key = req.api_key.strip()
    if not candidate_key:
        raise HTTPException(status_code=400, detail="API key cannot be empty.")

    # Validate against TomTom API
    test_url = f"https://api.tomtom.com/traffic/map/4/tile/flow/relative0/13/5821/3296.png?key={candidate_key}"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            resp = await client.head(test_url)
            if resp.status_code not in (200, 304):
                if resp.status_code in (401, 403):
                    raise HTTPException(status_code=401, detail="Invalid TomTom API key. Access unauthorized by provider.")
                raise HTTPException(status_code=400, detail=f"TomTom provider responded with status {resp.status_code}.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Could not reach TomTom provider servers: {str(exc)}")

    # Update in-memory configuration
    settings.TOMTOM_API_KEY = candidate_key

    # Persist securely to backend .env
    env_file_path = settings.ROOT_DIR / ".env"
    try:
        existing_lines = []
        if env_file_path.exists():
            existing_lines = env_file_path.read_text(encoding="utf-8").splitlines()
        
        updated = False
        new_lines = []
        for line in existing_lines:
            if line.startswith("TOMTOM_API_KEY="):
                new_lines.append(f'TOMTOM_API_KEY="{candidate_key}"')
                updated = True
            else:
                new_lines.append(line)
        if not updated:
            new_lines.append(f'TOMTOM_API_KEY="{candidate_key}"')
        env_file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Could not persist key to .env file: {exc}")

    return {
        "success": True,
        "message": "TomTom API key successfully verified and stored in server environment.",
        "configured": True
    }


@app.post("/api/v1/traffic/remove-key")
def remove_server_traffic_key():
    """Removes the TomTom API key from server environment."""
    settings.TOMTOM_API_KEY = None
    env_file_path = settings.ROOT_DIR / ".env"
    try:
        if env_file_path.exists():
            lines = env_file_path.read_text(encoding="utf-8").splitlines()
            new_lines = [l for l in lines if not l.startswith("TOMTOM_API_KEY=")]
            env_file_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception as exc:
        logger.warning(f"Could not update .env file: {exc}")

    return {
        "success": True,
        "message": "TomTom API key removed from server environment.",
        "configured": False
    }


# -------------------------------------------------------------
# Production Static SPA Frontend Serving
# -------------------------------------------------------------
frontend_dist_dir = settings.ROOT_DIR / "frontend" / "dist"
if frontend_dist_dir.exists() and (frontend_dist_dir / "index.html").exists():
    app.mount("/assets", StaticFiles(directory=str(frontend_dist_dir / "assets")), name="frontend_assets")

    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"], include_in_schema=False)
    async def serve_spa_frontend(full_path: str):
        # Exclude API endpoints, docs, openapi, maps, ws
        if full_path.startswith(("api/", "docs", "redoc", "openapi.json", "maps/", "ws/")):
            raise HTTPException(status_code=404, detail="Not Found")
        file_path = frontend_dist_dir / full_path
        if file_path.is_file():
            return FileResponse(file_path)
        return FileResponse(frontend_dist_dir / "index.html")
