import heapq
import pytest
from app.core.graph_loader import load_graph_from_graphml
from app.algorithms.graph_adapter import MultiGraphAdapter
from app.algorithms.astar import a_star_search
from app.algorithms.bfs import breadth_first_search
from app.algorithms.dfs import depth_first_search
from app.algorithms.greedy_best_first import greedy_best_first_search
from app.algorithms.algorithm_metrics import RoutingObjective


def run_dijkstra_reference(adapter: MultiGraphAdapter, start: int, target: int, objective: RoutingObjective):
    """
    Independent, minimal uniform-cost search (Dijkstra) implementation used
    STRICTLY as an automated ground-truth reference for A* optimality testing.
    """
    pq = [(0.0, start)]
    dist = {start: 0.0}
    visited = set()

    while pq:
        d, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)

        if u == target:
            return d

        for v, key, edge_cost, data in adapter.get_successors(u, objective):
            if v in visited:
                continue
            new_d = d + edge_cost
            if v not in dist or new_d < dist[v]:
                dist[v] = new_d
                heapq.heappush(pq, (new_d, v))

    return None


@pytest.fixture(scope="module")
def phagwara_adapter():
    graph = load_graph_from_graphml()
    return MultiGraphAdapter(graph)


def test_heuristic_admissibility_and_non_negative_costs(phagwara_adapter):
    """
    Verifies that:
    1. Every traversable edge has a strictly positive non-negative cost (>= 0.1).
    2. The network maximum speed bound v_max correctly bounds all edge speeds.
    """
    for u, v, k, data in phagwara_adapter.graph.edges(keys=True, data=True):
        cost_dist = phagwara_adapter.get_edge_cost(u, v, k, data, RoutingObjective.MIN_DISTANCE)
        cost_time = phagwara_adapter.get_edge_cost(u, v, k, data, RoutingObjective.MIN_TRAVEL_TIME)
        cost_traffic = phagwara_adapter.get_edge_cost(u, v, k, data, RoutingObjective.TRAFFIC_AWARE)

        assert cost_dist >= 0.1, f"Negative/zero distance on edge ({u}, {v}, {k})"
        assert cost_time >= 0.1, f"Negative/zero travel time on edge ({u}, {v}, {k})"
        assert cost_traffic >= 0.1, f"Negative/zero traffic cost on edge ({u}, {v}, {k})"

        edge_spd = float(data.get("speed_kph", 30.0))
        assert edge_spd <= phagwara_adapter.max_speed_kph, (
            f"Edge speed {edge_spd} exceeds maximum speed bound {phagwara_adapter.max_speed_kph}"
        )


def test_astar_vs_dijkstra_optimality_across_multiple_od_pairs(phagwara_adapter):
    """
    Rigorously asserts that A* Search matches the independent Dijkstra reference
    cost within a strict numerical tolerance (0.05) across multiple OD corridors
    and all three optimization objectives.
    """
    test_pairs = [
        (1368112650, 11578644470),  # Civil Hospital -> LPU Main Gate (Arterial corridor, ~8.0 km)
        (5214151814, 3148701364),    # Railway Station -> Central Bus Stand (Urban multi-block corridor, ~0.58 km)
        (444674679, 1368112663),    # Subhash Nagar Adjacent Block Link (~81.8 meters)
    ]

    for start_node, dest_node in test_pairs:
        for obj in [RoutingObjective.MIN_DISTANCE, RoutingObjective.MIN_TRAVEL_TIME, RoutingObjective.TRAFFIC_AWARE]:
            astar_res = a_star_search(phagwara_adapter, start_node, dest_node, obj)
            assert astar_res.success is True, f"A* failed on pair {start_node} -> {dest_node}"

            dijk_cost = run_dijkstra_reference(phagwara_adapter, start_node, dest_node, obj)
            assert dijk_cost is not None, f"Dijkstra found no path for {start_node} -> {dest_node}"

            diff = abs(astar_res.weighted_path_cost - dijk_cost)
            assert diff <= 0.05, (
                f"A* cost {astar_res.weighted_path_cost} does not match optimal Dijkstra cost {dijk_cost} "
                f"for pair {start_node}->{dest_node} on objective {obj.value} (diff={diff})"
            )


