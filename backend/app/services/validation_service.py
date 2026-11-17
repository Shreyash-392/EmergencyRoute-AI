import logging
from typing import Any, Dict, List
import networkx as nx

logger = logging.getLogger(__name__)


def validate_road_network(graph: nx.MultiDiGraph) -> Dict[str, Any]:
    """
    Performs comprehensive structural, geographic, and connectivity validation
    on the Phagwara road network graph.
    
    Validates:
    - Graph type (must be nx.MultiDiGraph)
    - Node and edge counts
    - Geographic coordinates (lat/lng limits)
    - Road lengths and travel-time attributes
    - Edge keys and parallel road segments
    - One-way directions
    - Geographic bounding box
    - Weakly connected components (WCC)
    - Strongly connected components (SCC)
    - Isolated nodes
    - Largest connected component ratio
    
    Returns a structured dictionary report.
    """
    is_multidigraph = isinstance(graph, nx.MultiDiGraph)
    is_directed = graph.is_directed()

    num_nodes = len(graph.nodes)
    num_edges = len(graph.edges)

    # 1. Geographic Coordinate Bounds
    lats = [data.get("y") for _, data in graph.nodes(data=True) if data.get("y") is not None]
    lngs = [data.get("x") for _, data in graph.nodes(data=True) if data.get("x") is not None]

    if lats and lngs:
        min_lat, max_lat = min(lats), max(lats)
        min_lng, max_lng = min(lngs), max(lngs)
        has_valid_coords = (len(lats) == num_nodes) and (len(lngs) == num_nodes)
    else:
        min_lat, max_lat, min_lng, max_lng = 0.0, 0.0, 0.0, 0.0
        has_valid_coords = False

    # 2. Edge Attributes (lengths, travel times, speeds)
    lengths = []
    travel_times = []
    speeds = []
    missing_length = 0
    missing_travel_time = 0
    observed_speeds_count = 0
    imputed_speeds_count = 0
    oneway_count = 0
    twoway_count = 0

    for u, v, k, data in graph.edges(keys=True, data=True):
        length = data.get("length")
        tt = data.get("travel_time")
        spd = data.get("speed_kph")
        
        if length is not None and length > 0:
            lengths.append(float(length))
        else:
            missing_length += 1
            
        if tt is not None and tt > 0:
            travel_times.append(float(tt))
        else:
            missing_travel_time += 1
            
        if spd is not None:
            speeds.append(float(spd))

        if data.get("has_observed_speed_limit", False):
            observed_speeds_count += 1
        else:
            imputed_speeds_count += 1

        oneway_val = data.get("oneway", False)
        if oneway_val is True or oneway_val == "yes" or oneway_val == "1":
            oneway_count += 1
        else:
            twoway_count += 1

    # 3. Parallel Edges (multiple keys between same u, v)
    node_pairs: Dict[tuple, int] = {}
    for u, v, k in graph.edges(keys=True):
        pair = (u, v)
        node_pairs[pair] = node_pairs.get(pair, 0) + 1

    parallel_edge_count = sum(count for count in node_pairs.values() if count > 1)
    parallel_edge_pairs = sum(1 for count in node_pairs.values() if count > 1)

    # 4. Connectivity Analysis (WCC and SCC)
    wccs = list(nx.weakly_connected_components(graph))
    num_wccs = len(wccs)
    largest_wcc_nodes = len(max(wccs, key=len)) if wccs else 0
    wcc_coverage_ratio = (largest_wcc_nodes / num_nodes) if num_nodes > 0 else 0.0

    sccs = list(nx.strongly_connected_components(graph))
    num_sccs = len(sccs)
    largest_scc_nodes = len(max(sccs, key=len)) if sccs else 0
    scc_coverage_ratio = (largest_scc_nodes / num_nodes) if num_nodes > 0 else 0.0

    # 5. Isolated Nodes (degree 0)
    isolated_nodes = list(nx.isolates(graph))
    isolated_node_count = len(isolated_nodes)

    # 6. Overall Validity Verdict
    is_valid = (
        is_multidigraph
        and is_directed
        and num_nodes > 0
        and num_edges > 0
        and has_valid_coords
        and missing_length == 0
        and missing_travel_time == 0
        and wcc_coverage_ratio >= 0.70  # largest component should cover major urban network
    )

    validation_summary = {
        "status": "PASS" if is_valid else "WARN",
        "is_valid": is_valid,
        "graph_type": type(graph).__name__,
        "is_directed": is_directed,
        "is_multidigraph": is_multidigraph,
        "nodes_count": num_nodes,
        "edges_count": num_edges,
        "geographic_bounds": {
            "min_latitude": round(min_lat, 6),
            "max_latitude": round(max_lat, 6),
            "min_longitude": round(min_lng, 6),
            "max_longitude": round(max_lng, 6),
            "center": {
                "latitude": round((min_lat + max_lat) / 2.0, 6) if lats else 0.0,
                "longitude": round((min_lng + max_lng) / 2.0, 6) if lngs else 0.0,
            }
        },
        "attributes": {
            "total_length_km": round(sum(lengths) / 1000.0, 2),
            "mean_edge_length_meters": round(sum(lengths) / len(lengths), 2) if lengths else 0.0,
            "min_edge_length_meters": round(min(lengths), 2) if lengths else 0.0,
            "max_edge_length_meters": round(max(lengths), 2) if lengths else 0.0,
            "mean_travel_time_seconds": round(sum(travel_times) / len(travel_times), 2) if travel_times else 0.0,
            "mean_speed_kph": round(sum(speeds) / len(speeds), 2) if speeds else 0.0,
            "missing_length_count": missing_length,
            "missing_travel_time_count": missing_travel_time,
            "observed_speed_limit_edges": observed_speeds_count,
            "imputed_speed_limit_edges": imputed_speeds_count,
            "oneway_edges": oneway_count,
            "twoway_edges": twoway_count,
            "parallel_edge_pairs": parallel_edge_pairs,
            "total_parallel_edges": parallel_edge_count,
        },
        "connectivity": {
            "weakly_connected_components": num_wccs,
            "largest_wcc_nodes": largest_wcc_nodes,
            "largest_wcc_percentage": round(wcc_coverage_ratio * 100.0, 2),
            "strongly_connected_components": num_sccs,
            "largest_scc_nodes": largest_scc_nodes,
            "largest_scc_percentage": round(scc_coverage_ratio * 100.0, 2),
            "isolated_nodes_count": isolated_node_count,
        },
        "notes": [
            "Network extracted as directed MultiDiGraph preserving one-ways and parallel edge keys.",
            "Disconnected components are preserved and not pruned automatically, as required.",
            "Speed limits distinguish observed OSM tags from regional highway classification imputation.",
            "Travel times represent baseline free-flow times; live traffic adjustments handled dynamically."
        ]
    }

    return validation_summary

