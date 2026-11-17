import logging
from typing import Any, Dict, List, Optional, Tuple
import networkx as nx
import osmnx as ox
from shapely.geometry import LineString

from app.core.graph_loader import load_graph_from_graphml

logger = logging.getLogger(__name__)


class GraphService:
    def __init__(self, graph: Optional[nx.MultiDiGraph] = None):
        self._graph = graph

    @property
    def graph(self) -> nx.MultiDiGraph:
        if self._graph is None:
            self._graph = load_graph_from_graphml()
        return self._graph

    def find_nearest_node(self, lat: float, lng: float) -> int:
        """
        Finds the nearest road network node to a given (latitude, longitude) coordinate.
        """
        G = self.graph
        # OSMnx nearest_nodes expects (X=lon, Y=lat)
        node_id = ox.distance.nearest_nodes(G, X=lng, Y=lat)
        return int(node_id)

    def get_node_coordinates(self, node_id: int) -> Tuple[float, float]:
        """Returns (latitude, longitude) for a given node ID."""
        node_data = self.graph.nodes[node_id]
        return float(node_data["y"]), float(node_data["x"])

    def get_edge_data(self, u: int, v: int, key: int = 0) -> Dict[str, Any]:
        """Returns the attributes of a specific directed edge."""
        return dict(self.graph[u][v][key])

    def calculate_reference_route(
        self,
        origin_lat: float,
        origin_lng: float,
        dest_lat: float,
        dest_lng: float,
        weight: str = "travel_time"
    ) -> Dict[str, Any]:
        """
        Calculates a baseline reference directed route using NetworkX Dijkstra shortest path.
        Validates one-way connectivity and computes path distance, travel time, and coordinates.
        This serves as the authoritative ground truth for Phase 2 algorithm benchmarking.
        """
        G = self.graph
        orig_node = self.find_nearest_node(origin_lat, origin_lng)
        dest_node = self.find_nearest_node(dest_lat, dest_lng)

        orig_coords = self.get_node_coordinates(orig_node)
        dest_coords = self.get_node_coordinates(dest_node)

        if not nx.has_path(G, orig_node, dest_node):
            return {
                "success": False,
                "error": f"No directed path exists between node {orig_node} and node {dest_node} (respecting one-ways).",
                "origin_node": orig_node,
                "dest_node": dest_node,
                "origin_coords": orig_coords,
                "dest_coords": dest_coords,
            }

        node_path = nx.shortest_path(G, orig_node, dest_node, weight=weight)
        
        # Calculate route metrics & assemble path geometry
        total_distance = 0.0
        total_travel_time = 0.0
        route_coordinates: List[List[float]] = []
        edge_segments: List[Dict[str, Any]] = []

        # Add origin node coord
        route_coordinates.append([orig_coords[0], orig_coords[1]])

        for i in range(len(node_path) - 1):
            u = node_path[i]
            v = node_path[i + 1]
            
            # Select edge with minimum weight among parallel edges
            edges = G[u][v]
            best_key = min(edges.keys(), key=lambda k: edges[k].get(weight, float("inf")))
            edge_data = edges[best_key]

            seg_len = float(edge_data.get("length", 0.0))
            seg_time = float(edge_data.get("travel_time", 0.0))
            total_distance += seg_len
            total_travel_time += seg_time

            # If edge has geometry (Shapely LineString), extract all coordinates
            geom = edge_data.get("geometry")
            if geom is not None and isinstance(geom, LineString):
                # Shapely coords are (lon, lat)
                for lon, lat in list(geom.coords)[1:]:
                    route_coordinates.append([lat, lon])
            else:
                target_coord = self.get_node_coordinates(v)
                route_coordinates.append([target_coord[0], target_coord[1]])

            edge_segments.append({
                "from_node": u,
                "to_node": v,
                "key": best_key,
                "name": edge_data.get("name", "Unnamed Road"),
                "highway": edge_data.get("highway", "unclassified"),
                "length_meters": round(seg_len, 2),
                "speed_kph": edge_data.get("speed_kph", 30.0),
                "travel_time_seconds": round(seg_time, 2),
                "speed_source": edge_data.get("speed_source", "imputed_hwy_class"),
            })

        return {
            "success": True,
            "origin_node": orig_node,
            "dest_node": dest_node,
            "origin_coords": {"latitude": orig_coords[0], "longitude": orig_coords[1]},
            "dest_coords": {"latitude": dest_coords[0], "longitude": dest_coords[1]},
            "nodes_count": len(node_path),
            "node_path": node_path,
            "total_distance_meters": round(total_distance, 2),
            "total_distance_km": round(total_distance / 1000.0, 3),
            "total_travel_time_seconds": round(total_travel_time, 2),
            "total_travel_time_minutes": round(total_travel_time / 60.0, 2),
            "route_coordinates": route_coordinates,
            "segments_count": len(edge_segments),
            "segments": edge_segments,
        }

