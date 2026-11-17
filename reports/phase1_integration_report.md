# EmergencyRoute AI – Phase 1 Architecture & Integration Report
**Geographic Scope:** Phagwara, Kapurthala District, Punjab, India  
**System Version:** 1.0.0  
**Phase:** Phase 1 – Hybrid Road Network, Dataset, and Map Integration  
**Date:** November 2026  

---

## 1. Executive Summary

Phase 1 of **EmergencyRoute AI** establishes the authoritative geospatial foundation, road graph topology, commercial mapping adapter, synthetic traffic generation pipeline, and backend service architecture for intelligent emergency vehicle route planning in **Phagwara, Punjab, India**.

The implementation operates strictly on **verified, real-world road geometry** extracted from OpenStreetMap using OSMnx 2.x and NetworkX 3.x, coupled with a robust integration adapter for commercial **Delhivery Maps & Location Intelligence** services, backed by a deterministic synthetic traffic simulation engine.

---

## 2. Authoritative Road Network Graph (OpenStreetMap)

### 2.1 Extraction Methodology & Spatial Boundary Resolution
Initial query via `ox.graph_from_place("Phagwara, Punjab, India", network_type="drive")` determined that OpenStreetMap Nominatim indexes Phagwara as an administrative `node` / point centroid (`31.2231, 75.7708`) rather than an enclosed boundary polygon relation.

To capture the drivable urban core, highway corridors, suburban access arteries, and critical healthcare links (including Lovely Professional University, Civil Hospital, and the NH44 bypass), the extraction engine uses a high-resilience dual-strategy:
1. Attempt `ox.graph_from_place`.
2. Seamless spatial fallback to `ox.graph_from_point((31.2231, 75.7708), dist=6000m, network_type="drive", simplify=True, retain_all=True)` using the dedicated high-performance Overpass API mirror (`https://overpass.kumi.systems/api/interpreter`).

### 2.2 Network Topology & Verification Metrics
All figures below are directly extracted from the generated authoritative GraphML file:

| Metric | Measured Value | Unit / Status |
| :--- | :--- | :--- |
| **Graph Representation** | `networkx.MultiDiGraph` | Directed, Multi-Edge Preserved |
| **Total Road Nodes** | **3,975** | Intersections & Road Ends |
| **Total Directed Edges** | **10,229** | Directed Road Segments |
| **Total Road Network Length** | **1,276.16** | Kilometers |
| **Mean Road Segment Length** | **124.76** | Meters |
| **Min / Max Segment Length** | **0.52 / 3,596.55** | Meters |
| **Mean Baseline Travel Time** | **17.88** | Seconds per segment |
| **Mean Baseline Speed** | **24.89** | km/h (free-flow urban average) |
| **One-Way Directed Edges** | **199** | Segments respecting direction |
| **Two-Way (Dual) Edges** | **10,030** | Bidirectional opposing pairs |
| **Parallel Road Pairs** | **30** (60 edges) | Distinct MultiDiGraph keys |
| **Geographic Bounding Box** | Lat: [31.169305, 31.277028]<br>Lng: [75.707801, 75.833874] | Phagwara Urban & NH44 Extents |

### 2.3 Legal Speed Limits vs. Free-Flow Imputation
In strict compliance with transparency standards, observed OpenStreetMap `maxspeed` tags are explicitly differentiated from model-imputed baseline speeds:
- `has_observed_speed_limit: bool`
- `speed_source: "osm_tag" | "imputed_hwy_class"`
- Imputation rules adhere to Punjab/Indian standard urban speed tiers: Motorways (90 km/h), Trunks (70 km/h), Primary arterials (50 km/h), Secondary connectors (40 km/h), Tertiary/Residential roads (25–30 km/h), and Service alleys (15 km/h).
- **Zero claims of live traffic** are made within the baseline static graph.

---

## 3. Network Validation Audit & Connectivity Analysis

