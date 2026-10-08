from pathlib import Path

# Directorio raíz del proyecto (TRAFICO)
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios de datos y artefactos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

# Configuración de Extracción de Grafo (OSMnx)
DEFAULT_PLACE_NAME = "Guadalajara, Jalisco, Mexico"
GRAPH_DISTANCE_METERS = 10000
INTERSECTION_TOLERANCE_METERS = 100
CUSTOM_HIGHWAY_FILTER = '["highway"~"motorway|primary|secondary"]'

# Configuración de Matriz de Adyacencia Gaussiana
DISTANCE_THRESHOLD_METERS = 5000.0

# Configuración del Modelo ST-GNN
TARGET_NUM_NODES = 400  # Nodos preliminares para la subred principal 
HISTORICAL_STEPS = 12   # 60 minutos de historial (12 pasos de 5 min)
PREDICTION_STEPS = [6, 12]  # Horizontes a 30 y 60 min (6 y 12 pasos de 5 min)
