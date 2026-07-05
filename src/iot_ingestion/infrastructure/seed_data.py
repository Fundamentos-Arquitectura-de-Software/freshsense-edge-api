from __future__ import annotations

from src.iot_ingestion.domain.freshness import CategoryThreshold

# Umbrales de referencia por categoria (temp °C / humedad %).
# Datos semilla; no dependen de ningun driver de BD para poder reutilizarse
# tambien en el catalogo en memoria (pruebas / fallback sin MySQL).
DEFAULT_THRESHOLDS: tuple[CategoryThreshold, ...] = (
    CategoryThreshold("Frutas", 2, 8, 85, 95),
    CategoryThreshold("Verduras", 0, 6, 90, 98),
    CategoryThreshold("Lácteos", 1, 5, 70, 85),
    CategoryThreshold("Carnes", -1, 4, 75, 85),
    CategoryThreshold("Proteínas", 0, 4, 75, 85),
    CategoryThreshold("Panadería", 16, 24, 50, 65),
    CategoryThreshold("Snacks", 16, 24, 40, 55),
)

# Dispositivo demo -> categoria, para que el flujo funcione de fabrica.
DEFAULT_DEVICE_CATEGORIES: dict[str, str] = {
    "esp32-freshsense-1": "Lácteos",
}
