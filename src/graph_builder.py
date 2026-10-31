import json
import logging
from typing import Dict, List, Tuple
import networkx as nx
import numpy as np
import osmnx as ox

from src.config import (
    CUSTOM_HIGHWAY_FILTER,
    DEFAULT_PLACE_NAME,
    DISTANCE_THRESHOLD_METERS,
    GRAPH_DISTANCE_METERS,
    INTERSECTION_TOLERANCE_METERS,
    PROCESSED_DATA_DIR,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)


def extract_zmg_graph(
    place_name: str = DEFAULT_PLACE_NAME,
    distance_meters: int = GRAPH_DISTANCE_METERS,
    tolerance_meters: int = INTERSECTION_TOLERANCE_METERS,
    custom_filter: str = CUSTOM_HIGHWAY_FILTER,
) -> nx.DiGraph:
    """
    Descarga y consolida la subred vial de corredores principales de la ZMG.
    """
    logger.info(f"Descargando red vial desde OpenStreetMap para: {place_name}...")

    # 1. Obtener grafo crudo
    G_raw = ox.graph_from_address(
        address=place_name,
        dist=distance_meters,
        network_type="drive",
        custom_filter=custom_filter,
        simplify=True,
    )
    logger.info(f"Grafo crudo: {len(G_raw.nodes)} nodos y {len(G_raw.edges)} aristas.")

    # 2. Proyectar a UTM para mediciones en metros y consolidar intersecciones
    logger.info(f"Consolidando intersecciones cercanas ({tolerance_meters}m)...")
    G_proj = ox.project_graph(G_raw)
    G_consolidated = ox.consolidate_intersections(
        G_proj,
        tolerance=tolerance_meters,
        rebuild_graph=True,
        dead_ends=False,
    )

    # 3. Re-proyectar a coordenadas geográficas WGS84 (Latitud/Longitud)
    G_final = ox.project_graph(G_consolidated, to_crs="EPSG:4326")
    logger.info(f"Grafo simplificado final: {len(G_final.nodes)} nodos principales.")

    return G_final


def compute_gaussian_adjacency_matrix(
    G: nx.DiGraph,
    threshold_meters: float = DISTANCE_THRESHOLD_METERS,
) -> Tuple[np.ndarray, List]:
    """
    Calcula la Matriz de Adyacencia Gaussiana (W) usando la distancia vial
    entre cada par de nodos con el Kernel RBF y un umbral de corte (threshold).
    Retorna la matriz W y la lista ordenada de nodos correspondientes.
    """
    nodes = list(G.nodes())
    num_nodes = len(nodes)
    logger.info(f"Calculando matriz de distancias viales para {num_nodes} nodos...")

    node_to_idx = {node_id: idx for idx, node_id in enumerate(nodes)}

    # Inicializar matriz de distancias con infinito y diagonal en cero
    d_matrix = np.full((num_nodes, num_nodes), np.inf, dtype=np.float64)
    np.fill_diagonal(d_matrix, 0.0)

    # Cálculo optimizado O(V * (E + V log V)) usando caminos mínimos desde cada fuente
    for source_node, lengths in nx.all_pairs_dijkstra_path_length(G, weight="length"):
        i = node_to_idx[source_node]
        for target_node, dist in lengths.items():
            j = node_to_idx[target_node]
            d_matrix[i, j] = dist

    # Obtener desviación estándar sigma de distancias válidas finitas
    valid_distances = d_matrix[np.isfinite(d_matrix) & (d_matrix > 0)]
    if valid_distances.size == 0:
        logger.warning("No se encontraron distancias finitas positivas entre nodos. Usando sigma=1.0")
        sigma = 1.0
    else:
        sigma = float(np.std(valid_distances))
        if sigma <= 0.0:
            logger.warning("Desviación estándar de distancias es 0. Usando sigma=1.0 para evitar división por cero.")
            sigma = 1.0

    logger.info(f"Desviación estándar (sigma) de distancias: {sigma:.2f} metros.")

    # Aplicar Kernel Gaussiano RBF vectorizado con umbral de corte
    mask = (d_matrix <= threshold_meters) & (d_matrix > 0)
    W = np.zeros((num_nodes, num_nodes), dtype=np.float32)
    W[mask] = np.exp(- ((d_matrix[mask] / sigma) ** 2))

    logger.info(f"Matriz de adyacencia W construida con éxito. Forma: {W.shape}")
    return W, nodes


def save_artifacts(G: nx.DiGraph, W: np.ndarray, nodes: List) -> None:
    """
    Guarda el grafo (.graphml), la matriz W (.npy) y el mapeo de nodos (.json)
    en data/processed/.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Asignar atributo node_index al grafo para persistencia directa
    for idx, node_id in enumerate(nodes):
        G.nodes[node_id]["node_index"] = idx

    # 2. Guardar matriz de adyacencia W
    w_path = PROCESSED_DATA_DIR / "adjacency_matrix.npy"
    np.save(w_path, W)
    logger.info(f"Matriz W guardada en: {w_path}")

    # 3. Guardar mapeo explícito de nodos (orden e IDs)
    node_mapping = {
        "ordered_nodes": [str(node_id) for node_id in nodes],
        "node_to_index": {str(node_id): idx for idx, node_id in enumerate(nodes)},
    }
    mapping_path = PROCESSED_DATA_DIR / "node_mapping.json"
    with open(mapping_path, "w", encoding="utf-8") as f:
        json.dump(node_mapping, f, indent=2)
    logger.info(f"Mapeo de nodos guardado en: {mapping_path}")

    # 4. Guardar el grafo vial usando OSMnx
    graphml_path = PROCESSED_DATA_DIR / "graph_zmg.graphml"
    ox.save_graphml(G, filepath=graphml_path)
    logger.info(f"Grafo guardado en: {graphml_path}")


if __name__ == "__main__":
    G = extract_zmg_graph()
    W, nodes = compute_gaussian_adjacency_matrix(G)
    save_artifacts(G, W, nodes)