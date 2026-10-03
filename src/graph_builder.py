import sys
from pathlib import Path

# Agrega la raíz del proyecto al sys.path de Python
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR))

# Ahora tus importaciones funcionarán sin importar cómo ejecutes el archivo
from src.config import PROCESSED_DATA_DIR, NUM_NODES

import os
import osmnx as ox
import networkx as nx
import numpy as np
from pathlib import Path

# Importación limpia gracias a la Opción B
from src.config import PROCESSED_DATA_DIR, NUM_NODES


def extract_zmg_graph(
    place_name: str = "Guadalajara, Jalisco, Mexico", 
    distance_meters: int = 10000,
    tolerance_meters: int = 100
) -> nx.DiGraph:
    """
    Descarga y consolida la subred vial de corredores principales de la ZMG.
    """
    print(f" Descargando red vial desde OpenStreetMap para: {place_name}...")
    
    # Filtro para conservar solo corredores y avenidas principales
    custom_filter = '["highway"~"motorway|primary|secondary"]'
    
    # 1. Obtener grafo crudo
    G_raw = ox.graph_from_address(
        address=place_name,
        dist=distance_meters,
        network_type="drive",
        custom_filter=custom_filter,
        simplify=True
    )
    print(f" Grafo crudo: {len(G_raw.nodes)} nodos y {len(G_raw.edges)} aristas.")

    # 2. Proyectar a UTM para mediciones en metros y consolidar intersecciones
    print(f" Consolidando intersecciones cercanas ({tolerance_meters}m)...")
    G_proj = ox.project_graph(G_raw)
    G_consolidated = ox.consolidate_intersections(
        G_proj, 
        tolerance=tolerance_meters, 
        rebuild_graph=True, 
        dead_ends=False
    )
    
    # 3. Re-proyectar a coordenadas geográficas WGS84 (Latitud/Longitud)
    G_final = ox.project_graph(G_consolidated, to_crs="EPSG:4326")
    print(f" Grafo simplificado final: {len(G_final.nodes)} nodos principales.")
    
    return G_final


def compute_gaussian_adjacency_matrix(
    G: nx.DiGraph, 
    threshold_meters: float = 5000.0
) -> np.ndarray:
    """
    Calcula la Matriz de Adyacencia Gaussiana (W) usando la distancia vial
    entre cada par de nodos con el Kernel RBF y un umbral de corte (threshold).
    """
    nodes = list(G.nodes())
    num_nodes = len(nodes)
    print(f" Calculando matriz de distancias viales para {num_nodes} nodos...")

    # Matriz de distancias viales d_ij
    d_matrix = np.full((num_nodes, num_nodes), np.inf)

    for i, u in enumerate(nodes):
        for j, v in enumerate(nodes):
            if i == j:
                d_matrix[i, j] = 0.0
            elif nx.has_path(G, u, v):
                # Distancia mas corta sobre la red vial
                d_matrix[i, j] = nx.shortest_path_length(G, u, v, weight="length")

    # Obtener desviacion estandar sigma de las distancias finitas
    valid_distances = d_matrix[np.isfinite(d_matrix) & (d_matrix > 0)]
    sigma = np.std(valid_distances)
    print(f" Desviacion estandar (sigma) de distancias: {sigma:.2f} metros.")

    # Aplicar Kernel Gaussiano RBF con umbral de corte theta
    W = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    for i in range(num_nodes):
        for j in range(num_nodes):
            if i != j and d_matrix[i, j] <= threshold_meters:
                W[i, j] = np.exp(- (d_matrix[i, j] / sigma) ** 2)

    print(f" Matriz de adyacencia W construida con exito. Forma: {W.shape}")
    return W


def save_artifacts(G: nx.DiGraph, W: np.ndarray):
    """
    Guarda el grafo (.graphml) y la matriz W (.npy) en data/processed/.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    
    # 1. Guardar la matriz de adyacencia W
    w_path = PROCESSED_DATA_DIR / "adjacency_matrix.npy"
    np.save(w_path, W)
    print(f" Matriz W guardada en: {w_path}")

    # 2. Guardar el grafo vial usando OSMnx (formato GraphML compatible con CRS y geometrías)
    graphml_path = PROCESSED_DATA_DIR / "graph_zmg.graphml"
    ox.save_graphml(G, filepath=graphml_path)
    print(f" Grafo guardado en: {graphml_path}")


if __name__ == "__main__":
    # Generar grafo y matriz
    G = extract_zmg_graph()
    W = compute_gaussian_adjacency_matrix(G)
    save_artifacts(G, W)