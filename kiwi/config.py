"""Configuración central: modelos, precios y rutas."""

import os

from dotenv import load_dotenv

load_dotenv()

# Modelos de imagen disponibles en la interfaz (nombre visible -> id de la API).
IMAGE_MODELS: dict[str, str] = {
    "Nano Banana 2.1": "gemini-nano-banana-2.1",
    "Nano Banana Pro": "gemini-3-pro-image",
}
DEFAULT_IMAGE_MODEL = "Nano Banana 2.1"

# Modelo de texto para interpretar el brief (tiene nivel gratuito).
TEXT_MODEL = os.environ.get("KIWI_TEXT_MODEL", "gemini-3.8-flash")

IMAGE_SIZES = ["1K", "2K", "4K"]
ASPECT_RATIOS = ["1:1", "4:5", "9:16", "16:9"]

# Precio aproximado en USD por imagen generada (tarifa estándar, nov. 2026).
# Solo se usa para mostrar una estimación.
PRICE_PER_IMAGE: dict[str, dict[str, float]] = {
    "gemini-nano-banana-2.1": {"1K": 0.0336, "2K": 0.0504, "4K": 0.113},
    "gemini-3-pro-image": {"1K": 0.134, "2K": 0.134, "4K": 0.24},
}

# Carpeta donde se guarda cada trabajo (una subcarpeta por fecha, como DD-MM-YY).
OUTPUT_DIR = os.environ.get("KIWI_OUTPUT_DIR", os.path.join(os.path.dirname(os.path.dirname(__file__)), "trabajos"))

MAX_PARALLEL_IMAGES = 4


def get_api_key() -> str:
    return os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY") or ""


def estimate_cost(model_id: str, size: str, count: int = 1) -> float:
    return PRICE_PER_IMAGE.get(model_id, {}).get(size, 0.0) * count
