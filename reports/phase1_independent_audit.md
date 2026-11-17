# EmergencyRoute AI — Phase 1 Independent Verification Audit Report

**Audit Date:** November 2026  
**Auditor Role:** Senior GIS Engineer, Geospatial Data Scientist & Independent Quality Auditor  
**Scope:** Phase 1 Hybrid Road Network, Dataset Integrity, and Mapping API Integration  
**Geographical Scope:** Phagwara, Kapurthala District, Punjab, India  

---

## 1. Executive Summary & Audit Matrix

This independent verification audit was conducted by inspecting the underlying code, raw GraphML files, GeoJSON and CSV exports, traffic data tables, API endpoints, and pytest execution logs. The system was evaluated strictly against reality: separating genuine geographical observations from estimations, synthetic demonstration models, and unconfigured commercial integrations.

### Independent Verification Matrix

| Item | Result | Justification / Finding | Correction Applied |
| :--- | :---: | :--- | :--- |
| **Actual OSM data verified** | **PASS** | Phagwara drivable road network extracted via OSMnx 2.x from OpenStreetMap planet snapshot under ODbL 1.0 license. Geographic bounding box (Lat 31.1693° to 31.2770° N, Lon 75.7078° to 75.8339° E) accurately captures Phagwara municipal boundary and arterial corridors. | Documented retrieval parameters and attribution in data provenance registry. |
| **Graph counts verified** | **PASS** | Directed `MultiDiGraph` verified in GraphML, GeoJSON, and CSV: exactly **3,975 nodes** and **10,229 directed edges**. | None needed; counts match across all exported formats. |
| **Road lengths verified** | **PASS** | Total network length is **1,276.16 km**, computed by summing individual directed edge `length` attributes in meters divided by 1000. Reverse-direction edges on two-way roads are counted separately as distinct directed edges. | Formula verified and confirmed. |
| **Speed estimates correctly labelled** | **PASS** | Audited all 10,229 edges: exactly **0 edges** contain raw OSM `maxspeed` tags. 100% of speeds are estimated based on highway class (`motorway`=80, `trunk`=60, `primary`=50, `secondary`=40, `residential`=25, `service`=15 km/h). | Corrected report to explicitly state that speeds are highway-class estimates, not live vehicle telemetry. |
| **Synthetic traffic clearly labelled** | **PASS** | `traffic_observations.csv`, `traffic_profiles.csv`, and `traffic_scenarios.json` are generated using a deterministic NumPy model (Seed 42). All records have `is_live=False` and `source="synthetic_simulation"`. | Verified that the API and UI display `SIMULATED` badges. |
| **Road closures correctly classified** | **PASS** | `data/traffic/road_closures.csv` previously contained generic incident text. | Replaced with explicit `[SIMULATED ROAD CLOSURE]` labels. Clarified that closures are test scenarios, not real municipal emergency blockages. |
| **Landmark coordinates verified** | **PASS** | Curated coordinates for Civil Hospital (31.2223, 75.7672), LPU Gate (31.2536, 75.7037), and Phagwara Junction (31.2185, 75.7725) match Phagwara ground reality. | Updated fallback search: if an address query does not match a verified landmark, the API returns empty results rather than guessing arbitrary locations. |
| **Delhivery live API verified** | **NOT VERIFIED** | The Delhivery HTTPX client, retry policies, and fallback wrappers are implemented and pass unit tests with mocks. However, no live commercial `DELHIVERY_API_KEY` was provided. | Marked honestly as **NOT VERIFIED (LIVE)**. Client operates safely in verified offline fallback mode without claiming active commercial connectivity. |
| **No fabricated live information** | **PASS** | Zero fake live vehicle feeds or fabricated live traffic. All dashboard indicators and API responses explicitly state `SIMULATED`, `ESTIMATED`, or `UNCONFIGURED FALLBACK`. | None needed. |
| **Automated tests reproduced** | **PASS** | Executed `pytest backend/tests/test_phase1.py -v`. All **19 tests pass cleanly (100%)** in 14.47s with 0 failures and 0 skipped. | Documented that 1 test uses mocked HTTP responses for rate-limiting verification. |
| **User-facing wording is simple** | **PASS** | Frontend displays clear, jargon-free badges: "Estimated Free-Flow Time", "Simulated Peak Hours", and "Commercial Map Offline (Using OSM)". Complex mathematical details are kept in technical documentation. | Verified UI text clarity. |

