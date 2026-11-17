# EmergencyRoute AI — Final System Architecture & Technical Specification

**Project Title:** EmergencyRoute AI — Intelligent Emergency Vehicle Route Rationalization & Dispatch  
**Academic Inspiration:** Smart India Hackathon Problem Statement SIH1617  
**Geographical Scope:** Phagwara, Punjab, India (Coordinates: Lat 31.18 to 31.26° N, Lon 75.70 to 75.82° E)  
**System Status:** Phase 3 Production Ready  
**Date:** November 2026  

---

## 1. Executive Summary & Purpose

EmergencyRoute AI is an intelligent transportation and dispatch platform engineered specifically for municipal emergency medical and rescue services in Phagwara, Punjab. Unlike typical shortest-path prototypes or commercial transit trackers, EmergencyRoute AI combines:

1. **A mathematically rigorous Graph Engine** implementing four custom search algorithms (A*, BFS, DFS, Greedy Best-First) executed on a real directed `MultiDiGraph` derived from OpenStreetMap (`3,975 nodes` and `10,229 edges`).
2. **Dynamic Traffic Fusion & Rerouting** supporting real-time edge travel time penalty calculation, congestion multipliers, and dynamic road closure excision.
3. **External Commercial Separation** utilizing Delhivery Maps SDK / REST interfaces strictly as an independent commercial benchmarking reference and address geocoder, ensuring local algorithmic execution remains 100% self-contained and auditable.
4. **An Operations Command Dashboard** written in React 18, Vite, TypeScript, Tailwind CSS, Leaflet, and Recharts, backed by FastAPI, WebSockets, and a spatial PostGIS/SQLite schema.
5. **Interactive Judge Demonstration Suite** allowing evaluators to step through an end-to-end emergency scenario: from Model Town to Civil Hospital, dynamic collision injection on GT Road, real-time A* recalculation, and fleet dispatch.

---

## 2. High-Level System Architecture

```mermaid
flowchart TD
    subgraph Data Sources & Topology
        OSM[OpenStreetMap Phagwara PBF] --> OSMnx[OSMnx 2.x Ingestion]
        OSMnx --> MDG[(Directed MultiDiGraph\n3,975 Nodes / 10,229 Edges)]
        MDG --> Adapter[MultiGraph Adapter & Adjacency Index]
    end

    subgraph Traffic Intelligence Engine
        MockTraffic[Deterministic Synthetic Traffic\nSeed 42 / 4 Diurnal Profiles] --> Fusion[Traffic Fusion Engine]
        DelhiveryTraffic[Delhivery Commercial Feed\nFallback / Mock Mode] --> Fusion
        Closures[Road Closure Manager\nActive Excisions] --> Fusion
        Fusion --> WeightCalc[Admissible Weight Calculator\ntt = L / (v_max * M_cong)]
    end

    subgraph DSA Search Engine
        Adapter & WeightCalc --> ASTAR[A* Search Engine\nAdmissible Haversine Heuristic]
        Adapter & WeightCalc --> BFS[BFS Engine\nFewest-Hop Baseline]
        Adapter & WeightCalc --> DFS[DFS Engine\nCycle-Handled Deep Search]
        Adapter & WeightCalc --> GREEDY[Greedy Best-First\nf(n) = h(n)]
    end

    subgraph Dispatch & Demo Orchestrator
        ASTAR --> DispatchSvc[Emergency Dispatch Service\nMulti-Criteria Fleet Ranking]
        DispatchSvc --> DemoEngine[Judge Demonstration Engine\n12-Step Walkthrough]
        DemoEngine --> DB[(PostGIS / SQLite ORM\nVehicles, Incidents, Dispatches)]
    end

    subgraph External Commercial Services
        DelhiveryAPI[Delhivery Maps API\nRouting & Geocoding] -.-> ExtCompare[Independent Reference\nNon-Polluting Baseline]
    end

    subgraph Telemetry & API Layer
        DB & ASTAR & ExtCompare --> FastAPI[FastAPI REST Endpoints]
        FastAPI --> WSMgr[WebSocket Event Manager\nBuffered Broadcast]
        WSMgr --> PollingFallback[HTTP Polling Fallback\n/api/v1/events/poll]
    end

    subgraph React Operations Dashboard
        FastAPI & WSMgr & PollingFallback --> UI[React 18 + Vite Frontend]
        UI --> MapView[Leaflet / OSM Multi-Polyline Map]
        UI --> Analytics[Recharts Benchmark Analytics]
        UI --> DispatchView[Emergency Fleet Console]
        UI --> DemoModal[Interactive Judge Modal]
    end
```

