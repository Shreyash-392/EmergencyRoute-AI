# EmergencyRoute AI — Final API Integration & Telemetry Specification

**Project:** EmergencyRoute AI — Phase 3  
**Base URL:** `http://localhost:8000/api/v1`  
**WebSocket URL:** `ws://localhost:8000/ws/events`  
**Protocol:** HTTP/1.1 REST + WebSockets (RFC 6455)  
**Security & Credential Handling:** Safe bearer token encapsulation, zero leakage in telemetry payloads.  

---

## 1. REST Endpoints Inventory

### 1.1 System & Core
- **`GET /api/v1/health`**
  - **Purpose:** Health check, graph load status, Delhivery configuration state, database connection.
  - **Response:**
    ```json
    {
      "status": "healthy",
      "graph_loaded": true,
      "graph_nodes": 3975,
      "graph_edges": 10229,
      "delhivery_configured": false,
      "active_traffic_scenario": "morning_peak",
      "timestamp": "2026-11-06T16:16:30Z"
    }
    ```
- **`GET /api/v1/maps/config`**
  - **Purpose:** Map tile URLs, attribution, fallback flags, bounding box coordinates for Phagwara.
- **`GET /api/v1/maps/road-network/statistics`**
  - **Purpose:** Full topological audit: node counts, edge counts, total road length in km, WCC percentage, speed distribution.

### 1.2 Geocoding & Locations
- **`GET /api/v1/locations/search?query={q}`**
  - **Purpose:** Address and POI search with Delhivery geocoding integration and verified local landmark fallback (e.g. Civil Hospital, LPU Gate, Model Town, Phagwara Junction).

### 1.3 Routing & Algorithm Benchmarking
- **`POST /api/v1/routes/optimal`**
  - **Payload:** `{ "origin": [lat, lon], "destination": [lat, lon], "algorithm": "A_Star", "avoid_closures": true }`
  - **Response:** Optimal route geometry (GeoJSON coordinate list), distance in km, estimated travel time in minutes, nodes explored, execution time in ms.
- **`POST /api/v1/routes/compare`**
  - **Payload:** `{ "origin": [lat, lon], "destination": [lat, lon], "include_delhivery": true }`
  - **Response:** Simultaneous results for all 4 algorithms (`A_Star`, `BFS`, `DFS`, `Greedy_Best_First`) alongside independent `delhivery_reference`.
- **`POST /api/v1/routes/reference`**
  - **Purpose:** External Delhivery commercial routing reference. If API keys are unconfigured, returns graceful structured fallback notice without throwing 500 errors.

### 1.4 Traffic Intelligence & Incident Control
- **`GET /api/v1/traffic/status`**: Current traffic scenario, active congestion multipliers, average network speed.
- **`POST /api/v1/traffic/simulate?scenario={name}`**: Switch active synthetic scenario (`morning_peak`, `evening_peak`, `afternoon_offpeak`, `night_clear`).
- **`GET /api/v1/traffic/closures`**: List active road closures and severed graph edges.
- **`POST /api/v1/traffic/closures`**: Manually or programmatically inject a road closure.
- **`DELETE /api/v1/traffic/closures/{id}`**: Re-open a severed road segment.
- **`GET /api/v1/traffic/providers`**: List registered traffic providers and provenance flags.

### 1.5 Emergency Fleet Dispatch
- **`GET /api/v1/dispatch/vehicles`**: Retrieve 8 municipal emergency response units with live GPS locations and operational statuses (`AVAILABLE`, `DISPATCHED`, `BUSY`).
- **`GET /api/v1/dispatch/incidents`**: Retrieve current active emergency incidents.
- **`POST /api/v1/dispatch/incidents`**: Report a new emergency incident.
- **`POST /api/v1/dispatch/rank-vehicles`**: Intelligently rank all available vehicles using custom A* travel time and capability matching.
- **`POST /api/v1/dispatch/execute`**: Dispatch the recommended vehicle, compute route geometry, update vehicle status, and record assignment in database.

### 1.6 Judge Demonstration Suite
- **`GET /api/v1/demo/baseline`**: Run the standardized Model Town $\to$ Civil Hospital baseline route.
- **`POST /api/v1/demo/simulate-incident`**: Inject a major multi-vehicle collision on GT Road and calculate the dynamic A* rerouting bypass.
- **`POST /api/v1/demo/reset`**: Restore network closures, vehicles, and incidents to baseline state.

---

## 2. Real-Time Telemetry & WebSocket Protocol

### 2.1 WebSocket Connection
- **Endpoint:** `ws://localhost:8000/ws/events`
- **Supported Events:**
  - `incident_created`: New emergency incident logged.
  - `dispatch_created`: Vehicle assigned with route and ETA.
  - `road_closure_added`: Road segment severed.
  - `road_closure_removed`: Road segment re-opened.
  - `traffic_scenario_changed`: Traffic conditions updated.
  - `demo_incident_injected`: Judge demonstration collision triggered.
  - `demo_reset`: System state reset to initial conditions.

### 2.2 HTTP Polling Fallback
In environments with strict corporate firewalls or proxies blocking RFC 6455 WebSockets, the frontend automatically falls back to:
- **`GET /api/v1/events/poll?since={iso_timestamp}`**
  - Returns buffered broadcast events from the backend queue.
  - Frontend queries every 3 seconds seamlessly if the WebSocket disconnects.

---

## 3. Delhivery Commercial Integration & Graceful Fallback

```
+-------------------------------------------------------------+
|             Delhivery Commercial Integration                |
+-------------------------------------------------------------+
                               |
                   Is DELHIVERY_API_KEY valid?
                               |
                +--------------+--------------+
                |                             |
              [YES]                         [NO]
                |                             |
      Live Commercial API           Graceful Fallback Mode
      - Live Geocoding              - Local Landmark KD-Tree Search
      - Fleet Commercial Routing    - OpenStreetMap Standard Tiles
      - Telematics Speed Feed       - Deterministic Synthetic Traffic
```

The system strictly decouples Delhivery commercial services from the core DSA algorithms. Even when Delhivery is active, the four search algorithms run exclusively on the local Phagwara directed `MultiDiGraph`, preserving full offline autonomy and SIH evaluation compliance.

