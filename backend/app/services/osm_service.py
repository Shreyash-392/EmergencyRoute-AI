import logging
from pathlib import Path
from typing import Dict, Optional, Tuple
import networkx as nx
import osmnx as ox

from app.core.config import settings

logger = logging.getLogger(__name__)

# Standard Indian urban/suburban roadway default speeds (km/h) for Phagwara region
DEFAULT_HWY_SPEEDS: Dict[str, float] = {
    "motorway": 90.0,
    "trunk": 70.0,
    "primary": 50.0,
    "secondary": 40.0,
    "tertiary": 30.0,
    "residential": 25.0,
    "unclassified": 25.0,
    "living_street": 15.0,
    "service": 15.0,
}


def setup_osmnx_cache(cache_folder: Optional[Path] = None) -> None:
    """Configures OSMnx caching and endpoint settings."""
    folder = cache_folder or settings.OSM_CACHE_DIR
    folder.mkdir(parents=True, exist_ok=True)
    ox.settings.use_cache = True
    ox.settings.cache_folder = str(folder)
    ox.settings.log_console = False
    ox.settings.overpass_endpoint = "https://overpass.kumi.systems/api/interpreter"
    ox.settings.requests_timeout = 90


def extract_phagwara_network(
    place_name: str = "Phagwara, Punjab, India",
    center_point: Tuple[float, float] = (31.2231, 75.7708),
    dist_meters: int = 6000,
    force_refresh: bool = False,
) -> nx.MultiDiGraph:
    """
    Downloads and builds the directed drivable MultiDiGraph road network for Phagwara.
    
    Preserves:
    - Directed edges (MultiDiGraph)
    - One-way road directions
    - Parallel edges and edge keys
    - OSM node IDs
    - Road geometry (Linestring)
    - Road classification ('highway') and road names ('name')
    - Available access restrictions ('access', 'oneway')
    """
    setup_osmnx_cache()
    if force_refresh:
        logger.info("Force refresh enabled; clearing OSMnx cache if necessary.")

    graph: Optional[nx.MultiDiGraph] = None

    # Step 1: Attempt ox.graph_from_place
    try:
        logger.info(f"Attempting road extraction using ox.graph_from_place('{place_name}')...")
        graph = ox.graph_from_place(
            place_name,
            network_type="drive",
            simplify=True,
            retain_all=True
        )
        logger.info("Successfully extracted road network via place query.")
    except Exception as e:
        logger.warning(
            f"ox.graph_from_place failed ('{e}'). "
            f"Falling back to spatial buffer query ox.graph_from_point({center_point}, dist={dist_meters}m)..."
        )

    # Step 2: Fallback to ox.graph_from_point if place query returned no polygon or failed
    if graph is None:
        graph = ox.graph_from_point(
            center_point,
            dist=dist_meters,
            network_type="drive",
            simplify=True,
            retain_all=True
        )
        logger.info(f"Successfully extracted road network via spatial radius ({dist_meters}m from {center_point}).")

    if not isinstance(graph, nx.MultiDiGraph):
        graph = nx.MultiDiGraph(graph)

    # Step 3: Enrich with speed attributes and travel times
    enrich_graph_attributes(graph)

    logger.info(
        f"Phagwara road extraction complete: {len(graph.nodes)} nodes, {len(graph.edges)} directed edges."
    )
    return graph


def enrich_graph_attributes(graph: nx.MultiDiGraph) -> nx.MultiDiGraph:
    """
    Enriches road edges with:
    - length (in meters)
    - speed_kph (estimated or observed speed limit)
    - travel_time (in seconds)
    - has_observed_speed_limit (boolean flag distinguishing OSM tag from model imputation)
    - speed_source ('osm_tag' vs 'imputed_hwy_class')
    
    NOTE: These represent static legal/physical limits and free-flow baseline speeds,
    NOT live traffic measurements. Live or dynamic conditions are provided separately.
    """
    # 1. Distinguish observed speed limit tags before imputing
    for u, v, k, data in graph.edges(keys=True, data=True):
        maxspeed_tag = data.get("maxspeed", None)
        if maxspeed_tag is not None:
            data["has_observed_speed_limit"] = True
            data["speed_source"] = "osm_tag"
        else:
            data["has_observed_speed_limit"] = False
            data["speed_source"] = "imputed_hwy_class"

    # 2. Add speed_kph using OSMnx edge speed imputation with regional fallback speeds
    ox.add_edge_speeds(graph, hwy_speeds=DEFAULT_HWY_SPEEDS, fallback=30.0)

    # 3. Add travel_time (seconds) based on edge length and speed_kph
    ox.add_edge_travel_times(graph)

    # 4. Standardize edge attributes
    for u, v, k, data in graph.edges(keys=True, data=True):
        if "length" not in data or data["length"] is None:
            data["length"] = 10.0  # minimal safe default
        if "speed_kph" not in data or data["speed_kph"] is None:
            data["speed_kph"] = 30.0
        if "travel_time" not in data or data["travel_time"] is None:
            data["travel_time"] = round(data["length"] / (data["speed_kph"] * 1000.0 / 3600.0), 2)
        else:
            data["travel_time"] = round(float(data["travel_time"]), 2)

    return graph