---

## 3. Road Network Graph Topology

The system operates directly on the topologically verified street network of Phagwara, Punjab:

- **Graph Structure:** `networkx.MultiDiGraph` (directed multigraph preserving parallel one-way lanes, dual carriageways, slip roads, and flyover ramps).
- **Nodes:** `3,975` physical junctions and georeferenced road vertices.
- **Edges:** `10,229` directed traversable road links.
- **Total Network Length:** `1,276.16 km`.
- **Largest Weakly Connected Component (WCC):** `99.6%` connectivity (3,960 nodes), ensuring virtually zero dead-ends or isolated subgraphs.
- **Attribute Completeness:** `100%` of edges possess valid `length` (meters), `speed_kph` (derived from OSM highway tags: `motorway`, `trunk`, `primary`, `secondary`, `residential`), `geometry`, `oneway` flags, and `time_cost_seconds`.

---

## 4. MultiGraph Adapter & Algorithm Implementation

All four search algorithms are implemented from scratch in pure Python using custom data structures, completely avoiding opaque NetworkX traversal libraries:

### 4.1 MultiGraph Parallel Edge Selection
Because the road network is a directed `MultiDiGraph`, adjacent nodes $u$ and $v$ may share multiple parallel edges $(u, v, k)$ representing distinct physical lanes or service roads:
$$\text{effective\_edge}(u, v) = \arg\min_{k} c(u, v, k)$$
Where $c(u, v, k)$ represents the dynamic traversal travel time in seconds. The custom `MultiGraphAdapter` transparently evaluates all parallel edges, prunes road closures, and yields the minimum-cost candidate.

### 4.2 Algorithm Mathematical Formulations

| Algorithm | Evaluation Function | Admissibility & Optimality | Data Structure | Explored Order |
| :--- | :--- | :--- | :--- | :--- |
| **A\* Search** | $f(n) = g(n) + h(n)$ | **Globally Optimal** ($h(n) \le h^*(n)$) | `heapq` Priority Queue | Minimum projected total time |
| **Greedy Best-First** | $f(n) = h(n)$ | **Sub-optimal** (Ignores accumulated $g(n)$) | `heapq` Priority Queue | Closest Haversine distance to target |
| **Breadth-First Search (BFS)** | $f(n) = \text{depth}(n)$ | **Minimal Hops Only** (Unweighted optimality) | `collections.deque` FIFO | Layer-by-layer radial expansion |
| **Depth-First Search (DFS)** | $f(n) = -\text{depth}(n)$ | **Non-Optimal** (Educational baseline) | LIFO Stack + Visited Set | Deepest branch first with cycle guard |

### 4.3 A* Admissible Heuristic Proof
To guarantee global travel-time optimality without under-estimating, the heuristic function $h(n)$ must be strictly admissible:
$$h(n) = \frac{\text{haversine}(n, \text{target})}{v_{\max}} \le h^*(n)$$
- $v_{\max} = 100.0 \text{ km/h} = 27.778 \text{ m/s}$ (maximum legal speed limit on any GT Road arterial segment in the Phagwara subgraph).
- Since straight-line Euclidean/Haversine distance is always less than or equal to actual road curve length ($\text{dist}_{\text{haversine}} \le \text{dist}_{\text{road}}$), dividing by the absolute maximum physical speed yields a guaranteed lower bound on travel time.
- Therefore, $h(n) \le h^*(n)$ holds for all nodes, preserving the triangle inequality and monotonic consistency.

---

## 5. Traffic Intelligence & Dynamic Fusion

The platform implements a resilient 3-tier traffic intelligence system:
1. **Tier 1 (Commercial Telematics):** Delhivery Maps live traffic API.
2. **Tier 2 (Deterministic Synthetic Traffic):** Diurnal time-of-day traffic model parameterized across 4 profiles:
   - `morning_peak` (08:00 - 11:00): Arterial GT Road congestion factor 1.8x - 2.5x.
   - `evening_peak` (17:00 - 20:30): Commercial market and town center congestion factor 2.0x - 3.0x.
   - `afternoon_offpeak` (12:00 - 16:00): Steady-state normal conditions (1.1x - 1.3x).
   - `night_clear` (22:00 - 06:00): Free-flow arterial speeds (1.0x).
