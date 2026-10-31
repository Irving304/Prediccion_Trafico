import logging
from typing import Optional
import folium
import networkx as nx
import osmnx as ox

from src.config import GRAPH_DISTANCE_METERS, PROCESSED_DATA_DIR

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def generate_interactive_map() -> None:
    graph_path = PROCESSED_DATA_DIR / "graph_zmg.graphml"
    if not graph_path.exists():
        logger.error(f"No se encontró el archivo del grafo en: {graph_path}")
        return

    logger.info("Cargando grafo vial...")
    G = ox.load_graphml(graph_path)

    # Extraer coordenadas válidas de los nodos
    lats = [float(data["y"]) for _, data in G.nodes(data=True) if "y" in data]
    lons = [float(data["x"]) for _, data in G.nodes(data=True) if "x" in data]

    if not lats or not lons:
        logger.error("El grafo no contiene coordenadas 'x' / 'y' válidas en sus nodos.")
        return

    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Crear mapa interactivo centrado en la ZMG
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    # Dibujar círculo de referencia de cobertura
    folium.Circle(
        location=[center_lat, center_lon],
        radius=GRAPH_DISTANCE_METERS,
        color="#0284c7",
        weight=2,
        fill=True,
        fill_opacity=0.08,
        popup=f"Radio de cobertura ({GRAPH_DISTANCE_METERS / 1000:.1f} km)"
    ).add_to(m)

    # Dibujar aristas / conexiones viales respetando geometrías reales si existen
    for u, v, data in G.edges(data=True):
        u_data, v_data = G.nodes.get(u, {}), G.nodes.get(v, {})
        if "y" not in u_data or "x" not in u_data or "y" not in v_data or "x" not in v_data:
            continue

        geom = data.get("geometry")
        if geom is not None and hasattr(geom, "coords"):
            # Shapely LineString: invertir (lon, lat) -> (lat, lon) para Folium
            points = [(lat, lon) for lon, lat in geom.coords]
        else:
            u_lat, u_lon = float(u_data["y"]), float(u_data["x"])
            v_lat, v_lon = float(v_data["y"]), float(v_data["x"])
            points = [(u_lat, u_lon), (v_lat, v_lon)]

        folium.PolyLine(
            locations=points,
            color="#64748b",
            weight=2,
            opacity=0.7
        ).add_to(m)

    # Dibujar nodos principales (intersecciones)
    for node_id, data in G.nodes(data=True):
        if "y" not in data or "x" not in data:
            continue
        lat, lon = float(data["y"]), float(data["x"])
        node_idx = data.get("node_index", "N/A")
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="#dc2626",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.9,
            popup=f"<b>Índice:</b> {node_idx}<br><b>OSM ID:</b> {node_id}<br><b>Lat:</b> {lat:.5f}<br><b>Lon:</b> {lon:.5f}"
        ).add_to(m)

    folium.LayerControl().add_to(m)

    output_html = PROCESSED_DATA_DIR / "mapa_nodos_zmg.html"
    m.save(str(output_html))
    logger.info(f"Mapa interactivo guardado exitosamente en: {output_html}")


if __name__ == "__main__":
    generate_interactive_map()
