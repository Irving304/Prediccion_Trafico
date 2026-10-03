import os
from pathlib import Path

# Directorio raíz del proyecto (TRAFICO)
BASE_DIR = Path(__file__).resolve().parent.parent

# Directorios de datos y artefactos
DATA_DIR = BASE_DIR / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
MODELS_DIR = BASE_DIR / "models"

# Configuración del Grafo y Modelo
NUM_NODES = 100
HISTORICAL_STEPS = 12  # 60 minutos de historial (12 pasos de 5 min)
PREDICTION_STEPS = [3, 6, 12]  # Horizontes a 15, 30 y 60 min