def test_case_a_nonexistent_destination(phagwara_adapter):
    """
    Case A: Destination node does NOT exist in the graph.
    All algorithms must immediately detect this, return success=False, and avoid hanging.
    """
    start_node = 1368112650
    invalid_dest = 999999999999

    assert phagwara_adapter.contains_node(start_node) is True
    assert phagwara_adapter.contains_node(invalid_dest) is False

    for name, fn in [
        ("A*", a_star_search),
        ("Greedy", greedy_best_first_search),
        ("BFS", breadth_first_search),
        ("DFS", depth_first_search),
    ]:
        res = fn(phagwara_adapter, start_node, invalid_dest)
        assert res.success is False
        assert "not present in road network" in res.error_message
        assert res.nodes_explored == 0


def test_case_b_genuine_unreachable_destination_in_graph(phagwara_adapter):
    """
    Case B: Destination node EXISTS in the graph, but is UNREACHABLE from origin
    due to disconnected components / directed one-way road network topology.
    All 4 algorithms must explore the component, terminate cleanly without loops,
    and return an honest route-not-found result.
    """
    import networkx as nx

    start_node = 1368113153  # In main weakly connected component (3,959 nodes)
    dest_node = 5271348536   # In separate disconnected component (4 nodes)

    # Confirm both nodes exist in the graph
    assert phagwara_adapter.contains_node(start_node) is True
    assert phagwara_adapter.contains_node(dest_node) is True

    # Confirm no directed path exists in ground truth
    assert nx.has_path(phagwara_adapter.graph, start_node, dest_node) is False

    for name, fn in [
        ("A*", a_star_search),
        ("Greedy", greedy_best_first_search),
        ("BFS", breadth_first_search),
        ("DFS", depth_first_search),
    ]:
        res = fn(phagwara_adapter, start_node, dest_node)
        assert res.success is False, f"{name} falsely reported success on unreachable destination!"
        assert "No directed path found" in res.error_message
        assert res.nodes_explored > 0, f"{name} should have explored the reachable component"
        assert res.path_distance_km == 0.0
        assert res.estimated_travel_time_minutes == 0.0


def test_astar_vs_dijkstra_with_road_closure(phagwara_adapter):
    """
    Asserts that when an arterial edge is closed, both A* and Dijkstra re-route
    identically and find the same optimal bypass cost.
    """
    start_node = 444674679
    dest_node = 1368112663

    # Close primary direct edge to trigger dynamic detour
    closure_set = {(start_node, dest_node, 0)}
    closed_adapter = MultiGraphAdapter(phagwara_adapter.graph, closed_edges=closure_set)

    astar_res = a_star_search(closed_adapter, start_node, dest_node, RoutingObjective.MIN_TRAVEL_TIME)
    dijk_cost = run_dijkstra_reference(closed_adapter, start_node, dest_node, RoutingObjective.MIN_TRAVEL_TIME)

    assert astar_res.success is True
    assert dijk_cost is not None
    assert abs(astar_res.weighted_path_cost - dijk_cost) <= 0.05


def test_bfs_and_dfs_cycle_and_hop_behavior(phagwara_adapter):
    """
    Asserts that BFS and DFS execute cleanly, terminate without infinite loops,
    and BFS optimizes hop count rather than travel time.
    """
    start_node = 444674679
    dest_node = 1368112663

    bfs_res = breadth_first_search(phagwara_adapter, start_node, dest_node)
    dfs_res = depth_first_search(phagwara_adapter, start_node, dest_node)

    assert bfs_res.success is True
    assert dfs_res.success is True
    assert len(bfs_res.node_path) > 1
    assert len(dfs_res.node_path) > 1
    # BFS should have fewer or equal hops compared to DFS
    assert len(bfs_res.node_path) <= len(dfs_res.node_path)
