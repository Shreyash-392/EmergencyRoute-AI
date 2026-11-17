import logging
from typing import List, Optional
from app.integrations.delhivery.client import DelhiveryClient, DelhiveryError
from app.integrations.delhivery.schemas import GeocodeResult, GeocodeSearchResponse

logger = logging.getLogger(__name__)

# Curated reference locations and emergency facilities in Phagwara, Punjab
PHAGWARA_REFERENCE_PLACES = [
    {
        "id": "civil_hospital",
        "name": "Civil Hospital Phagwara",
        "category": "Hospital / Emergency Healthcare",
        "lat": 31.2223,
        "lng": 75.7672,
        "address": "GT Road, Subhash Nagar, Phagwara, Punjab 144401"
    },
    {
        "id": "guru_nanak_hospital",
        "name": "Guru Nanak Bhai Lalo Hospital",
        "category": "Hospital",
        "lat": 31.2201,
        "lng": 75.7820,
        "address": "Banga Road, Phagwara, Punjab 144401"
    },
    {
        "id": "railway_station",
        "name": "Phagwara Junction Railway Station",
        "category": "Transit Hub",
        "lat": 31.2185,
        "lng": 75.7725,
        "address": "Station Road, Phagwara, Punjab 144401"
    },
    {
        "id": "bus_stand",
        "name": "Phagwara Central Bus Stand",
        "category": "Transit Hub",
        "lat": 31.2215,
        "lng": 75.7738,
        "address": "GT Road, Near City Center, Phagwara, Punjab 144401"
    },
    {
        "id": "lpu_gate",
        "name": "Lovely Professional University (LPU Main Gate)",
        "category": "University / High Traffic",
        "lat": 31.2536,
        "lng": 75.7037,
        "address": "Jalandhar - Delhi G.T. Road, Phagwara, Punjab 144411"
    },
    {
        "id": "hanumangarh_chowk",
        "name": "Hanumangarh Chowk",
        "category": "Major Intersection",
        "lat": 31.2241,
        "lng": 75.7695,
        "address": "Hanumangarh Chowk, Phagwara, Punjab 144401"
    },
    {
        "id": "model_town",
        "name": "Model Town Phagwara",
        "category": "Residential / Commercial Center",
        "lat": 31.2260,
        "lng": 75.7790,
        "address": "Model Town, Phagwara, Punjab 144401"
    },
    {
        "id": "hadiabad",
        "name": "Hadiabad Market Chowk",
        "category": "Commercial Area",
        "lat": 31.2140,
        "lng": 75.7480,
        "address": "Hadiabad, Phagwara, Punjab 144402"
    },
    {
        "id": "nh44_bypass",
        "name": "Phagwara Bypass Chowk (NH44 / GT Road)",
        "category": "Highway Interchange",
        "lat": 31.2112,
        "lng": 75.7891,
        "address": "NH44 Highway Bypass, Phagwara, Punjab 144401"
    },
    {
        "id": "satnampura",
        "name": "Satnampura Police Station Area",
        "category": "Civic / Emergency Services",
        "lat": 31.2290,
        "lng": 75.7610,
        "address": "Satnampura, Phagwara, Punjab 144401"
    }
]


class DelhiveryGeocodingService:
    """
    Geocoding service providing address-to-coordinate search and reverse geocoding.
    Uses Delhivery Maps API when configured, with high-accuracy local landmark fallback.
    """

    def __init__(self, client: Optional[DelhiveryClient] = None):
        self.client = client or DelhiveryClient()

    def search_locations(self, query: str, limit: int = 5) -> GeocodeSearchResponse:
        """
        Searches for locations matching the query.
        Falls back to local verified landmarks when Delhivery API key is absent or unreachable.
        """
        query_norm = query.strip()
        if not query_norm:
            return GeocodeSearchResponse(query="", count=0, results=[], provider="none")

        # Try live Delhivery API if configured
        if self.client.is_configured:
            try:
                response = self.client.request(
                    method="GET",
                    endpoint="/geocoding/geocode",
                    params={"q": query_norm, "limit": limit}
                )
                data = response.get("data", response)
                items = data.get("results", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])
                
                results: List[GeocodeResult] = []
                for item in items[:limit]:
                    results.append(
                        GeocodeResult(
                            place_id=str(item.get("id", item.get("place_id", ""))),
                            formatted_address=item.get("address", item.get("formatted_address", query_norm)),
                            display_name=item.get("name", item.get("display_name", query_norm)),
                            latitude=float(item.get("lat", item.get("latitude", 0.0))),
                            longitude=float(item.get("lng", item.get("longitude", 0.0))),
                            confidence=float(item.get("confidence", 0.95)),
                            provider="delhivery",
                            category=item.get("category", "Address"),
                            raw_response=item
                        )
                    )
                if results:
                    return GeocodeSearchResponse(
                        query=query_norm,
                        count=len(results),
                        results=results,
                        provider="delhivery",
                        is_fallback=False
                    )
            except DelhiveryError as e:
                logger.warning(f"Delhivery geocoding call failed ({e}). Falling back to local reference dataset.")

        # Fallback to local landmark directory
        logger.info(f"Using local verified landmark search for query: '{query_norm}'")
        matched = []
        q_lower = query_norm.lower()

        for place in PHAGWARA_REFERENCE_PLACES:
            score = 0.0
            if q_lower in place["name"].lower():
                score = 0.95
            elif q_lower in place["address"].lower():
                score = 0.85
            elif any(part in place["name"].lower() for part in q_lower.split()):
                score = 0.70

            if score > 0:
                matched.append((score, place))

        # If no specific match, return empty results honestly rather than guessing
        if not matched and ("phagwara" in q_lower):
            # Only if the user specifically asked for "phagwara" return major landmarks
            matched = [(0.6, p) for p in PHAGWARA_REFERENCE_PLACES[:limit]]

        matched.sort(key=lambda x: x[0], reverse=True)
        fallback_results = [
            GeocodeResult(
                place_id=p["id"],
                formatted_address=p["address"],
                display_name=p["name"],
                latitude=p["lat"],
                longitude=p["lng"],
                confidence=s,
                provider="local_reference_fallback",
                category=p["category"],
            )
            for s, p in matched[:limit]
        ]

        return GeocodeSearchResponse(
            query=query_norm,
            count=len(fallback_results),
            results=fallback_results,
            provider="local_reference_fallback",
            is_fallback=True
        )

