import json
import logging
from pathlib import Path
import sys

# Ensure backend package is importable
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import geopandas as gpd
import networkx as nx
import osmnx as ox
import pandas as pd
from shapely.geometry import Point

from app.core.config import settings
from app.core.graph_loader import save_graph_to_graphml
from app.services.osm_service import extract_phagwara_network
from app.services.validation_service import validate_road_network

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("extract_and_export")


def export_nodes_and_edges(graph: nx.MultiDiGraph):
    """
    Exports road network nodes and edges into GeoJSON and CSV formats,
    preserving OSM IDs, parallel edge keys, and geometric linestrings.
    """
    logger.info("Converting MultiDiGraph to GeoDataFrames...")
    gdf_nodes, gdf_edges = ox.graph_to_gdfs(graph)

    # 1. Export Nodes
    nodes_geojson_path = settings.PROCESSED_NODES_DIR / "phagwara_nodes.geojson"
    nodes_csv_path = settings.PROCESSED_NODES_DIR / "phagwara_nodes.csv"
    
    settings.PROCESSED_NODES_DIR.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Exporting {len(gdf_nodes)} nodes to GeoJSON ({nodes_geojson_path})...")
    gdf_nodes.to_file(nodes_geojson_path, driver="GeoJSON")
    
    logger.info(f"Exporting {len(gdf_nodes)} nodes to CSV ({nodes_csv_path})...")
    # Clean geometry representation for CSV
    df_nodes = pd.DataFrame(gdf_nodes.drop(columns=["geometry"], errors="ignore"))
    df_nodes["node_id"] = gdf_nodes.index
    df_nodes.to_csv(nodes_csv_path, index=False)

    # 2. Export Edges
    edges_geojson_path = settings.PROCESSED_EDGES_DIR / "phagwara_edges.geojson"
    edges_csv_path = settings.PROCESSED_EDGES_DIR / "phagwara_edges.csv"
    
    settings.PROCESSED_EDGES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Flatten complex list columns (e.g., highway or oneway as lists) for GeoJSON serialization
    gdf_edges_export = gdf_edges.copy()
    for col in gdf_edges_export.columns:
        if col != "geometry" and gdf_edges_export[col].apply(lambda x: isinstance(x, list)).any():
            gdf_edges_export[col] = gdf_edges_export[col].apply(lambda x: ", ".join(map(str, x)) if isinstance(x, list) else str(x) if pd.notnull(x) else "")

    logger.info(f"Exporting {len(gdf_edges_export)} edges to GeoJSON ({edges_geojson_path})...")
    gdf_edges_export.to_file(edges_geojson_path, driver="GeoJSON")
    
    logger.info(f"Exporting {len(gdf_edges)} edges to CSV ({edges_csv_path})...")
    df_edges = pd.DataFrame(gdf_edges_export.drop(columns=["geometry"], errors="ignore"))
    # MultiIndex is (u, v, key)
    df_edges["u"] = [idx[0] for idx in gdf_edges.index]
    df_edges["v"] = [idx[1] for idx in gdf_edges.index]
    df_edges["key"] = [idx[2] for idx in gdf_edges.index]
    df_edges.to_csv(edges_csv_path, index=False)


def main():
    logger.info("Starting Phase 1 OSM Extraction and Dataset Generation...")
    
    # 1. Download and enrich graph
    graph = extract_phagwara_network(
        place_name=settings.CITY,
        center_point=(settings.DEFAULT_LAT, settings.DEFAULT_LNG),
        dist_meters=settings.DEFAULT_SEARCH_RADIUS_METERS,
        force_refresh=False
    )

    # 2. Save Authoritative GraphML
    graphml_path = save_graph_to_graphml(graph)
    logger.info(f"Authoritative GraphML saved at: {graphml_path}")

    # 3. Export GeoJSON and CSV formats
    export_nodes_and_edges(graph)

    # 4. Perform comprehensive validation
    logger.info("Executing network validation audit...")
    validation_report = validate_road_network(graph)

    # 5. Save validation report
    settings.REPORTS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    report_path = settings.REPORTS_OUTPUT_DIR / "phase1_validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(validation_report, f, indent=2)
    logger.info(f"Validation report saved to: {report_path}")

    print("\n" + "=" * 60)
    print("PHASE 1 DATA EXTRACTION & VALIDATION SUMMARY")
    print("=" * 60)
    print(f"Validation Status:       {validation_report['status']}")
    print(f"Graph Type:              {validation_report['graph_type']}")
    print(f"Directed MultiDiGraph:   {validation_report['is_multidigraph']}")
    print(f"Total Nodes:             {validation_report['nodes_count']}")
    print(f"Total Directed Edges:    {validation_report['edges_count']}")
    print(f"Total Road Length:       {validation_report['attributes']['total_length_km']} km")
    print(f"Mean Edge Length:        {validation_report['attributes']['mean_edge_length_meters']} m")
    print(f"Mean Edge Travel Time:   {validation_report['attributes']['mean_travel_time_seconds']} s")
    print(f"Parallel Edge Pairs:     {validation_report['attributes']['parallel_edge_pairs']}")
    print(f"Weakly Connected Comp.:  {validation_report['connectivity']['weakly_connected_components']}")
    print(f"Largest WCC Coverage:    {validation_report['connectivity']['largest_wcc_percentage']}%")
    print(f"Strongly Connected Comp: {validation_report['connectivity']['strongly_connected_components']}")
    print(f"Isolated Nodes:          {validation_report['connectivity']['isolated_nodes_count']}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()

