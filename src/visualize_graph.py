import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

import networkx as nx
import osmnx as ox
import folium

from src.config import PROCESSED_DATA_DIR

def generate_interactive_map():
    graph_path = PROCESSED_DATA_DIR / "graph_zmg.graphml"
    if not graph_path.exists():
        print(f"Error: No se encontró el archivo {graph_path}")
        return

    print("Cargando grafo...")
    G = ox.load_graphml(graph_path)

    # Calcular centroide promedio para centrar el mapa
    lats = [float(data.get("y", 0)) for _, data in G.nodes(data=True)]
    lons = [float(data.get("x", 0)) for _, data in G.nodes(data=True)]
    
    center_lat = sum(lats) / len(lats)
    center_lon = sum(lons) / len(lons)

    # Crear mapa interactivo centrado en la ZMG
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=12,
        tiles="OpenStreetMap"
    )

    # Dibujar círculo de referencia del radio de 10km (10,000 m)
    folium.Circle(
        location=[center_lat, center_lon],
        radius=10000,
        color="#0284c7",
        weight=2,
        fill=True,
        fill_opacity=0.08,
        popup="Radio de cobertura actual (10 km)"
    ).add_to(m)

    # Dibujar las aristas / conexiones viales
    for u, v, data in G.edges(data=True):
        u_lat, u_lon = float(G.nodes[u]["y"]), float(G.nodes[u]["x"])
        v_lat, v_lon = float(G.nodes[v]["y"]), float(G.nodes[v]["x"])
        folium.PolyLine(
            locations=[(u_lat, u_lon), (v_lat, v_lon)],
            color="#64748b",
            weight=2,
            opacity=0.7
        ).add_to(m)

    # Dibujar los nodos principales (intersecciones)
    for node_id, data in G.nodes(data=True):
        lat, lon = float(data["y"]), float(data["x"])
        folium.CircleMarker(
            location=[lat, lon],
            radius=4,
            color="#dc2626",
            fill=True,
            fill_color="#ef4444",
            fill_opacity=0.9,
            popup=f"<b>Nodo:</b> {node_id}<br><b>Lat:</b> {lat:.5f}<br><b>Lon:</b> {lon:.5f}"
        ).add_to(m)

    folium.LayerControl().add_to(m)

    output_html = PROCESSED_DATA_DIR / "mapa_nodos_zmg.html"
    m.save(str(output_html))
    print(f" Mapa interactivo guardado exitosamente en:\n -> {output_html}")

if __name__ == "__main__":
    generate_interactive_map()