3. **Tier 3 (Active Road Closures):** Real-time administrative excision of severed road segments. Road segments marked as closed are pruned from the `MultiGraphAdapter` adjacency generation, forcing immediate dynamic rerouting.

### Provenance Classification Table
| Field | Source Classification | Description |
| :--- | :--- | :--- |
| **Road Graph Geometry** | `REAL_OBSERVATION` | OpenStreetMap 2026 planet snapshot for Phagwara municipal limits |
| **Traffic Congestion** | `SIMULATED_REPRODUCIBLE` | Seed 42 diurnal profile applied deterministically to edge weights |
| **Commercial Reference** | `EXTERNAL_COMMERCIAL` | Delhivery Maps routing engine (unpolluted parallel evaluation) |
| **Emergency Incidents** | `SIMULATED_DEMO` | Pre-seeded municipal emergency calls (Trauma, Cardiac, Fire) |
| **Emergency Fleet** | `SIMULATED_DEMO` | 8 geolocated municipal emergency response units across Phagwara |

---

## 6. Emergency Dispatch & Multi-Criteria Vehicle Ranking

When an emergency incident is reported, the dispatch service computes:
1. **Physical Eligibility:** Matches incident priority (`P1_CRITICAL`, `P2_HIGH`, `P3_MODERATE`) with vehicle capabilities (`ALS_AMBULANCE`, `BLS_AMBULANCE`, `RAPID_PARAMEDIC`, `FIRE_RESCUE`).
2. **Dynamic Network Distance & ETA:** Executes custom A* on the active road network from every available vehicle's current coordinates to the incident location, taking into account current congestion and active closures.
3. **Vehicle Ranking Score:**
   $$\text{Score} = w_1 \cdot \text{ETA}_{\text{minutes}} + w_2 \cdot \text{Distance}_{\text{km}} + w_3 \cdot \text{Penalty}_{\text{capability}}$$
   The vehicle with the minimum composite score is recommended for 1-click dispatch.

---

## 7. Database Schema & Storage

The system provides dual-mode database support:
- **Production Enterprise Mode:** PostgreSQL 16 + PostGIS extension for spatial queries (`database/schema.sql`).
- **Academic Standalone Mode:** SQLite 3 with SQLAlchemy ORM and in-memory spatial calculations (`backend/app/db/database.py`).

### Key Relational Entities:
1. `vehicles`: Municipal emergency fleet state (coordinates, type, status, equipment).
2. `emergency_incidents`: Emergency incident queue (type, severity, priority, coordinates, status).
3. `dispatch_assignments`: Active and historical dispatch logs linking vehicles to incidents with assigned routes and ETAs.
4. `route_history`: Route audit trail including node sequences, physical distance, estimated time, and algorithm used.
5. `road_closures`: Active municipal road blockages and incident hazards.
6. `algorithm_benchmarks`: Recorded benchmarks for audit and SIH evaluation.

---

## 8. Frontend Command Interface

The frontend is a single-page web application featuring:
- **Live Ops Dashboard:** Key emergency metrics, active incident log, real-time vehicle fleet status, and synchronized Leaflet map.
- **Route Planner:** Point-to-point coordinate selection, side-by-side comparison of all 4 custom search algorithms alongside Delhivery commercial routing.
- **Algorithm Analytics:** Interactive Recharts charts displaying execution time (ms), nodes explored, total distance, and travel time across scenarios.
- **Traffic Intelligence Monitor:** Spatial heatmaps and road status badges with provenance labels (`LIVE`, `SIMULATED`, `UNAVAILABLE`).
- **Traffic Simulator:** Interactive road closure injector allowing the user to sever GT Road segments and view instantaneous dynamic rerouting.
- **Emergency Dispatch Console:** Live incident queue, automated nearest eligible vehicle ranking, and 1-click assignment.
- **System Diagnostics:** Backend health checks, PostGIS schema details, OSM graph topology statistics, and system reset controls.
- **Judge Demonstration Modal:** 12-step guided interactive walkthrough designed for hackathon judges and evaluators.

