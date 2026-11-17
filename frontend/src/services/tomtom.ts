/**
 * Secure TomTom Live Traffic & Mapping Platform Service
 *
 * Enterprise Security Notice:
 * API credentials and secrets are NEVER stored in browser localStorage or transmitted in
 * client-side query parameters. All traffic flow overlays, incident alerts, raster base maps,
 * POI searches, and segment telemetry are securely reverse-proxied through the FastAPI backend
 * (/api/v1/traffic/...) with zero client-side credential exposure.
 */

import { GeocodeResult } from '../types';
import { API_ORIGIN } from './api';

export interface TomTomFlowSegment {
  currentSpeed: number;
  freeFlowSpeed: number;
  currentTravelTime: number;
  freeFlowTravelTime: number;
  confidence: number;
  roadClosure: boolean;
  delaySeconds: number;
  congestionPercent: number;
  coordinates: [number, number][];
}

export interface TomTomIncident {
  id: string;
  type: string;
  description: string;
  iconCategory: number;
  categoryName: string;
  magnitudeOfDelay: number;
  delaySeconds: number;
  from?: string;
  to?: string;
  lengthMeters?: number;
  startTime?: string;
  endTime?: string;
  coordinates?: [number, number][];
}

// Cached server telemetry configuration status
let isServerConfigured: boolean = false;
let hasCheckedStatus: boolean = false;

// Initialize telemetry status in background
const checkInitialStatus = async () => {
  try {
    const res = await fetch(`${API_ORIGIN}/api/v1/traffic/telemetry-status`);
    if (res.ok) {
      const data = await res.json();
      isServerConfigured = Boolean(data.configured);
      hasCheckedStatus = true;
      window.dispatchEvent(new CustomEvent('tomtom_key_updated', { detail: { configured: isServerConfigured } }));
    }
  } catch (err) {
    console.warn('Could not fetch traffic telemetry status:', err);
  }
};
checkInitialStatus();

