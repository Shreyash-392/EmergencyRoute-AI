# EmergencyRoute AI – Phase 1
## Hybrid Road Network, Dataset, and Map Integration for Phagwara, Punjab, India

An advanced, production-grade emergency vehicle route planning architecture built for the Smart India Hackathon (SIH) problem domain.

Phase 1 establishes the **authoritative road network topology**, commercial **Delhivery Maps platform adapter**, **synthetic traffic simulation pipeline**, and **FastAPI backend services**.

---

## 🏗️ Architecture & Technology Stack

- **Geospatial & Graph Processing:** OpenStreetMap, OSMnx 2.x, NetworkX 3.x, GeoPandas, Shapely, Pyogrio
- **Commercial Map Integration:** Delhivery Maps & Location Intelligence Platform (HTTPX client with fallback)
- **Synthetic Simulation Engine:** Deterministic pseudo-random scenario generator (6 scenarios, 61,374 observations)
- **Backend API:** Python 3.10+, FastAPI, Pydantic v2, Uvicorn
- **Visualization:** Folium, Leaflet, React + Vite + TypeScript (Scaffold)
- **Testing:** Pytest (19 automated tests, 100% pass rate)

---

## 📁 Project Structure

```
EmergencyRoute-AI/
│
├── backend/
│   ├── app/
│   │   ├── main.py                          # FastAPI REST API endpoints & lifespan handler
│   │   ├── core/
│   │   │   ├── config.py                    # Pydantic BaseSettings (.env loading)
│   │   │   └── graph_loader.py              # GraphML persistence and memory caching
│   │   ├── services/
│   │   │   ├── osm_service.py               # OSMnx graph extraction & speed imputation
│   │   │   ├── graph_service.py             # Nearest node matching & baseline Dijkstra
│   │   │   └── validation_service.py        # Network topology & connectivity validation
│   │   ├── integrations/
│   │   │   ├── delhivery/
│   │   │   │   ├── client.py                # HTTPX client with retries, timeout & token redaction
│   │   │   │   ├── maps_service.py          # Map tile configuration (Delhivery / OSM)
│   │   │   │   ├── geocoding_service.py     # Address geocoding with Phagwara POI fallback
│   │   │   │   ├── routing_service.py       # Commercial routing with local graph fallback
│   │   │   │   └── schemas.py               # Pydantic request & response schemas
│   │   │   └── traffic/
│   │   │       ├── traffic_models.py        # Observations, closures & scenario models
│   │   │       ├── traffic_provider.py      # Abstract provider interface
│   │   │       ├── mock_traffic.py          # Deterministic synthetic simulation engine
│   │   │       └── delhivery_traffic.py     # Commercial ETA delay adapter
│   │
│   └── tests/
│       └── test_phase1.py                   # 19 comprehensive automated tests
│
├── frontend/                                # React + Vite + TypeScript scaffold
│   ├── src/
│   │   ├── App.tsx                          # Emergency dispatch UI shell & map viewer
│   │   └── services/api.ts                  # Typed Axios client for FastAPI backend
│   ├── package.json
│   └── vite.config.ts
│
├── data/
│   ├── raw/osm/                             # Raw Overpass API query caches
│   ├── processed/
│   │   ├── graph/phagwara_roads.graphml     # Authoritative GraphML (3,975 nodes, 10,229 edges)
│   │   ├── nodes/                           # phagwara_nodes.geojson & phagwara_nodes.csv
│   │   └── edges/                           # phagwara_edges.geojson & phagwara_edges.csv
│   └── traffic/
│       ├── traffic_observations.csv         # 61,374 simulated scenario observations
│       ├── traffic_profiles.csv             # Aggregated speed profiles by road classification
│       ├── road_closures.csv                # Impassable emergency roadblock records
│       └── traffic_scenarios.json           # Scenario definitions & congestion factors
│
├── maps/
│   └── phagwara_road_network.html           # 22 MB interactive Folium map visualization
├── reports/
│   ├── phase1_validation_report.json        # Machine-readable graph audit report
│   └── phase1_integration_report.md         # Comprehensive architectural documentation
├── scripts/
│   ├── extract_and_export.py                # Graph extraction, validation & file export
│   ├── generate_traffic.py                  # Synthetic traffic observation generator
│   └── build_folium_map.py                  # Folium HTML map generator
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 📊 Measured Phagwara Road Network Metrics

Figures computed directly from the extracted OpenStreetMap network:

- **Graph Structure:** Directed `MultiDiGraph` (preserves one-ways and parallel multi-edges)
- **Total Road Nodes:** `3,975`
- **Total Directed Edges:** `10,229`
- **Total Road Length:** `1,276.16 km`
- **Mean Segment Length:** `124.76 m`
- **Mean Free-Flow Travel Time:** `17.88 s`
- **Parallel Edge Pairs:** `30` pairs (`60` directed edges)
- **One-Way Directed Edges:** `199`
- **Weakly Connected Components:** `7` (Largest WCC covers **99.60%** of nodes)
- **Strongly Connected Components:** `10` (Largest SCC covers **99.52%** of nodes)
- **Preserved Isolated Nodes:** `4` (kept without destructive pruning)
- **Validation Status:** `PASS`

---

## 🚀 Quickstart Guide

### 1. Environment Setup
```bash
cd EmergencyRoute-AI
python -m venv venv

# Windows
venv\Scripts\activate

# Linux / macOS
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables (Optional)
```bash
cp .env.example .env
```
*Note: If `DELHIVERY_API_KEY` is not provided, the platform automatically and gracefully operates using high-resolution OpenStreetMap tiles and verified Phagwara landmark references.*

### 3. Re-extract Road Network & Export Datasets (Already pre-generated)
```bash
python scripts/extract_and_export.py
```

### 4. Generate Synthetic Traffic Scenarios
```bash
python scripts/generate_traffic.py
```

### 5. Build Interactive Folium Map
```bash
python scripts/build_folium_map.py
```

### 6. Start FastAPI Backend Server
```bash
uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 7. Run Test Suite
```bash
pytest backend/tests/test_phase1.py -v
```

---

## 🌐 API Endpoints

- `GET /api/v1/health`: Operational health check, node/edge counts, and active provider status.
- `GET /api/v1/map/config`: Tile layer URL templates and copyright attributions.
- `GET /api/v1/map/locations/search?q={query}`: Address geocoding and landmark search.
- `GET /api/v1/roads/statistics`: Structural graph validation and connectivity report.
- `GET /api/v1/traffic/status?scenario={scenario_id}`: Scenario status and active road closures.
- `GET /api/v1/routes/reference`: Baseline directed shortest path distance and travel time.

