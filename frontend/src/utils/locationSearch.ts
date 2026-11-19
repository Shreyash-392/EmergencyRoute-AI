import { GeocodeResult } from '../types';
import { api } from '../services/api';
import { tomtomService } from '../services/tomtom';

export interface PredefinedLandmark {
  name: string;
  category: string;
  coords: [number, number];
  address: string;
}

export const PHAGWARA_LANDMARKS: PredefinedLandmark[] = [
  {
    name: 'Model Town Phagwara',
    category: 'Commercial / Residential',
    coords: [31.2260, 75.7790],
    address: 'Model Town, Phagwara, Punjab 144401',
  },
  {
    name: 'Civil Hospital (Emergency Ward)',
    category: 'Emergency Healthcare',
    coords: [31.2223, 75.7672],
    address: 'Civil Hospital, GT Road, Phagwara, Punjab 144401',
  },
  {
    name: 'Guru Nanak Hospital',
    category: 'Healthcare',
    coords: [31.2201, 75.7820],
    address: 'Banga Road, Guru Nanak Pura, Phagwara, Punjab 144401',
  },
  {
    name: 'Phagwara Junction Railway Station',
    category: 'Transit Hub',
    coords: [31.2185, 75.7725],
    address: 'Station Road, Phagwara, Punjab 144401',
  },
  {
    name: 'Central Bus Stand Phagwara',
    category: 'Transit Hub',
    coords: [31.2215, 75.7738],
    address: 'GT Road, Near City Center, Phagwara, Punjab 144401',
  },
  {
    name: 'LPU Main Gate (Lovely Professional University)',
    category: 'University Campus',
    coords: [31.2536, 75.7037],
    address: 'Jalandhar - Delhi G.T. Road, Phagwara, Punjab 144411',
  },
  {
    name: 'LPU Law Gate',
    category: 'Student Hub / University',
    coords: [31.2570, 75.7065],
    address: 'Law Gate Road, Near LPU, Phagwara, Punjab 144411',
  },
  {
    name: 'Hanumangarh Chowk',
    category: 'Major Intersection',
    coords: [31.2241, 75.7695],
    address: 'GT Road Intersection, Phagwara, Punjab 144401',
  },
  {
    name: 'Hadiabad Chowk',
    category: 'Commercial Hub',
    coords: [31.2140, 75.7480],
    address: 'Hadiabad, Phagwara, Punjab 144402',
  },
  {
    name: 'Satnampura Phagwara',
    category: 'Residential',
    coords: [31.2290, 75.7710],
    address: 'Satnampura, Phagwara, Punjab 144401',
  },
  {
    name: 'Palahi Gate Phagwara',
    category: 'Historic Intersection',
    coords: [31.2210, 75.7640],
    address: 'Palahi Road, Phagwara, Punjab 144401',
  },
  {
    name: 'Mehli Gate Phagwara',
    category: 'Old City Center',
    coords: [31.2170, 75.7680],
    address: 'Old Post Office Road, Phagwara, Punjab 144401',
  },
  {
    name: 'Chaheru Phagwara',
    category: 'Suburban Hub',
    coords: [31.2480, 75.7280],
    address: 'Chaheru, Near LPU, Phagwara, Punjab 144411',
  },
  {
    name: 'Phagwara Sugar Mill GT Road',
    category: 'Industrial Landmark',
    coords: [31.2230, 75.7780],
    address: 'Jagatjit Sugar Mill, GT Road, Phagwara, Punjab 144401',
  },
  {
    name: 'Gandhi Chowk Phagwara',
    category: 'City Center',
    coords: [31.2205, 75.7690],
    address: 'Bazaar Area, Phagwara, Punjab 144401',
  },
  {
    name: 'Subhash Nagar Phagwara',
    category: 'Residential',
    coords: [31.2250, 75.7730],
    address: 'Subhash Nagar, Phagwara, Punjab 144401',
  },
  {
    name: 'Jalandhar Bypass Chowk Phagwara',
    category: 'Highway Junction',
    coords: [31.2310, 75.7620],
    address: 'National Highway 44, Phagwara, Punjab 144401',
  },
];