export const tomtomService = {
  /**
   * Checks whether the backend server has an active TomTom API key configured.
   */
  isConfigured(): boolean {
    return isServerConfigured;
  },

  /**
   * Refreshes telemetry configuration status from the backend proxy.
   */
  async fetchStatus(): Promise<boolean> {
    try {
      const res = await fetch(`${API_ORIGIN}/api/v1/traffic/telemetry-status`);
      if (res.ok) {
        const data = await res.json();
        isServerConfigured = Boolean(data.configured);
        hasCheckedStatus = true;
        window.dispatchEvent(new CustomEvent('tomtom_key_updated', { detail: { configured: isServerConfigured } }));
        return isServerConfigured;
      }
    } catch (err) {
      console.warn('Traffic telemetry status check failed:', err);
    }
    return false;
  },

  /**
   * Real-time Traffic Flow tile URL reverse-proxied via backend server.
   * Style: relative0 (green = free flow, yellow = delay, red = congestion)
   */
  getTrafficFlowTileUrl(): string {
    return `${API_ORIGIN}/api/v1/traffic/tiles/flow/{z}/{x}/{y}.png`;
  },

  /**
   * Real-time Traffic Incidents tile URL reverse-proxied via backend server.
   */
  getTrafficIncidentsTileUrl(): string {
    return `${API_ORIGIN}/api/v1/traffic/tiles/incidents/{z}/{x}/{y}.png`;
  },

  /**
   * TomTom Basic Light vector-rendered raster tile URL reverse-proxied via backend server.
   */
  getTomTomLightTileUrl(): string {
    return `${API_ORIGIN}/api/v1/traffic/tiles/light/{z}/{x}/{y}.png`;
  },

  /**
   * TomTom Basic Night / Dark mode raster tile URL reverse-proxied via backend server.
   */
  getTomTomNightTileUrl(): string {
    return `${API_ORIGIN}/api/v1/traffic/tiles/night/{z}/{x}/{y}.png`;
  },

  /**
   * TomTom Satellite imagery raster tile URL reverse-proxied via backend server.
   */
  getTomTomSatelliteTileUrl(): string {
    return `${API_ORIGIN}/api/v1/traffic/tiles/sat/{z}/{x}/{y}.png`;
  },

  /**
   * Real-Time Fuzzy Search & Hospital / Landmark Autocomplete
   * Reverse-proxied via backend /api/v1/traffic/search with zero API key exposure.
   */
  async searchPlaces(query: string, limit: number = 6): Promise<GeocodeResult[]> {
    const trimmed = query.trim();
    if (!trimmed) return [];

    try {
      const url = `${API_ORIGIN}/api/v1/traffic/search?query=${encodeURIComponent(trimmed)}&limit=${limit}`;
      const res = await fetch(url);
      if (!res.ok) return [];

      const results = await res.json();
      if (!Array.isArray(results)) return [];

      return results.map((item: any) => {
        const poiName = item.poi?.name;
        const freeform = item.address?.freeformAddress || '';
        const name = poiName ? `${poiName} (${freeform})` : freeform || trimmed;

        return {
          place_id: item.id || `tomtom_${Math.random()}`,
          display_name: name,
          formatted_address: freeform || name,
          latitude: item.position.lat,
          longitude: item.position.lon,
          confidence: item.score ? Math.min(1.0, item.score / 10) : 0.9,
          provider: 'TomTom Search',
        };
      });
    } catch (err) {
      console.warn('TomTom search request failed:', err);
      return [];
    }
  },

  /**
   * Live Traffic Flow Segment Data Inspector
   * Fetches real-time speed, free-flow speed, travel times, and road closure flag for any point.
   */
  async getFlowSegmentData(lat: number, lon: number): Promise<TomTomFlowSegment | null> {
    try {
      const url = `${API_ORIGIN}/api/v1/traffic/flow-segment?lat=${lat}&lon=${lon}`;
      const res = await fetch(url);
      if (!res.ok) return null;

      const data = await res.json();
      const flow = data?.flowSegmentData;
      if (!flow) return null;

      const currentSpeed = Math.round(flow.currentSpeed ?? 0);
      const freeFlowSpeed = Math.max(1, Math.round(flow.freeFlowSpeed ?? 1));
      const currentTravelTime = Math.round(flow.currentTravelTime ?? 0);
      const freeFlowTravelTime = Math.round(flow.freeFlowTravelTime ?? 0);
      const delaySeconds = Math.max(0, currentTravelTime - freeFlowTravelTime);

      const congestionRatio = Math.max(0, 1 - currentSpeed / freeFlowSpeed);
      const congestionPercent = Math.min(100, Math.round(congestionRatio * 100));

      const rawCoords = flow.coordinates?.coordinate || [];
      const coordinates: [number, number][] = rawCoords.map((c: any) => [c.latitude, c.longitude]);

      return {
        currentSpeed,
        freeFlowSpeed,
        currentTravelTime,
        freeFlowTravelTime,
        confidence: flow.confidence ?? 1.0,
        roadClosure: Boolean(flow.roadClosure),
        delaySeconds,
        congestionPercent,
        coordinates,
      };
    } catch (err) {
      console.warn('Traffic Flow Segment request failed:', err);
      return null;
    }
  },

  /**
   * Live Traffic Incident Details & Road Closure Feed
   * Reverse-proxied via backend /api/v1/traffic/incident-details.
   */
  async getIncidentDetails(): Promise<TomTomIncident[]> {
    try {
      const url = `${API_ORIGIN}/api/v1/traffic/incident-details`;
      const res = await fetch(url);
      if (!res.ok) return [];

      const rawIncidents = await res.json();
      if (!Array.isArray(rawIncidents)) return [];

      const iconCategoryMap: Record<number, string> = {
        0: 'Unknown Incident',
        1: 'Accident',
        2: 'Fog / Poor Visibility',
        3: 'Dangerous Conditions',
        4: 'Heavy Rain',
        5: 'Ice / Slippery Surface',
        6: 'Traffic Jam',
        7: 'Lane Closed',
        8: 'Road Closed',
        9: 'Road Works / Construction',
        10: 'High Winds',
        11: 'Flooding',
        14: 'Broken Down Vehicle',
      };

      return rawIncidents.map((inc: any) => {
        const props = inc.properties || {};
        const cat = props.iconCategory ?? 0;
        const catName = iconCategoryMap[cat] || 'Road Obstruction';
        const eventDesc = props.events?.[0]?.description || catName;

        let coords: [number, number][] = [];
        if (inc.geometry?.type === 'LineString' && Array.isArray(inc.geometry.coordinates)) {
          coords = inc.geometry.coordinates.map((pt: [number, number]) => [pt[1], pt[0]]);
        }

        return {
          id: props.id || `inc_${Math.random()}`,
          type: inc.type || 'Feature',
          description: eventDesc,
          iconCategory: cat,
          categoryName: catName,
          magnitudeOfDelay: props.magnitudeOfDelay ?? 0,
          delaySeconds: props.delay ?? 0,
          from: props.from,
          to: props.to,
          lengthMeters: props.length,
          startTime: props.startTime,
          endTime: props.endTime,
          coordinates: coords,
        };
      });
    } catch (err) {
      console.warn('Traffic Incident Details request failed:', err);
      return [];
    }
  },

  /**
   * Securely saves and verifies the TomTom API key on the backend server.
   * Key is stored in backend .env and NEVER saved in client storage or returned.
   */
  async saveServerKey(key: string): Promise<{ success: boolean; message: string }> {
    const trimmed = key.trim();
    if (!trimmed) {
      return { success: false, message: 'API key cannot be empty.' };
    }
    try {
      const res = await fetch(`${API_ORIGIN}/api/v1/traffic/set-key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ api_key: trimmed }),
      });
      const data = await res.json();
      if (res.ok && data.success) {
        isServerConfigured = true;
        window.dispatchEvent(new CustomEvent('tomtom_key_updated', { detail: { configured: true } }));
        return { success: true, message: data.message || 'Key securely verified and stored in server environment.' };
      }
      return { success: false, message: data.detail || data.message || 'Key verification failed.' };
    } catch (err: any) {
      return { success: false, message: err?.message || 'Failed to connect to backend server.' };
    }
  },

  /**
   * Removes the TomTom API key from backend server environment.
   */
  async removeServerKey(): Promise<{ success: boolean; message: string }> {
    try {
      const res = await fetch(`${API_ORIGIN}/api/v1/traffic/remove-key`, { method: 'POST' });
      const data = await res.json();
      if (res.ok) {
        isServerConfigured = false;
        window.dispatchEvent(new CustomEvent('tomtom_key_updated', { detail: { configured: false } }));
        return { success: true, message: data.message || 'Key removed from server.' };
      }
      return { success: false, message: 'Failed to remove key from server.' };
    } catch (err: any) {
      return { success: false, message: err?.message || 'Server connection error.' };
    }
  },
};
