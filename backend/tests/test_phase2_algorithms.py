from pathlib import Path
import sys
import networkx as nx
import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

from app.algorithms.algorithm_metrics import RoutingObjective
from app.algorithms.astar import a_star_search
from app.algorithms.bfs import breadth_first_search
from app.algorithms.dfs import depth_first_search
from app.algorithms.graph_adapter import MultiGraphAdapter
from app.algorithms.greedy_best_first import greedy_best_first_search
from app.algorithms.heuristic import haversine_distance
from app.core.graph_loader import load_graph_from_graphml


@pytest.fixture
def small_test_graph():
    """
    Creates a small deterministic MultiDiGraph with geometrically valid coordinates:
    
    Nodes: 1, 2, 3, 4, 5 (isolated)
    1 at (31.2200, 75.7700)
    2 at (31.2205, 75.7705) [~75m from 1]
    3 at (31.2210, 75.7710) [~150m from 1]
    
    Edges:
    1 -> 2 (key=0, length=200.0, speed_kph=30.0, travel_time=24.0)
    1 -> 2 (key=1, length=80.0,  speed_kph=30.0, travel_time=9.6)  <-- parallel edge!
    2 -> 3 (key=0, length=80.0,  speed_kph=30.0, travel_time=9.6)
    1 -> 3 (key=0, length=300.0, speed_kph=30.0, travel_time=36.0) <-- 1 hop, but higher cost (300m vs 80+80=160m)!
    3 -> 4 (key=0, length=50.0,  speed_kph=30.0, travel_time=6.0)
    4 -> 2 (key=0, length=50.0,  speed_kph=30.0, travel_time=6.0)  <-- cycle!
    """
    G = nx.MultiDiGraph()
    G.add_node(1, y=31.2200, x=75.7700)
    G.add_node(2, y=31.2205, x=75.7705)
    G.add_node(3, y=31.2210, x=75.7710)
    G.add_node(4, y=31.2215, x=75.7715)
    G.add_node(5, y=31.2300, x=75.7800)  # Isolated

    # Parallel edges between 1 and 2
    G.add_edge(1, 2, key=0, length=200.0, speed_kph=30.0, travel_time=24.0, highway="residential", name="Long Road")
    G.add_edge(1, 2, key=1, length=80.0,  speed_kph=30.0, travel_time=9.6,  highway="primary",     name="Short Cut")
    
    # 2 -> 3
    G.add_edge(2, 3, key=0, length=80.0,  speed_kph=30.0, travel_time=9.6,  highway="primary",     name="Main Ave")
    
    # 1 -> 3 (Direct hop, length=300m vs 1->2->3 which is 80+80 = 160m)
    G.add_edge(1, 3, key=0, length=300.0, speed_kph=30.0, travel_time=36.0, highway="secondary",   name="Direct Bypass")
    
    # Cycle: 3 -> 4 -> 2
    G.add_edge(3, 4, key=0, length=50.0,  speed_kph=30.0, travel_time=6.0,  highway="service",     name="Loop A")
    G.add_edge(4, 2, key=0, length=50.0,  speed_kph=30.0, travel_time=6.0,  highway="service",     name="Loop B")

    return G


# -------------------------------------------------------------
# 1. Deterministic Small Graph Algorithm Verification
# -------------------------------------------------------------

def test_multigraph_parallel_edge_selection(small_test_graph):
    """Verifies that MultiGraphAdapter picks key=1 (length 80m) over key=0 (length 200m)."""
    adapter = MultiGraphAdapter(small_test_graph)
    successors = adapter.get_successors(1, RoutingObjective.MIN_DISTANCE)
    
    trans_to_2 = next(s for s in successors if s[0] == 2)
    chosen_key = trans_to_2[1]
    chosen_cost = trans_to_2[2]

    assert chosen_key == 1, f"Expected key=1 for parallel edge, got {chosen_key}"
    assert chosen_cost == 80.0


def test_bfs_vs_astar_hop_vs_cost(small_test_graph):
    """
    BFS must choose 1 hop (1 -> 3, cost=300).
    A* must choose 2 hops (1 -> 2 -> 3, cost=160).
    """
    adapter = MultiGraphAdapter(small_test_graph)
    
    bfs_res = breadth_first_search(adapter, 1, 3, RoutingObjective.MIN_DISTANCE)
    astar_res = a_star_search(adapter, 1, 3, RoutingObjective.MIN_DISTANCE)

    assert bfs_res.success is True
    assert astar_res.success is True

    # BFS chooses fewest hops: [1, 3] (length 300m)
    assert bfs_res.node_path == [1, 3]
    assert bfs_res.path_distance_meters == 300.0

    # A* chooses lowest distance: [1, 2, 3] (length 80 + 80 = 160m)
    assert astar_res.node_path == [1, 2, 3]
    assert astar_res.path_distance_meters == 160.0
    assert astar_res.is_optimal is True