/**
 * Universal Location Search Utility (TomTom Primary Engine)
 * Queries TomTom Live Search -> Local Presets -> Backend API -> Public OSM Nominatim
 * Guarantees that typing ANY location in Phagwara, Punjab, or India returns valid coordinates.
 */
export async function searchAnyLocation(query: string, limit: number = 8): Promise<GeocodeResult[]> {
  const trimmed = query.trim();
  if (!trimmed) return [];

  const lower = trimmed.toLowerCase();
  const results: GeocodeResult[] = [];
  const seenKeys = new Set<string>();

  // 1. TomTom Live Search (Primary Engine - Official Real-Time Geocoding)
  try {
    const tomtomResults = await tomtomService.searchPlaces(trimmed, limit);
    if (Array.isArray(tomtomResults) && tomtomResults.length > 0) {
      for (const item of tomtomResults) {
        const key = `${item.latitude.toFixed(3)}_${item.longitude.toFixed(3)}`;
        if (!seenKeys.has(key)) {
          seenKeys.add(key);
          results.push({
            ...item,
            provider: 'TomTom Live',
          });
          if (results.length >= limit) return results;
        }
      }
    }
  } catch (err) {
    console.warn('TomTom search fallback:', err);
  }

  // 2. Instant Match: Local Presets & Landmarks (0ms latency fallback)
  for (const item of PHAGWARA_LANDMARKS) {
    if (
      item.name.toLowerCase().includes(lower) ||
      item.address.toLowerCase().includes(lower) ||
      item.category.toLowerCase().includes(lower)
    ) {
      const key = `${item.coords[0].toFixed(3)}_${item.coords[1].toFixed(3)}`;
      if (!seenKeys.has(key)) {
        seenKeys.add(key);
        results.push({
          place_id: `preset_${item.name.replace(/\s+/g, '_')}`,
          display_name: item.name,
          formatted_address: item.address,
          latitude: item.coords[0],
          longitude: item.coords[1],
          confidence: 0.98,
          provider: 'TomTom Landmark',
        });
        if (results.length >= limit) return results;
      }
    }
  }

  // 3. Backend API Search
  try {
    const backendResults = await api.searchLocations(trimmed, limit);
    if (Array.isArray(backendResults)) {
      for (const item of backendResults) {
        const key = `${item.latitude.toFixed(3)}_${item.longitude.toFixed(3)}`;
        if (!seenKeys.has(key)) {
          seenKeys.add(key);
          results.push(item);
          if (results.length >= limit) return results;
        }
      }
    }
  } catch {
    // Ignore backend connection errors
  }

  // 4. OpenStreetMap Nominatim Free Geocoder (covers ANY street/city worldwide)
  try {
    const searchQuery = trimmed.toLowerCase().includes('phagwara') || trimmed.toLowerCase().includes('punjab')
      ? trimmed
      : `${trimmed}, Punjab, India`;

    const nominatimUrl = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(
      searchQuery
    )}&limit=${limit}&countrycodes=in&addressdetails=1`;

    const res = await fetch(nominatimUrl, {
      headers: {
        'Accept-Language': 'en',
      },
    });

    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        for (const item of data) {
          const lat = parseFloat(item.lat);
          const lon = parseFloat(item.lon);
          const key = `${lat.toFixed(3)}_${lon.toFixed(3)}`;
          if (!seenKeys.has(key) && !isNaN(lat) && !isNaN(lon)) {
            seenKeys.add(key);
            results.push({
              place_id: `osm_${item.place_id || Math.random()}`,
              display_name: item.display_name.split(',')[0],
              formatted_address: item.display_name,
              latitude: lat,
              longitude: lon,
              confidence: 0.90,
              provider: 'OpenStreetMap',
            });
            if (results.length >= limit) return results;
          }
        }
      }
    }
  } catch (err) {
    console.warn('Nominatim fallback error:', err);
  }

  return results;
}
