# ZERO FABRICATED DATA POLICY AUDIT & COMPLIANCE REPORT
**EmergencyRoute AI &bull; Phagwara Municipal Operations System**  
**Audit Date:** 2026-11-07  
**Compliance Standard:** Zero Fabricated Data Policy (Mandatory Operational Honesty)

---

## 1. Executive Summary

A comprehensive, full-stack audit of EmergencyRoute AI was executed across the database, backend services, API endpoints, frontend pages, telemetry layers, and mapping engines. 

In strict adherence to the **Zero Fabricated Data Policy**, all synthetic traffic scenarios, seeded vehicle tracking coordinates, pre-populated mock emergency calls, hardcoded response times, and unverified demo triggers were eradicated from production-facing systems.

Where genuine real-time data is unavailable (e.g. live vehicle GPS telematics, real-time street sensors), the system now surfaces **honest empty states** and **approved data provenance badges**. Data honesty has been prioritized over decorative aesthetics.

---

## 2. Files Inspected

The audit inspected the following production and test components:

### Backend
1. `backend/app/db/database.py` (Schema, session management, table initialization)
2. `backend/app/dispatch/dispatch_service.py` (Intake pipeline, vehicle ranking, dispatch state)
3. `backend/app/dispatch/dispatch_models.py` (Pydantic models for calls and assignments)
4. `backend/app/traffic/traffic_service.py` (Traffic management, road closures)
5. `backend/app/traffic/traffic_simulator.py` (Scenario simulation logic)
6. `backend/app/traffic/road_closure_manager.py` (Closure registration and edge pruning)
7. `backend/app/demo/demo_service.py` (Demonstration walkthrough service)
8. `backend/app/main.py` (FastAPI routing, lifecycle hooks, WebSocket broadcasting)
9. `data/emergency_route.db` (SQLite production database storage)

### Frontend
1. `frontend/src/pages/Dashboard.tsx` (Operational overview, KPI metrics, telemetry map)
2. `frontend/src/pages/EmergencyDispatch.tsx` (112 intake console, vehicle allocation)
3. `frontend/src/pages/TrafficMonitor.tsx` (Roadway monitor, closure log)
4. `frontend/src/pages/TrafficSimulation.tsx` (Road closure and detour evaluation lab)
5. `frontend/src/pages/RoutePlanner.tsx` (A* and OSRM dual routing engines)
6. `frontend/src/pages/AlgorithmComparison.tsx` (Routing engine benchmark suite)
7. `frontend/src/pages/SystemSettings.tsx` (System diagnostics and storage status)
8. `frontend/src/components/maps/PhagwaraMap.tsx` (Leaflet tile layer, route rendering, popups)
9. `frontend/src/components/layout/Navbar.tsx` (Municipal header, system status)
10. `frontend/src/components/layout/Sidebar.tsx` (Module navigation)
11. `frontend/src/components/layout/JudgeDemoModal.tsx` (DELETED)

### Automated Test Suites
1. `backend/tests/test_phase1.py` (OSM graph integrity, edge attributes, connectivity)
2. `backend/tests/test_phase2_algorithms.py` (A*, BFS, DFS, Greedy correctness)
3. `backend/tests/test_phase2_correctness_audit.py` (Admissibility, non-negative costs)
4. `backend/tests/test_phase2_traffic_rerouting.py` (Closure pruning and rerouting)
5. `backend/tests/test_phase3_dispatch_demo.py` (Intake API, unit ranking, assignments)
6. `backend/tests/test_osrm_integration.py` (OSRM Route API, GeoJSON parsing, fallbacks)

---

## 3. Fabricated Data Discovered & Corrective Action Taken

| Discovered Item | Location | Root Issue | Action Taken |
| :--- | :--- | :--- | :--- |
| **Pre-seeded Emergency Incidents** | `database.py`, `emergency_route.db` | Mock calls (`[DISPATCH TEST] Medical Emergency Call`) were auto-seeded into DB on boot. | Removed `sample_incidents` entirely. Purged SQLite database. Production boots with 0 incidents. |
| **Fake Vehicle GPS Coordinates** | `database.py`, `emergency_route.db` | 8 static emergency vehicles with mock lat/lng coordinates were seeded into the DB. | Seed routine gated behind `seed_test_fixtures=False` by default. Production DB purged. When tracking is offline, returns `[]`. |
| **Synthetic Traffic Scenarios** | `TrafficMonitor.tsx`, `RoutePlanner.tsx`, `AlgorithmComparison.tsx` | UI offered "Morning Peak (Seed 42)", "Evening Peak", "Monsoon Flood" synthetic slowdown multipliers. | Removed scenario selectors from production pages. Local A* travel times use genuine OSM legal speed limits. |
| **Hardcoded Response KPI** | `Dashboard.tsx` | Metric card claimed "Avg Est. Response: 4.8 min". | Removed invented number. Displays "Unavailable" with subtitle *"Live operational data is unavailable."* |
| **Simulated Closure Claim** | `TrafficMonitor.tsx` | UI claimed "All 10,229 directed edges are open and passable." | Replaced with honest policy: *"No recorded road closures found. This does not guarantee that all roads are open."* |
| **Hackathon & Demo Modals** | `Navbar.tsx`, `App.tsx`, `JudgeDemoModal.tsx` | Demo button injected synthetic incidents. Navbar had "SIH1617" hackathon tag. | Deleted `JudgeDemoModal.tsx`. Removed all demo triggers and hackathon badges. Replaced with municipal operations status. |
| **CartoDB Watermark** | `PhagwaraMap.tsx` | Basemap showed `API KEY REQUIRED carto.com/basemaps/apikey` watermark. | Replaced with official OpenStreetMap tile server (`tile.openstreetmap.org`). |

