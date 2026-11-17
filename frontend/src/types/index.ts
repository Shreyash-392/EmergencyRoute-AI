export type RoutingObjective = 'distance' | 'travel_time' | 'traffic_aware';

export interface PathSegment {
  u: number;
  v: number;
  key: number;
  length_meters: number;
  travel_time_seconds: number;
  speed_kph: number;
  name: string;
  highway: string;
  cost: number;
  geometry_coords?: [number, number][];
}

export interface AlgorithmResult {
  algorithm_name: string;
  source_node: number;
  target_node: number;
  success: boolean;
  node_path: number[];
  edge_path: PathSegment[];
  path_distance_meters: number;
  path_distance_km: number;
  estimated_travel_time_seconds: number;
  estimated_travel_time_minutes: number;
  weighted_path_cost: number;
  nodes_explored: number;
  execution_time_ms: number;
  routing_objective: RoutingObjective;
  is_optimal: boolean;
  coordinates: [number, number][];
  error_message?: string;
}

export interface AlgorithmComparisonSummary {
  source_node: number;
  target_node: number;
  routing_objective: RoutingObjective;
  traffic_scenario: string;
  results: Record<string, AlgorithmResult>;
  fastest_execution_algorithm: string;
  least_nodes_explored_algorithm: string;
  lowest_cost_algorithm: string;
  shortest_distance_algorithm: string;
  lowest_travel_time_algorithm: string;
}

export interface Vehicle {
  vehicle_id: string;
  call_sign: string;
  vehicle_type: 'ambulance' | 'fire_engine' | 'police';
  status: 'available' | 'dispatched' | 'in_transit' | 'maintenance';
  current_lat: number;
  current_lng: number;
  base_station: string;
  assigned_incident_id?: string;
  last_updated?: string;
}

export interface EmergencyIncident {
  incident_id: string;
  title: string;
  description?: string;
  incident_type: 'cardiac_arrest' | 'road_accident' | 'fire_emergency' | 'crime_in_progress' | 'general_medical';
  priority: 'critical' | 'high' | 'medium' | 'low';
  lat: number;
  lng: number;
  status: 'reported' | 'dispatched' | 'in_progress' | 'resolved' | 'cancelled';
  reported_at?: string;
  assigned_vehicle_id?: string;
  resolved_at?: string;
}

export interface VehicleRankingCandidate {
  vehicle: Vehicle;
  estimated_travel_time_seconds: number;
  estimated_travel_time_minutes: number;
  distance_km: number;
  suitability_score: number;
  rank: number;
  route_preview?: AlgorithmResult;
}

export interface VehicleRankingResponse {
  incident: EmergencyIncident;
  candidates_count: number;
  ranked_candidates: VehicleRankingCandidate[];
}

export interface DispatchExecutionResponse {
  success: boolean;
  assignment_id: string;
  incident_id: string;
  vehicle_id: string;
  assigned_at: string;
  estimated_eta_minutes: number;
  distance_km: number;
  dispatch_route: AlgorithmResult;
  message: string;
}

export interface ActiveRoadClosure {
  closure_id: string;
  u: number;
  v: number;
  key: number;
  reason: string;
  severity: string;
  reported_at?: string;
  active: boolean;
}

export interface TrafficScenario {
  scenario_id: string;
  name: string;
  description: string;
  time_of_day: string;
  affected_corridors: string[];
  global_congestion_factor: number;
  closures_count: number;
}

export interface SystemHealth {
  status: string;
  service: string;
  version: string;
  phase: number;
  city: string;
  graph_loaded: boolean;
  graph_nodes: number;
  graph_edges: number;
  delhivery_configured: boolean;
  traffic_provider_mode: string;
  websocket_active_clients: number;
  algorithms: string[];
}

export interface DelhiveryRouteResponse {
  success: boolean;
  distance_meters: number;
  duration_seconds: number;
  distance_km: number;
  duration_minutes: number;
  traffic_delay_seconds?: number;
  polyline_geometry?: string;
  coordinates?: [number, number][];
  provider: string;
  is_fallback: boolean;
  message?: string;
}

export interface GeocodeResult {
  place_id: string;
  formatted_address: string;
  display_name: string;
  latitude: number;
  longitude: number;
  confidence: number;
  provider: string;
  category?: string;
}

export interface MapTileConfig {
  provider: string;
  tile_url_template: string;
  attribution: string;
  max_zoom: number;
  min_zoom: number;
  subdomains: string[];
  is_commercial: boolean;
}

export interface RerouteResponse {
  reroute_triggered: boolean;
  decision: string;
  reason: string;
  active_route: AlgorithmResult;
  previous_route?: AlgorithmResult;
  comparison?: {
    decision: string;
    old_travel_time_seconds: number;
    new_travel_time_seconds: number;
    time_saved_seconds: number;
    percentage_time_saved: number;
    old_distance_meters: number;
    new_distance_meters: number;
    path_similarity_jaccard: number;
    identical_path: boolean;
    explanation: string;
  };
  validation: {
    is_valid: boolean;
    is_blocked: boolean;
    blocked_edge?: [number, number, number];
    travel_time_increase_percentage: number;
    reason: string;
  };
  event_id?: string;
}

export interface OSRMStep {
  name: string;
  distance_meters: number;
  duration_seconds: number;
  mode?: string;
  maneuver?: any;
  instruction: string;
}

export interface OSRMLeg {
  distance_meters: number;
  duration_seconds: number;
  summary: string;
  steps: OSRMStep[];
}

export interface OSRMRoute {
  distance_meters: number;
  duration_seconds: number;
  distance_km: number;
  duration_minutes: number;
  geometry: any;
  coordinates: [number, number][];
  legs: OSRMLeg[];
  turn_by_turn: string[];
}

export interface OSRMRouteResponse {
  success: boolean;
  provider: string;
  code: string;
  message: string;
  origin: { lat: number; lng: number };
  destination: { lat: number; lng: number };
  distance_km?: number;
  duration_minutes?: number;
  is_live_traffic: boolean;
  disclaimer: string;
  route?: OSRMRoute;
  alternatives_count: number;
  alternatives: OSRMRoute[];
}