---

## 2. In-Depth OpenStreetMap Graph Verification

- **Authoritative Graph:** [`data/processed/graph/phagwara_roads.graphml`](file:///d:/Antigravity/AI_project/EmergencyRoute-AI/data/processed/graph/phagwara_roads.graphml)
- **Graph Type:** `networkx.MultiDiGraph` (Directed, Multi-Edge).
- **Node Count:** 3,975.
- **Edge Count:** 10,229.
- **Export Parity:**
  - `data/processed/nodes/phagwara_nodes.csv`: 3,975 rows.
  - `data/processed/edges/phagwara_edges.csv`: 10,229 rows.
  - `data/processed/nodes/phagwara_nodes.geojson`: 3,975 features.
  - `data/processed/edges/phagwara_edges.geojson`: 10,229 features.
- **Directional & Parallel Edge Breakdown:**
  - `oneway == True`: 199 edges.
  - `oneway == False`: 10,030 edges (representing 5,015 physical two-way road segments split into opposing directed edges).
  - Parallel edges (`key > 0`): 30 edges (30 pairs of physical parallel edges preserved with distinct keys $k=0$ and $k=1$).
- **Connectivity:**
  - Weakly Connected Components (WCC): 7 components; largest covers **3,959 nodes (99.60%)**.
  - Strongly Connected Components (SCC): 10 components; largest covers **3,956 nodes (99.52%)**.
  - Isolated Nodes: 4 junctions (preserved without deletion, in compliance with project rules).
- **Geographic Extent:**
  - Latitude: 31.169305° N to 31.277028° N.
  - Longitude: 75.707801° E to 75.833874° E.
  - Represents the municipal bounds of Phagwara and adjacent corridors connecting toward Jalandhar and Ludhiana (NH44).

---

## 3. Speed Limit & Travel-Time Audit

- **Observed Speed Limits:** OSM currently contains **zero (`0`) raw `maxspeed` tags** in the Phagwara bounding box.
- **Imputed Baseline Speeds:** 10,229 edges (100%) have speeds assigned using standardized Indian urban/arterial highway classification defaults:
  - `motorway` / `motorway_link`: 80.0 km/h
  - `trunk` / `trunk_link` (GT Road / NH44): 60.0 km/h
  - `primary` / `primary_link`: 50.0 km/h
  - `secondary` / `secondary_link`: 40.0 km/h
  - `tertiary` / `tertiary_link`: 30.0 km/h
  - `residential` / `living_street`: 25.0 km/h
  - `service` / `unclassified`: 15.0 km/h
- **Baseline Travel-Time Formula:**
  $$\text{time\_cost\_seconds} = \frac{\text{length\_meters}}{\text{speed\_kph} \times \frac{1000}{3600}}$$
- **Audit Clarification:** All travel times calculated using this formula represent **ideal, free-flow baseline estimates**, not real-time or measured ETAs.

---

## 4. Traffic & Closure Files Audit

1. **`data/traffic/traffic_observations.csv` (61,374 rows):**
   - **Provenance:** `SIMULATED_REPRODUCIBLE`
   - **Generation:** Deterministic NumPy model parameterized by time of day across 4 diurnal profiles (`morning_peak`, `evening_peak`, `afternoon_offpeak`, `night_clear`) using Seed 42.
   - **Fields:** `is_live=False`, `source="synthetic_simulation"`.
2. **`data/traffic/traffic_profiles.csv` (72 rows):**
   - **Provenance:** `SIMULATED_HOURLY_CURVES`
   - **Generation:** Aggregated hourly congestion multipliers by highway type.
3. **`data/traffic/road_closures.csv` (3 rows):**
   - **Provenance:** `SIMULATED_TEST_SCENARIOS`
   - **Correction:** The incident descriptions have been updated to explicitly read:
     - `[SIMULATED ROAD CLOSURE] Test collision scenario near Hanumangarh Chowk (GT Road)`
     - `[SIMULATED ROAD CLOSURE] Test underpass seasonal waterlogging scenario`
     - `[SIMULATED ROAD CLOSURE] Test underpass seasonal waterlogging scenario (Opposite Direction)`
   - **Finding:** These are test fixtures designed to verify dynamic graph pruning and rerouting algorithms, not real-world municipal road closures.

---

## 5. Landmark & Geocoding Verification

- **Curated POI Registry:**
  - `Civil Hospital Phagwara`: Lat `31.2223`, Lng `75.7672` (Verified on GT Road).
  - `LPU Main Gate`: Lat `31.2536`, Lng `75.7037` (Verified on Jalandhar-Delhi GT Road).
  - `Phagwara Junction Railway Station`: Lat `31.2185`, Lng `75.7725` (Verified on Station Road).
  - `Phagwara Central Bus Stand`: Lat `31.2215`, Lng `75.7738` (Verified near City Center).
  - `Hanumangarh Chowk`: Lat `31.2241`, Lng `75.7695` (Verified intersection).
- **Search Behavior Correction:**
  - Previously, an unrecognized address search could fall back to generic town center landmarks.
  - **Correction Applied:** If a user query does not match any verified landmark in the local registry, the geocoding service now returns an empty result list (`count: 0, results: []`) with an honest status indicating that live street-level geocoding requires a configured external commercial provider.

---

## 6. Delhivery Integration Status: NOT VERIFIED (LIVE)

- **Official Documentation Source:** Delhivery Maps & Location Intelligence Platform API Specifications.
- **Implemented Modules:**
  - `DelhiveryClient` with exponential backoff and credential masking.
  - `DelhiveryGeocodingService` for address search.
  - `DelhiveryRoutingService` for external baseline reference routing.
  - `DelhiveryTrafficService` for external commercial traffic telematics.
- **Live Verification Status:** **NOT VERIFIED (LIVE)**
  - *Reason:* No active commercial `DELHIVERY_API_KEY` was supplied in the environment.
  - *Test Methodology:* Verified using `unittest.mock` and unit test fixtures simulating 429 rate limits, 500 server errors, and successful payloads.
  - *Audit Finding:* The client architecture is sound and production-ready, but **it must not be claimed as live-tested against Delhivery production servers**. The system operates cleanly in its verified offline fallback mode.

---

## 7. Automated Test Suite Audit

- **Command Executed:** `pytest backend/tests/test_phase1.py -v`
- **Total Tests:** 19
- **Passed:** 19 (100%)
- **Failed:** 0
- **Skipped:** 0
- **Warnings:** 2 (Starlette/AnyIO deprecation warnings)
- **Mocks Used:**
  - `test_delhivery_client_retry_and_rate_limit`: Uses `unittest.mock.patch("httpx.Client.request")` to verify retry backoff and rate-limiting handling.
  - Remaining 18 tests run on real local data (authoritative GraphML, spatial KD-tree, deterministic synthetic traffic generator, and FastAPI test client).

---

## 8. Summary of Findings

### 1. What is genuinely working:
- Real Phagwara road network graph (`3,975 nodes`, `10,229 edges`, `1,276.16 km`) loaded and queryable.
- Preservation of directed one-way streets, parallel multigraph edges, and disconnected components.
- Interactive HTML road network map (`maps/phagwara_road_network.html`).
- Nearest-node spatial resolution using Scipy KD-Tree.
- Fully verified offline fallback mechanisms for geocoding, visual tiles, and routing references.
- All 19 Phase 1 automated tests passing cleanly.

### 2. What is only simulated:
- Traffic congestion levels (`morning_peak`, `evening_peak`, `afternoon_offpeak`, `night_clear`) generated deterministically via NumPy Seed 42.
- Road closures (GT Road collision and Railway Underpass waterlogging) created for algorithm stress-testing.

### 3. What is estimated:
- Road speeds: Derived 100% from OSM highway classification tags (no raw OSM speed limit tags exist in Phagwara).
- Baseline travel times: Calculated from length and imputed speed limits assuming free-flow traffic.

### 4. What could not be verified:
- **Delhivery live API calls:** Cannot be verified against live production servers without a paid commercial API key. The integration code and offline fallbacks are verified, but the live service is marked **NOT VERIFIED**.

### 5. What was corrected during this audit:
1. Re-labeled test road closures in `road_closures.csv` to explicitly include `[SIMULATED ROAD CLOSURE]` to eliminate any impression of real-world municipal blockages.
2. Hardened geocoding fallback: searches that do not match verified landmarks return empty results rather than guessing arbitrary locations.
3. Updated data provenance documentation in `reports/phase1_data_provenance.json` and `reports/phase1_corrected_validation_report.json`.

