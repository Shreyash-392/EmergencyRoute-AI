import logging
from pathlib import Path
from typing import Optional
import networkx as nx
import osmnx as ox

from app.core.config import settings

logger = logging.getLogger(__name__)

_cached_graph: Optional[nx.MultiDiGraph] = None


def save_graph_to_graphml(graph: nx.MultiDiGraph, filepath: Optional[Path] = None) -> Path:
    """
    Saves the authoritative road network graph in GraphML format.
    GraphML is the primary storage standard for algorithm execution and graph persistence.
    """
    target_path = filepath or settings.GRAPHML_PATH
    target_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving graph to GraphML at {target_path} (Nodes: {len(graph.nodes)}, Edges: {len(graph.edges)})")
    ox.save_graphml(graph, filepath=target_path)
    return target_path


def load_graph_from_graphml(filepath: Optional[Path] = None, force_reload: bool = False) -> nx.MultiDiGraph:
    """
    Loads the road network graph from GraphML into memory as a directed MultiDiGraph.
    Caches the graph in memory for subsequent API and service calls unless force_reload is True.
    """
    global _cached_graph
    
    if _cached_graph is not None and not force_reload:
        return _cached_graph

    target_path = filepath or settings.GRAPHML_PATH
    if not target_path.exists():
        raise FileNotFoundError(
            f"Authoritative GraphML file not found at {target_path}. "
            f"Please run the extraction script (scripts/extract_and_export.py) first."
        )

    logger.info(f"Loading authoritative road network graph from {target_path}...")
    graph = ox.load_graphml(filepath=target_path)
    
    if not isinstance(graph, nx.MultiDiGraph):
        graph = nx.MultiDiGraph(graph)
        
    _cached_graph = graph
    logger.info(f"Graph loaded successfully: {len(graph.nodes)} nodes, {len(graph.edges)} edges.")
    return _cached_graph


def get_cached_graph() -> Optional[nx.MultiDiGraph]:
    """Returns the currently loaded graph in memory, or None if not loaded yet."""
    return _cached_graph