def test_dfs_cycle_handling(small_test_graph):
    """Verifies that DFS handles the cycle (2 -> 3 -> 4 -> 2) without infinite loop."""
    adapter = MultiGraphAdapter(small_test_graph)
    dfs_res = depth_first_search(adapter, 1, 4, RoutingObjective.MIN_DISTANCE)
    
    assert dfs_res.success is True
    assert dfs_res.node_path[-1] == 4
    assert dfs_res.nodes_explored > 0


def test_greedy_best_first_heuristic(small_test_graph):
    """Verifies Greedy Best-First navigates towards target."""
    adapter = MultiGraphAdapter(small_test_graph)
    greedy_res = greedy_best_first_search(adapter, 1, 3, RoutingObjective.MIN_DISTANCE)
    
    assert greedy_res.success is True
    assert greedy_res.node_path[0] == 1
    assert greedy_res.node_path[-1] == 3


def test_road_closure_pruning(small_test_graph):
    """Verifies that closing edge (1, 3, 0) prevents direct hop."""
    closed = {(1, 3, 0)}
    adapter = MultiGraphAdapter(small_test_graph, closed_edges=closed)

    bfs_res = breadth_first_search(adapter, 1, 3, RoutingObjective.MIN_DISTANCE)
    assert bfs_res.success is True
    # Now BFS must go through node 2 because direct edge is closed
    assert bfs_res.node_path == [1, 2, 3]


def test_disconnected_destination(small_test_graph):
    """Verifies clean failure response when target is unreachable (isolated node 5)."""
    adapter = MultiGraphAdapter(small_test_graph)
    astar_res = a_star_search(adapter, 1, 5, RoutingObjective.MIN_DISTANCE)
    
    assert astar_res.success is False
    assert "No directed path found" in astar_res.error_message


def test_one_way_compliance(small_test_graph):
    """Verifies that directed edges cannot be traversed in reverse (e.g. 3 -> 1)."""
    adapter = MultiGraphAdapter(small_test_graph)
    astar_res = a_star_search(adapter, 3, 1, RoutingObjective.MIN_DISTANCE)
    
    assert astar_res.success is False


# -------------------------------------------------------------
# 2. Real Phagwara Road Graph Integration Tests
# -------------------------------------------------------------

@pytest.fixture(scope="module")
def phagwara_graph():
    return load_graph_from_graphml()


def test_all_four_algorithms_on_phagwara_network(phagwara_graph):
    """Runs all four search algorithms on the actual Phagwara road graph."""
    adapter = MultiGraphAdapter(phagwara_graph)

    # Use two known connected nodes from Phagwara
    # Civil Hospital (lat ~31.2223) and Central Bus Stand (lat ~31.2215)
    import osmnx as ox
    src = int(ox.distance.nearest_nodes(phagwara_graph, X=75.7672, Y=31.2223))
    tgt = int(ox.distance.nearest_nodes(phagwara_graph, X=75.7738, Y=31.2215))

    bfs_res = breadth_first_search(adapter, src, tgt, RoutingObjective.TRAFFIC_AWARE)
    dfs_res = depth_first_search(adapter, src, tgt, RoutingObjective.TRAFFIC_AWARE)
    gbfs_res = greedy_best_first_search(adapter, src, tgt, RoutingObjective.TRAFFIC_AWARE)
    astar_res = a_star_search(adapter, src, tgt, RoutingObjective.TRAFFIC_AWARE)

    assert bfs_res.success is True, f"BFS failed: {bfs_res.error_message}"
    assert dfs_res.success is True, f"DFS failed: {dfs_res.error_message}"
    assert gbfs_res.success is True, f"Greedy failed: {gbfs_res.error_message}"
    assert astar_res.success is True, f"A* failed: {astar_res.error_message}"

    # A* must produce <= travel time of BFS
    assert astar_res.estimated_travel_time_seconds <= bfs_res.estimated_travel_time_seconds + 0.1
    assert astar_res.is_optimal is True
    assert bfs_res.is_optimal is False
    assert dfs_res.is_optimal is False
    assert gbfs_res.is_optimal is False

    # Check coordinate polyline validity
    assert len(astar_res.coordinates) >= 2
    for coord in astar_res.coordinates:
        assert 31.10 <= coord[0] <= 31.35
        assert 75.60 <= coord[1] <= 75.90
