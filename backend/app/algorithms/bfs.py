from collections import deque
import time
from typing import Dict, Set, Tuple

from app.algorithms.algorithm_metrics import AlgorithmResult, RoutingObjective
from app.algorithms.graph_adapter import MultiGraphAdapter


def breadth_first_search(
    adapter: MultiGraphAdapter,
    source: int,
    target: int,
    objective: RoutingObjective = RoutingObjective.TRAFFIC_AWARE
) -> AlgorithmResult:
    """
    Breadth-First Search (BFS) implementation for directed MultiDiGraph road networks.
    
    Characteristics:
    - Queue-based FIFO frontier.
    - Visited set preventing cycles and duplicate exploration.
    - Parent tracking preserving directed edge keys for accurate geometry.
    - Optimizes for unweighted minimum hop count (fewest road segments).
    - NOTE: Does NOT guarantee minimum travel time or weighted road distance.
    """
    start_time = time.perf_counter()

    if not adapter.contains_node(source):
        return AlgorithmResult(
            algorithm_name="BFS",
            source_node=source,
            target_node=target,
            success=False,
            error_message=f"Source node {source} not present in road network."
        )

    if not adapter.contains_node(target):
        return AlgorithmResult(
            algorithm_name="BFS",
            source_node=source,
            target_node=target,
            success=False,
            error_message=f"Target node {target} not present in road network."
        )

    if source == target:
        src_coord = adapter.get_node_coords(source)
        return AlgorithmResult(
            algorithm_name="BFS",
            source_node=source,
            target_node=target,
            success=True,
            node_path=[source],
            coordinates=[[src_coord[0], src_coord[1]]],
            is_optimal=False,
            nodes_explored=1,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            routing_objective=objective
        )

    # Queue contains: current_node
    queue: deque[int] = deque([source])
    visited: Set[int] = {source}
    parent_pointers: Dict[int, Tuple[int, int]] = {}  # child -> (parent, key)
    nodes_explored = 0
    target_found = False

    while queue:
        curr = queue.popleft()
        nodes_explored += 1

        if curr == target:
            target_found = True
            break

        for neighbor, key, cost, edge_data in adapter.get_successors(curr, objective):
            if neighbor not in visited:
                visited.add(neighbor)
                parent_pointers[neighbor] = (curr, key)
                queue.append(neighbor)

    elapsed_ms = (time.perf_counter() - start_time) * 1000.0

    if not target_found:
        return AlgorithmResult(
            algorithm_name="BFS",
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
        algorithm_name="BFS",
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
        is_optimal=False,  # Hop-count optimal only, not weighted metric optimal
        coordinates=full_coords
    )