---

## 4. Approved Data Sources & Standard Provenance Labels

All information displayed in the application now carries one of the authorized provenance labels:

1. **`OSM DATA`**:
   - **Provenance**: Official OpenStreetMap network for Phagwara (3,975 intersections, 10,229 directed edges, 1,276 km network length).
   - **Applied To**: Graph network structure, local A* routing geometry, road speed limits, highway classifications, and algorithmic benchmarks.
2. **`OSRM RESPONSE`**:
   - **Provenance**: Official public Open Source Routing Machine driving API (`router.project-osrm.org`).
   - **Applied To**: External driving route comparison, road distance, duration estimates, and turn-by-turn steps.
3. **`USER REPORTED`**:
   - **Provenance**: Records explicitly submitted by a dispatcher (e.g. 112 phone intake) or operator-registered test road closures.
   - **Applied To**: Emergency incident cards, dispatch queue entries, and user-initiated road closures.
   - **Constraint**: Never labeled as officially verified.
4. **`OFFICIALLY VERIFIED`**:
   - **Provenance**: Authoritative government or emergency agency telematics.
   - **Applied To**: Reserved exclusively for authenticated municipal tracking feeds. (Currently not active; marked `UNAVAILABLE`).
5. **`UNAVAILABLE`**:
   - **Provenance**: Honest indicator when no real-time telemetry or external feed is connected.
   - **Applied To**: Live traffic congestion, emergency vehicle GPS telematics, live dispatch response metrics.

---

## 5. Honest Empty-State Behavior

When real-time information is absent, the interface presents the exact standard empty states mandated by policy:

- **Live Traffic Feed**:  
  `"No verified live traffic information is currently available."` &bull; **Badge: `UNAVAILABLE`**
- **Road Closures**:  
  `"No recorded road closures found. This does not guarantee that all roads are open."` &bull; **Badge: `UNAVAILABLE`**
- **Emergency Incidents**:  
  `"No verified emergency incidents are currently available."` &bull; **Badge: `UNAVAILABLE`**
- **Emergency Vehicle Tracking**:  
  `"No connected emergency vehicle tracking feed."` &bull; **Badge: `UNAVAILABLE`**
- **Dashboard Telemetry**:  
  `"Live operational data is unavailable."` &bull; **Badge: `UNAVAILABLE`**

---

## 6. Routing & Telemetry Integrity

1. **Local Routing**:
   - Executes Dijkstra and A* Search directly on the real directed OSM MultiDiGraph.
   - Travel times are derived strictly from road segment lengths and legal highway speed limits from OSM.
   - Clearly labeled: *"Calculated Travel Time Estimate, Not Live ETA."*
2. **External OSRM Routing**:
   - Queries the public OSRM driving engine using real coordinate pairs.
   - Free-flow estimates are clearly identified as OSRM routing engine outputs, not real-time GPS probe traffic.
3. **Commercial Delhivery Adapter**:
   - Evaluates API key configuration.
   - When keys are not present in `.env`, cleanly falls back with an explicit honest notice: `"No live Delhivery API credentials configured"`. No fake delivery routes are fabricated.

---

## 7. Verification Test Results

### Backend Automated Test Suite
- **Command**: `pytest backend/tests -v`
- **Total Tests Executed**: 64
- **Passed**: 64 (100%)
- **Failed**: 0
- **Duration**: 14.73 seconds
- **Note**: Test fixtures (such as test vehicle assignments in `test_phase3_dispatch_demo.py`) are strictly confined to isolated test scopes using `seed_test_fixtures=True` inside test fixtures. The production database is left with 0 unverified records.

### Frontend Production Build
- **Command**: `npm run build`
- **Output**:
  - `dist/index.html`: 0.91 kB
  - `dist/assets/index.css`: 38.84 kB
  - `dist/assets/index.js`: 836.56 kB
- **TypeScript Typecheck**: Passed with 0 errors.

### Live Production Database State Verification
- **Vehicle Count**: `0`
- **Incident Count**: `0`
- **Dispatch Assignment Count**: `0`
- **Active Recorded Closures**: `0`

---

## 8. Conclusion

EmergencyRoute AI is now fully compliant with the **Zero Fabricated Data Policy**. The entire platform operates exclusively on genuine OpenStreetMap road graph data, live OSRM external API responses, and dispatcher-entered user reports. Empty states and data source labels provide total transparency to operators, citizens, and municipal authorities.

