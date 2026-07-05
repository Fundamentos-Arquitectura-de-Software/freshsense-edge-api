from __future__ import annotations

import logging

from src.config import Settings
from src.iot_ingestion.domain.freshness import CategoryThreshold
from src.iot_ingestion.infrastructure.mysql import connect

logger = logging.getLogger(__name__)


class MySqlThresholdCatalog:
    """Catalogo de umbrales respaldado por el MySQL local del Edge.

    Cada operacion abre y cierra su propia conexion (volumen bajo). Ante un
    fallo de BD, las lecturas degradan a UNKNOWN en vez de romper la ingesta:
    los getters devuelven None y se registra el error."""

    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    def category_for_device(self, device_id: str) -> str | None:
        try:
            with connect(self._settings) as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT category FROM device_categories WHERE device_id = %s",
                    (device_id,),
                )
                row = cur.fetchone()
                return row["category"] if row else None
        except Exception:
            logger.exception("No se pudo leer la categoria del device %s", device_id)
            return None

    def threshold_for_category(self, category: str) -> CategoryThreshold | None:
        try:
            with connect(self._settings) as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT category, temp_min, temp_max, humidity_min, humidity_max "
                    "FROM category_thresholds WHERE category = %s",
                    (category,),
                )
                row = cur.fetchone()
                return _to_threshold(row) if row else None
        except Exception:
            logger.exception("No se pudo leer el umbral de la categoria %s", category)
            return None

    def list_thresholds(self) -> list[CategoryThreshold]:
        try:
            with connect(self._settings) as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT category, temp_min, temp_max, humidity_min, humidity_max "
                    "FROM category_thresholds ORDER BY category"
                )
                return [_to_threshold(row) for row in cur.fetchall()]
        except Exception:
            logger.exception("No se pudieron listar los umbrales")
            return []

    def list_device_categories(self) -> dict[str, str]:
        try:
            with connect(self._settings) as conn, conn.cursor() as cur:
                cur.execute("SELECT device_id, category FROM device_categories ORDER BY device_id")
                return {row["device_id"]: row["category"] for row in cur.fetchall()}
        except Exception:
            logger.exception("No se pudieron listar los mapeos device -> categoria")
            return {}

    def set_device_category(self, device_id: str, category: str) -> None:
        with connect(self._settings) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO device_categories (device_id, category) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE category = VALUES(category)",
                (device_id, category),
            )

    def secret_for_device(self, device_id: str) -> str | None:
        try:
            with connect(self._settings) as conn, conn.cursor() as cur:
                cur.execute(
                    "SELECT secret_key FROM device_categories WHERE device_id = %s",
                    (device_id,),
                )
                row = cur.fetchone()
                return row["secret_key"] if row and row["secret_key"] else None
        except Exception:
            logger.exception("No se pudo leer la clave del device %s", device_id)
            return None

    def set_secret_for_device(self, device_id: str, secret_key: str) -> None:
        with connect(self._settings) as conn, conn.cursor() as cur:
            cur.execute(
                "INSERT INTO device_categories (device_id, secret_key) VALUES (%s, %s) "
                "ON DUPLICATE KEY UPDATE secret_key = VALUES(secret_key)",
                (device_id, secret_key),
            )


def _to_threshold(row: dict) -> CategoryThreshold:
    return CategoryThreshold(
        category=row["category"],
        temp_min=row["temp_min"],
        temp_max=row["temp_max"],
        humidity_min=row["humidity_min"],
        humidity_max=row["humidity_max"],
    )
