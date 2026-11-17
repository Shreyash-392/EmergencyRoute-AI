import axios from 'axios';
import {
  AlgorithmComparisonSummary,
  AlgorithmResult,
  DelhiveryRouteResponse,
  DispatchExecutionResponse,
  EmergencyIncident,
  GeocodeResult,
  MapTileConfig,
  OSRMRouteResponse,
  RerouteResponse,
  RoutingObjective,
  SystemHealth,
  Vehicle,
  VehicleRankingResponse,
} from '../types';

const API_BASE = '/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const api = {
  // System Diagnostics
  getHealth: async (): Promise<SystemHealth> => {
    const res = await apiClient.get<SystemHealth>('/health');
    return res.data;
  },

  getMapConfig: async (): Promise<MapTileConfig> => {
    const res = await apiClient.get<MapTileConfig>('/map/config');
    return res.data;
  },

  searchLocations: async (query: string, limit = 5): Promise<GeocodeResult[]> => {
    const res = await apiClient.get<{ results: GeocodeResult[] }>('/map/locations/search', {
      params: { q: query, limit },
    });
    return res.data.results;
  },

  getRoadStatistics: async (): Promise<any> => {
    const res = await apiClient.get('/roads/statistics');
    return res.data;
  },

  // Routing & Algorithms
  calculateOptimalRoute: async (payload: {
    origin_lat?: number;
    origin_lng?: number;
    dest_lat?: number;
    dest_lng?: number;
    source_node?: number;
    target_node?: number;
    objective?: RoutingObjective;
    scenario_id?: string;
  }): Promise<AlgorithmResult> => {
    const res = await apiClient.post<AlgorithmResult>('/routes/optimal', payload);
    return res.data;
  },

  compareRoutes: async (payload: {
    origin_lat?: number;
    origin_lng?: number;
    dest_lat?: number;
    dest_lng?: number;
    source_node?: number;
    target_node?: number;
    objective?: RoutingObjective;
    scenario_id?: string;
  }): Promise<AlgorithmComparisonSummary> => {
    const res = await apiClient.post<AlgorithmComparisonSummary>('/routes/compare', payload);
    return res.data;
  },

  dynamicReroute: async (payload: {
    route_id: string;
    current_route: AlgorithmResult;
    new_closures?: any[];
    new_traffic_observations?: any[];
    min_improvement_threshold_pct?: number;
    force_recalculate?: boolean;
  }): Promise<RerouteResponse> => {
    const res = await apiClient.post<RerouteResponse>('/routes/reroute', payload);
    return res.data;
  },

  getCommercialReferenceRoute: async (payload: {
    origin_lat: number;
    origin_lng: number;
    dest_lat: number;
    dest_lng: number;
  }): Promise<DelhiveryRouteResponse> => {
    const res = await apiClient.post<DelhiveryRouteResponse>('/routes/reference', payload);
    return res.data;
  },

  getOSRMRoute: async (
    origin_lat: number,
    origin_lng: number,
    dest_lat: number,
    dest_lng: number
  ): Promise<OSRMRouteResponse> => {
    const res = await apiClient.get<OSRMRouteResponse>('/routes/osrm', {
      params: { origin_lat, origin_lng, dest_lat, dest_lng },
    });
    return res.data;
  },

  // Traffic
  getTraffic: async (scenario?: string): Promise<any> => {
    const res = await apiClient.get('/traffic', { params: { scenario } });
    return res.data;
  },

  simulateTraffic: async (scenario_id: string, extra_factors?: Record<string, number>): Promise<any> => {
    const res = await apiClient.post('/traffic/simulate', {
      scenario_id,
      extra_congestion_factors: extra_factors,
    });
    return res.data;
  },

  manageClosures: async (payload: {
    action: 'add' | 'remove' | 'clear';
    closure_id?: string;
    u?: number;
    v?: number;
    key?: number;
    reason?: string;
    severity?: string;
  }): Promise<any> => {
    const res = await apiClient.post('/traffic/closures', payload);
    return res.data;
  },

  getTrafficProviders: async (): Promise<any[]> => {
    const res = await apiClient.get('/traffic/providers');
    return res.data;
  },

  getAlgorithmMetrics: async (): Promise<any> => {
    const res = await apiClient.get('/algorithms/metrics');
    return res.data;
  },

  // Emergency Dispatch
  getVehicles: async (): Promise<Vehicle[]> => {
    const res = await apiClient.get<Vehicle[]>('/dispatch/vehicles');
    return res.data;
  },

  getIncidents: async (): Promise<EmergencyIncident[]> => {
    const res = await apiClient.get<EmergencyIncident[]>('/dispatch/incidents');
    return res.data;
  },

  createIncident: async (payload: {
    title: string;
    description?: string;
    incident_type: string;
    priority: string;
    lat: number;
    lng: number;
  }): Promise<EmergencyIncident> => {
    const res = await apiClient.post<EmergencyIncident>('/dispatch/incidents', payload);
    return res.data;
  },

  rankVehicles: async (incident_id: string, scenario_id = 'morning_peak'): Promise<VehicleRankingResponse> => {
    const res = await apiClient.post<VehicleRankingResponse>('/dispatch/rank', null, {
      params: { incident_id, scenario_id },
    });
    return res.data;
  },

  assignVehicle: async (incident_id: string, vehicle_id: string): Promise<DispatchExecutionResponse> => {
    const res = await apiClient.post<DispatchExecutionResponse>('/dispatch/assign', {
      incident_id,
      vehicle_id,
    });
    return res.data;
  },

  // Demonstration Mode
  getDemoBaseline: async (): Promise<any> => {
    const res = await apiClient.get('/demo/baseline');
    return res.data;
  },

  simulateDemoIncident: async (): Promise<any> => {
    const res = await apiClient.post('/demo/simulate-incident');
    return res.data;
  },

  resetDemo: async (): Promise<any> => {
    const res = await apiClient.post('/demo/reset');
    return res.data;
  },

  // Polling Fallback
  pollRecentEvents: async (limit = 20): Promise<any[]> => {
    const res = await apiClient.get('/events/poll', { params: { limit } });
    return res.data;
  },
};
