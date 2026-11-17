-- ==============================================================================
-- EmergencyRoute AI - PostgreSQL + PostGIS Database Schema
-- Production DDL for Phagwara Emergency Transportation Platform
-- ==============================================================================

-- 1. Enable PostGIS Extension
CREATE EXTENSION IF NOT EXISTS postgis;

-- 2. Emergency Vehicles Fleet Table
CREATE TABLE IF NOT EXISTS vehicles (
    vehicle_id VARCHAR(64) PRIMARY KEY,
    call_sign VARCHAR(64) NOT NULL,
    vehicle_type VARCHAR(32) NOT NULL CHECK (vehicle_type IN ('ambulance', 'fire_engine', 'police')),
    status VARCHAR(32) NOT NULL DEFAULT 'available' CHECK (status IN ('available', 'dispatched', 'in_transit', 'maintenance')),
    current_lat DOUBLE PRECISION NOT NULL,
    current_lng DOUBLE PRECISION NOT NULL,
    base_station VARCHAR(128) NOT NULL,
    assigned_incident_id VARCHAR(64),
    last_updated TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    geom GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(current_lng, current_lat), 4326)) STORED
);

-- 3. Emergency Incidents Table
CREATE TABLE IF NOT EXISTS emergency_incidents (
    incident_id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(128) NOT NULL,
    description TEXT,
    incident_type VARCHAR(64) NOT NULL CHECK (incident_type IN ('cardiac_arrest', 'road_accident', 'fire_emergency', 'crime_in_progress', 'general_medical')),
    priority VARCHAR(16) NOT NULL CHECK (priority IN ('critical', 'high', 'medium', 'low')),
    lat DOUBLE PRECISION NOT NULL,
    lng DOUBLE PRECISION NOT NULL,
    status VARCHAR(32) NOT NULL DEFAULT 'reported' CHECK (status IN ('reported', 'dispatched', 'in_progress', 'resolved', 'cancelled')),
    reported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    assigned_vehicle_id VARCHAR(64) REFERENCES vehicles(vehicle_id) ON DELETE SET NULL,
    resolved_at TIMESTAMPTZ,
    geom GEOMETRY(Point, 4326) GENERATED ALWAYS AS (ST_SetSRID(ST_MakePoint(lng, lat), 4326)) STORED
);

-- 4. Dispatch Assignments Table
CREATE TABLE IF NOT EXISTS dispatch_assignments (
    assignment_id VARCHAR(64) PRIMARY KEY,
    incident_id VARCHAR(64) NOT NULL REFERENCES emergency_incidents(incident_id) ON DELETE CASCADE,
    vehicle_id VARCHAR(64) NOT NULL REFERENCES vehicles(vehicle_id) ON DELETE CASCADE,
    assigned_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estimated_eta_seconds DOUBLE PRECISION NOT NULL,
    estimated_distance_km DOUBLE PRECISION NOT NULL,
    algorithm_used VARCHAR(32) NOT NULL DEFAULT 'A_Star',
    route_id VARCHAR(64),
    status VARCHAR(32) NOT NULL DEFAULT 'active' CHECK (status IN ('active', 'completed', 'rerouted', 'cancelled'))
);

-- 5. Route Audit History Table
CREATE TABLE IF NOT EXISTS route_history (
    route_id VARCHAR(64) PRIMARY KEY,
    source_node BIGINT NOT NULL,
    target_node BIGINT NOT NULL,
    algorithm_name VARCHAR(64) NOT NULL,
    routing_objective VARCHAR(32) NOT NULL,
    traffic_scenario VARCHAR(64) NOT NULL,
    distance_meters DOUBLE PRECISION NOT NULL,
    travel_time_seconds DOUBLE PRECISION NOT NULL,
    nodes_explored INTEGER NOT NULL,
    execution_time_ms DOUBLE PRECISION NOT NULL,
    is_optimal BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- 6. Road Closures & Blockages Table
CREATE TABLE IF NOT EXISTS road_closures (
    closure_id VARCHAR(64) PRIMARY KEY,
    u BIGINT NOT NULL,
    v BIGINT NOT NULL,
    key_id INTEGER NOT NULL DEFAULT 0,
    reason VARCHAR(256) NOT NULL,
    severity VARCHAR(32) NOT NULL DEFAULT 'impassable',
    reported_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- 7. Algorithm Benchmark Trials Table
CREATE TABLE IF NOT EXISTS algorithm_benchmarks (
    benchmark_id SERIAL PRIMARY KEY,
    corridor_name VARCHAR(128) NOT NULL,
    scenario_id VARCHAR(64) NOT NULL,
    algorithm_name VARCHAR(64) NOT NULL,
    nodes_explored INTEGER NOT NULL,
    path_distance_km DOUBLE PRECISION NOT NULL,
    travel_time_minutes DOUBLE PRECISION NOT NULL,
    mean_execution_time_ms DOUBLE PRECISION NOT NULL,
    recorded_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Spatial Indices for fast GIS querying
CREATE INDEX IF NOT EXISTS idx_vehicles_geom ON vehicles USING GIST(geom);
CREATE INDEX IF NOT EXISTS idx_incidents_geom ON emergency_incidents USING GIST(geom);

