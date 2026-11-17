import logging
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from shapely.geometry import LineString

from app.algorithms.algorithm_metrics import PathSegment, RoutingObjective
from app.algorithms.heuristic import HeuristicCalculator

logger = logging.getLogger(__name__)


class MultiGraphAdapter:
    """
    Adapter for directed MultiDiGraph road networks.
    
    Provides:
    - Directed successor traversal respecting one-way streets.
    - Optimal parallel edge selection: selects the minimum-cost usable edge among
      parallel edges between node pairs (u, v) while retaining the original edge key.
    - Road closure and availability enforcement.
    - Uniform edge cost evaluation based on the active RoutingObjective.
    - Coordinate lookups and geometry reconstruction for route visualization.
    """

    def __init__(
        self,
        graph: nx.MultiDiGraph,
        closed_edges: Optional[Set[Tuple[int, int, int]]] = None,
        traffic_updates: Optional[Dict[Tuple[int, int, int], Dict[str, Any]]] = None,
    ):
        if not isinstance(graph, nx.MultiDiGraph):
            raise TypeError(f"Expected nx.MultiDiGraph, got {type(graph).__name__}")
        if not graph.is_directed():
            raise ValueError("Road graph must be directed to preserve one-way roads.")

        self.graph = graph
        self.closed_edges: Set[Tuple[int, int, int]] = closed_edges or set()
        self.traffic_updates: Dict[Tuple[int, int, int], Dict[str, Any]] = traffic_updates or {}

        # Pre-cache node coordinates for instant heuristic lookup: node_id -> (lat, lon)
        self.node_coords: Dict[int, Tuple[float, float]] = {}
        for n, data in self.graph.nodes(data=True):
            lat = data.get("y", 0.0)
            lon = data.get("x", 0.0)
            self.node_coords[n] = (float(lat), float(lon))

        # Determine maximum speed bound across traversable edges for admissible heuristic
        self.max_speed_kph = self._calculate_max_speed()
        self.heuristic_calc = HeuristicCalculator(self.node_coords, self.max_speed_kph)

    def _calculate_max_speed(self) -> float:
        """Finds upper bound of speed in network (km/h) for admissible lower-bound heuristic."""
        from app.traffic.traffic_weight_calculator import TrafficWeightCalculator
        max_spd = 0.0
        for _, _, _, data in self.graph.edges(keys=True, data=True):
            spd = float(data.get("speed_kph", 30.0))
            if spd > max_spd:
                max_spd = spd
        # Ensure a mathematically safe bound against any legal or traffic speed cap (120 km/h)
        return max(max_spd, TrafficWeightCalculator.MAX_SPEED_KPH)

    def contains_node(self, node_id: int) -> bool:
        return node_id in self.graph

    def get_node_coords(self, node_id: int) -> Tuple[float, float]:
        return self.node_coords.get(node_id, (0.0, 0.0))

    def is_edge_closed(self, u: int, v: int, key: int) -> bool:
        """Checks if a directed edge is closed (blocked/impassable)."""
        return (u, v, key) in self.closed_edges or (u, v, -1) in self.closed_edges

    def get_edge_cost(
        self,
        u: int,
        v: int,
        key: int,
        edge_data: Dict[str, Any],
        objective: RoutingObjective
    ) -> float:
        """
        Computes non-negative edge cost according to the routing objective:
        - MIN_DISTANCE: length in meters.
        - MIN_TRAVEL_TIME: base legal/free-flow travel time in seconds.
        - TRAFFIC_AWARE: dynamic travel time factoring in congestion/telematics.
        """
        length_m = float(edge_data.get("length", 10.0))

        if objective == RoutingObjective.MIN_DISTANCE:
            return max(0.1, length_m)

        # Check for dynamic traffic updates on this edge
        traffic_info = self.traffic_updates.get((u, v, key))
        if traffic_info and "dynamic_travel_time" in traffic_info:
            dynamic_tt = float(traffic_info["dynamic_travel_time"])
        else:
            dynamic_tt = float(edge_data.get("dynamic_travel_time", edge_data.get("travel_time", 1.0)))

        if objective == RoutingObjective.TRAFFIC_AWARE:
            return max(0.1, dynamic_tt)
        else:
            # MIN_TRAVEL_TIME uses static baseline free-flow travel time
            base_tt = float(edge_data.get("travel_time", dynamic_tt))
            return max(0.1, base_tt)

    def get_successors(
        self,
        u: int,
        objective: RoutingObjective
    ) -> List[Tuple[int, int, float, Dict[str, Any]]]:
        """
        Returns list of directed successors (v, best_key, best_cost, edge_data).
        
        For MultiDiGraph parallel edges between u and v:
        Evaluates all available (non-closed) edges and selects the one with the
        lowest cost for the given objective. The original edge key is retained.
        """
        if u not in self.graph:
            return []

        successors = []
        adj = self.graph.adj.get(u, {})

        for v, parallel_edges in adj.items():
            best_key: Optional[int] = None
            best_cost: float = float("inf")
            best_data: Optional[Dict[str, Any]] = None

            for key, data in parallel_edges.items():
                if self.is_edge_closed(u, v, key):
                    continue

                cost = self.get_edge_cost(u, v, key, data, objective)
                if cost < best_cost:
                    best_cost = cost
                    best_key = key
                    best_data = data

            if best_key is not None and best_data is not None:
                successors.append((v, best_key, best_cost, best_data))

        return successors

    def build_path_segment(
        self,
        u: int,
        v: int,
        key: int,
        objective: RoutingObjective
    ) -> PathSegment:
        """Constructs a PathSegment record with metrics and coordinates."""
        edge_data = dict(self.graph[u][v][key])
        cost = self.get_edge_cost(u, v, key, edge_data, objective)
        
        length_m = float(edge_data.get("length", 10.0))
        speed_kph = float(edge_data.get("dynamic_speed_kph", edge_data.get("speed_kph", 30.0)))
        travel_time_s = float(edge_data.get("dynamic_travel_time", edge_data.get("travel_time", 1.0)))
        
        name = edge_data.get("name", "Unnamed Road")
        if isinstance(name, list):
            name = "/".join(map(str, name))
            
        hwy = edge_data.get("highway", "unclassified")
        if isinstance(hwy, list):
            hwy = hwy[0]

        # Extract edge geometry coordinates [[lat, lon], ...]
        coords: List[List[float]] = []
        geom = edge_data.get("geometry")
        if geom is not None and isinstance(geom, LineString):
            coords = [[lat, lon] for lon, lat in geom.coords]
        else:
            u_coord = self.get_node_coords(u)
            v_coord = self.get_node_coords(v)
            coords = [[u_coord[0], u_coord[1]], [v_coord[0], v_coord[1]]]

        return PathSegment(
            u=u,
            v=v,
            key=key,
            length_meters=round(length_m, 2),
            travel_time_seconds=round(travel_time_s, 2),
            speed_kph=round(speed_kph, 1),
            name=str(name),
            highway=str(hwy),
            cost=round(cost, 3),
            geometry_coords=coords
        )

    def reconstruct_full_path(
        self,
        parent_pointers: Dict[int, Tuple[int, int]],
        source_node: int,
        target_node: int,
        objective: RoutingObjective
    ) -> Tuple[List[int], List[PathSegment], List[List[float]], float, float, float]:
        """
        Reconstructs node path, edge path segments, continuous polyline coordinates,
        total distance, estimated travel time, and weighted cost.
        """
        if target_node not in parent_pointers and target_node != source_node:
            return [], [], [], 0.0, 0.0, 0.0

        # Trace back from target to source
        curr = target_node
        node_path = [curr]
        edge_tuples: List[Tuple[int, int, int]] = []

        while curr != source_node:
            parent, key = parent_pointers[curr]
            edge_tuples.append((parent, curr, key))
            curr = parent
            node_path.append(curr)

        node_path.reverse()
        edge_tuples.reverse()

        edge_segments: List[PathSegment] = []
        total_dist = 0.0
        total_tt = 0.0
        total_cost = 0.0
        full_coords: List[List[float]] = []

        # Add origin coordinate
        src_coord = self.get_node_coords(source_node)
        full_coords.append([src_coord[0], src_coord[1]])

        for u, v, k in edge_tuples:
            segment = self.build_path_segment(u, v, k, objective)
            edge_segments.append(segment)
            total_dist += segment.length_meters
            total_tt += segment.travel_time_seconds
            total_cost += segment.cost

            if segment.geometry_coords and len(segment.geometry_coords) > 1:
                # Append subsequent coordinates (skipping duplicated first point)
                full_coords.extend(segment.geometry_coords[1:])
            else:
                v_coord = self.get_node_coords(v)
                full_coords.append([v_coord[0], v_coord[1]])

        return (
            node_path,
            edge_segments,
            full_coords,
            round(total_dist, 2),
            round(total_tt, 2),
            round(total_cost, 3),
        )