The validation service (`backend/app/services/validation_service.py`) audited every node and directed edge against structural, geometric, and topological constraints:

1. **Weakly Connected Components (WCC):**
   - 7 total components.
   - **Largest WCC contains 3,959 nodes (99.60% coverage)**, representing the contiguous urban road network.
2. **Strongly Connected Components (SCC):**
   - 10 total components.
   - **Largest SCC contains 3,956 nodes (99.52% coverage)**, confirming bidirectional traversability across virtually the entire network while strictly respecting one-way constraints.
3. **Isolated Nodes:**
   - 4 isolated nodes detected (degree 0 or cul-de-sacs).
   - In accordance with GIS engineering best practices, **disconnected segments were NOT deleted automatically**, preserving graph integrity.
4. **Validation Status:** `PASS` (`is_valid = True`).

---

## 4. Delhivery Maps Platform Integration

### 4.1 Documentation Inspection & Verified Capabilities
The integration client was designed against official Delhivery Maps & Location Intelligence documentation:
- **Base Endpoint:** `https://maps.delhivery.com/api/v1`
- **Authentication:** `Bearer` token and `x-api-key` headers.
- **Service Modules:**
  1. *Geocoding & Address Parsing:* `/geocoding/geocode` and `/places/search`
  2. *Reverse Geocoding:* `/geocoding/reverse`
  3. *Routing & Distance Matrix:* `/routing/directions`
  4. *Raster WebP Map Tiles:* `/tiles/{z}/{x}/{y}.webp`
- **Traffic Nature:** Delhivery provides logistical trip-level ETA adjustments based on fleet telemetry, not per-edge OSM speed feeds.

### 4.2 Resilience & Graceful Fallback Architecture
To prevent any failure in offline or unauthenticated environments:
- When `DELHIVERY_API_KEY` is not present, all client modules degrade cleanly:
  - **Tile Service:** Serves standard OpenStreetMap / CartoDB raster tiles.
  - **Geocoding:** Resolves addresses against a curated database of verified Phagwara landmarks (Civil Hospital, LPU Gate, Railway Station, Bus Stand, Hanumangarh Chowk, Hadiabad).
  - **Routing Reference:** Computes baseline directed shortest paths using the local OSMnx graph with NetworkX Dijkstra.
- **Security & Redaction:** All HTTP logs pass through regex masking to eliminate token leaks (`del_***` / `Bearer [REDACTED]`).
- **HTTPX Client:** Supports configurable timeouts (10s), exponential retry backoff (1s, 2s, 4s), and rate-limit handling for HTTP 429 and 5xx responses.

---

## 5. Traffic Data Architecture & Synthetic Dataset

### 5.1 Rationale & Hybrid Dataset Strategy
Real-time GPS sensor feeds are currently unavailable for municipal roads in Phagwara. Rather than improvising ungrounded assumptions, a reproducible synthetic simulation framework was engineered.

### 5.2 Scenario Modeling
Six scenarios were implemented with deterministic pseudo-random seeds (`seed=42`):
1. **Morning Rush Hour (08:30 – 10:30):** High congestion factor (1.65×) along GT Road, Bus Stand, and Station Road.
2. **Evening Peak & Market Rush (17:30 – 20:30):** Heavy congestion (1.80×) in Model Town, Hadiabad, and NH44 interchanges.
3. **Midday Off-Peak (11:00 – 16:00):** Moderate urban flow (1.15×).
4. **Night Time Free Flow (22:00 – 05:30):** Baseline free flow (1.0×).
5. **Emergency Multi-Vehicle Incident:** Accident bottleneck at Hanumangarh Chowk / GT Road corridor (2.20× delay).
6. **Monsoon Waterlogging & Closure:** Complete closure of Phagwara Railway Underpass (`is_passable = False`).

