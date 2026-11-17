import json
import logging
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "backend"))

import folium
from folium import plugins
import networkx as nx
from shapely.geometry import LineString

from app.core.config import settings
from app.core.graph_loader import load_graph_from_graphml
from app.integrations.delhivery.geocoding_service import PHAGWARA_REFERENCE_PLACES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("build_folium_map")

# Color mapping by OSM highway classification
HWY_COLORS = {
    "motorway": "#d90429",
    "motorway_link": "#ef233c",
    "trunk": "#e63946",
    "trunk_link": "#f26a76",
    "primary": "#f77f00",
    "primary_link": "#fcbf49",
    "secondary": "#2a9d8f",
    "secondary_link": "#52b788",
    "tertiary": "#457b9d",
    "tertiary_link": "#74c0fc",
    "residential": "#6c757d",
    "living_street": "#adb5bd",
    "unclassified": "#8d99ae",
    "service": "#ced4da",
}

HWY_WEIGHTS = {
    "motorway": 5,
    "trunk": 4,
    "primary": 4,
    "secondary": 3,
    "tertiary": 2.5,
    "residential": 2,
    "unclassified": 2,
    "service": 1.5,
}


def build_interactive_map() -> Path:
    logger.info("Loading road network for interactive Folium map visualization...")
    graph = load_graph_from_graphml()
    settings.MAPS_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    map_filepath = settings.MAPS_OUTPUT_DIR / "phagwara_road_network.html"

    center_lat = settings.DEFAULT_LAT
    center_lng = settings.DEFAULT_LNG

    logger.info(f"Initializing Leaflet map centered at ({center_lat}, {center_lng})...")
    m = folium.Map(
        location=[center_lat, center_lng],
        zoom_start=13,
        tiles=None,
    )

    # Base Tile Layers
    folium.TileLayer(
        tiles="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png",
        attr="&copy; <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a> contributors | EmergencyRoute AI",
        name="OpenStreetMap Standard",
        control=True
    ).add_to(m)



    # Layer 1: Road Network
    road_layer = folium.FeatureGroup(name="Drivable Road Network (OSM)", show=True)

    logger.info("Rendering directed road segments...")
    for u, v, k, data in graph.edges(keys=True, data=True):
        hwy = data.get("highway", "unclassified")
        if isinstance(hwy, list):
            hwy = hwy[0]
        hwy_str = str(hwy)

        color = HWY_COLORS.get(hwy_str, "#8d99ae")
        weight = HWY_WEIGHTS.get(hwy_str, 2)

        name = data.get("name", "Unnamed Road")
        if isinstance(name, list):
            name = "/".join(map(str, name))

        length_m = round(float(data.get("length", 0.0)), 1)
        speed_kph = round(float(data.get("speed_kph", 30.0)), 1)
        tt_sec = round(float(data.get("travel_time", 0.0)), 1)
        speed_src = data.get("speed_source", "imputed_hwy_class")
        oneway = data.get("oneway", False)

        popup_html = f"""
        <div style="font-family: Arial, sans-serif; min-width: 200px;">
            <h4 style="margin: 0 0 6px 0; color: #1e3a8a;">{name}</h4>
            <table style="font-size: 12px; width: 100%; border-collapse: collapse;">
                <tr><td><b>Highway:</b></td><td><code>{hwy_str}</code></td></tr>
                <tr><td><b>Length:</b></td><td>{length_m} m</td></tr>
                <tr><td><b>Speed:</b></td><td>{speed_kph} km/h</td></tr>
                <tr><td><b>Travel Time:</b></td><td>{tt_sec} s</td></tr>
                <tr><td><b>Speed Type:</b></td><td>{speed_src}</td></tr>
                <tr><td><b>One-Way:</b></td><td>{oneway}</td></tr>
                <tr><td><b>Edge ID:</b></td><td>{u} &rarr; {v} (k={k})</td></tr>
            </table>
        </div>
        """

        geom = data.get("geometry")
        if geom is not None and isinstance(geom, LineString):
            coords = [[lat, lon] for lon, lat in geom.coords]
        else:
            u_node = graph.nodes[u]
            v_node = graph.nodes[v]
            coords = [[u_node["y"], u_node["x"]], [v_node["y"], v_node["x"]]]

        folium.PolyLine(
            locations=coords,
            color=color,
            weight=weight,
            opacity=0.85,
            tooltip=f"{name} ({hwy_str}) - {speed_kph} km/h",
            popup=folium.Popup(popup_html, max_width=300)
        ).add_to(road_layer)

    road_layer.add_to(m)

    # Layer 2: Emergency Landmarks & Facilities
    landmark_layer = folium.FeatureGroup(name="Emergency Facilities & Key Hubs", show=True)
    for p in PHAGWARA_REFERENCE_PLACES:
        cat = p["category"]
        if "Hospital" in cat:
            icon_color = "red"
            icon_name = "plus"
        elif "Transit" in cat:
            icon_color = "blue"
            icon_name = "road"
        elif "University" in cat:
            icon_color = "purple"
            icon_name = "graduation-cap"
        else:
            icon_color = "darkgreen"
            icon_name = "info-sign"

        popup_text = f"""
        <div style="font-family: Arial, sans-serif;">
            <b style="color: #b91c1c;">{p['name']}</b><br>
            <span style="font-size: 11px; color: #4b5563;">{p['category']}</span><br>
            <p style="font-size: 12px; margin: 4px 0 0 0;">{p['address']}</p>
            <code style="font-size: 11px;">Lat: {p['lat']}, Lng: {p['lng']}</code>
        </div>
        """

        folium.Marker(
            location=[p["lat"], p["lng"]],
            popup=folium.Popup(popup_text, max_width=280),
            tooltip=f"{p['name']} ({p['category']})",
            icon=folium.Icon(color=icon_color, icon=icon_name, prefix="glyphicon")
        ).add_to(landmark_layer)

    landmark_layer.add_to(m)

    # Add Layer Control
    folium.LayerControl(collapsed=False).add_to(m)

    # Add Legend
    legend_html = """
    <div style="
        position: fixed; 
        bottom: 25px; left: 25px; width: 230px; height: auto; 
        background-color: white; z-index:9999; font-size:12px;
        padding: 10px 14px; border:2px solid #ccc; border-radius: 8px;
        box-shadow: 2px 2px 8px rgba(0,0,0,0.2);
        font-family: Arial, sans-serif;
    ">
        <h4 style="margin: 0 0 8px 0; font-size: 13px;"><b>Phagwara Road Classes</b></h4>
        <div style="line-height: 20px;">
            <span style="background: #e63946; width: 20px; height: 4px; display: inline-block; vertical-align: middle;"></span> Motorway / Trunk<br>
            <span style="background: #f77f00; width: 20px; height: 4px; display: inline-block; vertical-align: middle;"></span> Primary Road<br>
            <span style="background: #2a9d8f; width: 20px; height: 3px; display: inline-block; vertical-align: middle;"></span> Secondary Road<br>
            <span style="background: #457b9d; width: 20px; height: 3px; display: inline-block; vertical-align: middle;"></span> Tertiary Road<br>
            <span style="background: #6c757d; width: 20px; height: 2px; display: inline-block; vertical-align: middle;"></span> Residential / Local<br>
        </div>
        <hr style="margin: 8px 0;">
        <span style="font-size: 10px; color: #666;">EmergencyRoute AI &bull; Phase 1</span>
    </div>
    """
    m.get_root().html.add_child(folium.Element(legend_html))

    logger.info(f"Saving Folium map to {map_filepath}...")
    m.save(str(map_filepath))
    logger.info("Interactive map saved successfully.")
    return map_filepath


if __name__ == "__main__":
    build_interactive_map()

