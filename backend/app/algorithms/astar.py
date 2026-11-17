import heapq
import time
from typing import Dict, Set, Tuple

from app.algorithms.algorithm_metrics import AlgorithmResult, RoutingObjective
from app.algorithms.graph_adapter import MultiGraphAdapter


def a_star_search(
    adapter: MultiGraphAdapter,
    source: int,
    target: int,
    objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE
) -> AlgorithmResult:
    """
    A* (A-Star) Search implementation for directed MultiDiGraph road networks.
    
    Characteristics:
    - Priority queue ordered by: f(n) = g(n) + h(n)
      where g(n) = exact accumulated path cost from source,
      and h(n) = provably admissible lower-bound geographic heuristic.
    - Cost relaxation: updates g(v) whenever a cheaper directed path is discovered.
    - Stale queue entry handling: discards superseded priority queue elements.
    - Closed set tracking finalized expanded nodes.
    - Guarantees provably optimal route under the chosen RoutingObjective.
    """
    start_time = time.perf_counter()

    if not adapter.contains_node(source):
        return AlgorithmResult(
            algorithm_name="A* Search",
            source_node=source,
            target_node=target,
            success=False,
            error_message=f"Source node {source} not present in road network."
        )

    if not adapter.contains_node(target):
        return AlgorithmResult(
            algorithm_name="A* Search",
            source_node=source,
            target_node=target,
            success=False,
            error_message=f"Target node {target} not present in road network."
        )

    if source == target:
        src_coord = adapter.get_node_coords(source)
        return AlgorithmResult(
            algorithm_name="A* Search",
            source_node=source,
            target_node=target,
            success=True,
            node_path=[source],
            coordinates=[[src_coord[0], src_coord[1]]],
            is_optimal=True,
            nodes_explored=1,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            routing_objective=objective
        )

    # g_scores: node -> actual accumulated cost from source
    g_scores: Dict[int, float] = {source: 0.0}
    
    # Priority queue: (f_score, tie_breaker_counter, node)
    counter = 0
    h_start = adapter.heuristic_calc.estimate(source, target, objective)
    pq = [(h_start, counter, source)]

    parent_pointers: Dict[int, Tuple[int, int]] = {}  # child -> (parent, key)
    closed_set: Set[int] = set()
    nodes_explored = 0
    target_found = False

    while pq:
        f_score, _, curr = heapq.heappop(pq)

        # Skip stale priority queue entries
        if curr in closed_set:
            continue

        closed_set.add(curr)
        nodes_explored += 1

        if curr == target:
            target_found = True
            break

        curr_g = g_scores[curr]

        for neighbor, key, edge_cost, edge_data in adapter.get_successors(curr, objective):
            tentative_g = curr_g + edge_cost

            if tentative_g < g_scores.get(neighbor, float("inf")):
                # Found a strictly superior path to neighbor
                g_scores[neighbor] = tentative_g
                parent_pointers[neighbor] = (curr, key)
                
                h_cost = adapter.heuristic_calc.estimate(neighbor, target, objective)
                f_cost = tentative_g + h_cost
                counter += 1
                heapq.heappush(pq, (f_cost, counter, neighbor))

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    if not target_found:
        return AlgorithmResult(
            algorithm_name="A* Search",
            source_node=source,
            target_node=target,
            success=False,
            nodes_explored=nodes_explored,
            execution_time_ms=round(elapsed_ms, 3),
            routing_objective=objective,
            error_message=f"No directed path found from node {source} to node {target}."
        )

    (
        node_path,
        edge_segments,
        full_coords,
        total_dist,
        total_tt,
        total_cost
    ) = adapter.reconstruct_full_path(parent_pointers, source, target, objective)

    return AlgorithmResult(
        algorithm_name="A* Search",
        source_node=source,
        target_node=target,
        success=True,
        node_path=node_path,
        edge_path=edge_segments,
        path_distance_meters=total_dist,
        path_distance_km=round(total_dist / 1000.0, 3),
        estimated_travel_time_seconds=total_tt,
        estimated_travel_time_minutes=round(total_tt / 60.0, 2),
        weighted_path_cost=total_cost,
        nodes_explored=nodes_explored,
        execution_time_ms=round(elapsed_ms, 3),
        routing_objective=objective,
        is_optimal=True,
        coordinates=full_coords
    )