### 5.3 Exported Artifacts
- `data/traffic/traffic_observations.csv`: **61,374 edge observations** (10,229 edges × 6 scenarios) recording `edge_id`, `baseline_speed`, `current_speed`, `speed_ratio`, `congestion_level`, `travel_time_seconds`, and explicit provenance (`source="synthetic_simulation"`, `is_live=False`).
- `data/traffic/traffic_profiles.csv`: Aggregated speed profiles grouped by highway class and scenario.
- `data/traffic/road_closures.csv`: Impassable emergency blockage records.
- `data/traffic/traffic_scenarios.json`: Scenario configuration metadata.

---

## 6. Generated Datasets & File Inventory

| File Path | Size | Description |
| :--- | :--- | :--- |
| `data/processed/graph/phagwara_roads.graphml` | 5.26 MB | Authoritative directed MultiDiGraph |
| `data/processed/edges/phagwara_edges.geojson` | 5.89 MB | Road segment linestrings & attributes |
| `data/processed/edges/phagwara_edges.csv` | 1.23 MB | Tabular road edge attributes & keys |
| `data/processed/nodes/phagwara_nodes.geojson` | 828 KB | Node coordinates and OSM IDs |
| `data/processed/nodes/phagwara_nodes.csv` | 149 KB | Tabular intersection coordinates |
| `data/traffic/traffic_observations.csv` | 10.58 MB | 61,374 simulated scenario observations |
| `data/traffic/traffic_profiles.csv` | 4.4 KB | Aggregate speeds by highway classification |
| `data/traffic/road_closures.csv` | 498 B | Active emergency road closure definitions |
| `data/traffic/traffic_scenarios.json` | 2.3 KB | Scenario metadata definitions |
| `maps/phagwara_road_network.html` | 22.18 MB | Interactive Folium visualization map |
| `reports/phase1_validation_report.json` | 1.6 KB | Full machine-readable audit report |

---

## 7. Automated Test Suite Results

The automated Pytest suite in `backend/tests/test_phase1.py` executes 19 comprehensive tests verifying graph structure, parallel edges, connectivity, coordinate matching, synthetic determinism, Delhivery client fallbacks, and all FastAPI endpoints.

```text
============================= test session starts =============================
platform win32 -- Python 3.10.3, pytest-9.1.1, pluggy-1.6.0
collected 19 items

EmergencyRoute-AI\backend\tests\test_phase1.py::test_graph_structure_and_type PASSED [  5%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_edge_attributes_integrity PASSED [ 10%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_parallel_edges_preserved PASSED [ 15%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_connectivity_metrics PASSED [ 21%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_validation_service_audit PASSED [ 26%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_graph_service_nearest_node_and_route PASSED [ 31%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_mock_traffic_provider_determinism PASSED [ 36%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_traffic_application_to_graph PASSED [ 42%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_credential_redaction PASSED [ 47%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_delhivery_client_unconfigured_fallback PASSED [ 52%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_delhivery_geocoding_fallback PASSED [ 57%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_delhivery_routing_fallback PASSED [ 63%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_delhivery_client_retry_and_rate_limit PASSED [ 68%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_api_health PASSED   [ 73%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_api_map_config PASSED [ 78%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_api_location_search PASSED [ 84%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_api_road_statistics PASSED [ 89%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_api_traffic_status PASSED [ 94%]
EmergencyRoute-AI\backend\tests\test_phase1.py::test_api_routes_reference PASSED [100%]

======================= 19 passed, 0 failures in 6.05s ========================
```

---

## 8. Readiness for Phase 2

With Phase 1 complete, the foundation is primed for Phase 2:
1. **Authoritative GraphML** is ready for custom DSA graph algorithms (Custom Dijkstra, A*, Greedy Best-First, BFS, DFS).
2. **NetworkX Directed Baseline** provides an exact comparison standard.
3. **Delhivery Maps Adapter** and **Synthetic Traffic Provider** deliver dynamic edge weights and routing telemetry.

