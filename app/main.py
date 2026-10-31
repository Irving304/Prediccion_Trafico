import json
from pathlib import Path
import numpy as np
import streamlit as st
import streamlit.components.v1 as components

# Configuración de página
st.set_page_config(
    page_title="Predicción de Tráfico ZMG | ST-GNN",
    page_icon="🚦",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = BASE_DIR / "data" / "processed"
MAP_HTML_PATH = PROCESSED_DATA_DIR / "mapa_nodos_zmg.html"
MAPPING_JSON_PATH = PROCESSED_DATA_DIR / "node_mapping.json"
ADJACENCY_NPY_PATH = PROCESSED_DATA_DIR / "adjacency_matrix.npy"


@st.cache_data
def load_graph_metadata():
    """Carga metadatos de los nodos y la matriz de adyacencia procesados."""
    num_nodes = 0
    matrix_shape = ("N/A", "N/A")
    sparsity = 0.0

    if MAPPING_JSON_PATH.exists():
        with open(MAPPING_JSON_PATH, "r", encoding="utf-8") as f:
            mapping = json.load(f)
            num_nodes = len(mapping.get("ordered_nodes", []))

    if ADJACENCY_NPY_PATH.exists():
        W = np.load(ADJACENCY_NPY_PATH)
        matrix_shape = W.shape
        non_zero = np.count_nonzero(W)
        total_elements = W.size
        sparsity = 100.0 * (1.0 - (non_zero / total_elements)) if total_elements > 0 else 0.0

    return num_nodes, matrix_shape, sparsity


num_nodes, matrix_shape, sparsity = load_graph_metadata()
# Barra lateral (Sidebar)
with st.sidebar:
    st.title("🚦 ST-GNN ZMG")
    st.caption("Sistema de Predicción Espacio-Temporal")
    st.markdown("---")

    st.subheader("Configuración de Inferencia")
    selected_horizon = st.radio(
        "Horizonte de Predicción:",
        options=["30 minutos", "60 minutos", "Ambos horizontes"],
        index=0,
        help="Tiempo futuro para el cual se estima la velocidad y congestión."
    )

    congestion_threshold = st.slider(
        "Umbral de congestión severa (km/h):",
        min_value=10,
        max_value=50,
        value=25,
        step=5,
        help="Velocidades por debajo de este valor se marcarán en alerta roja."
    )

    st.markdown("---")
    st.subheader("Estado de la Red")
    st.write(f"**Nodos modelados:** {num_nodes}")
    st.write(f"**Forma de Matriz W:** {matrix_shape[0]} × {matrix_shape[1]}")
    st.write(f"**Dispersión de W:** {sparsity:.1f}%")

    st.markdown("---")
    st.info("ℹ️ **Fase actual:** Topología de grafo consolidada. Pipeline de predicción en tiempo real en desarrollo.")
# Panel Principal
st.title("Sistema de Predicción Espacio-Temporal de Tráfico")
st.markdown(
    "Monitoreo y estimación multi-horizonte del flujo vehicular en los corredores "
    "principales de la **Zona Metropolitana de Guadalajara (ZMG)** mediante Graph Neural Networks."
)
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="Nodos en la Red (Vías Principales)", value=f"{num_nodes}")
with col2:
    st.metric(label="Horizontes Objetivo", value="30 y 60 min", delta="Multi-horizonte")
with col3:
    st.metric(label="Granularidad Temporal", value="5 min", delta="12 pasos/hora")
with col4:
    st.metric(label="Horizonte Seleccionado", value=selected_horizon.split()[0] + " min")

st.markdown("---")

# Visualización del Mapa Interactivo
st.subheader("Mapa de Topología Vial y Red de Monitoreo")

if MAP_HTML_PATH.exists():
    with open(MAP_HTML_PATH, "r", encoding="utf-8") as f:
        html_content = f.read()
    components.html(html_content, height=620, scrolling=True)
else:
    st.warning(
        f"No se encontró el mapa generado en `{MAP_HTML_PATH}`. "
        "Ejecuta `python src/visualize_graph.py` para construirlo."
    )