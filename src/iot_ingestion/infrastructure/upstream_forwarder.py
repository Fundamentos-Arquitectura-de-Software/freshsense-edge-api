from __future__ import annotations

import logging

import requests

from src.iot_ingestion.domain.freshness import FreshnessStatus
from src.iot_ingestion.domain.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

EDGE_AUTH_HEADER = "X-Device-Key"
BACKEND_TIME_FORMAT = "%d/%m/%Y %H:%M"


class BackendForwarder:
    def __init__(self, backend_url: str, timeout: float, auth_token: str = "") -> None:
        self._backend_url = backend_url
        self._timeout = timeout
        self._auth_token = auth_token

    def forward(
        self,
        reading: SensorReading,
        category: str | None,
        status: FreshnessStatus,
        secret_key: str | None = None,
    ) -> bool:
        if not self._backend_url:
            return False
        try:
            response = requests.post(
                self._backend_url,
                json=self._payload(reading, category, status),
                timeout=self._timeout,
                headers=self._headers(secret_key),
            )
            return 200 <= response.status_code < 300
        except requests.RequestException as exc:
            logger.warning("Fallo el reenvio de la lectura %s: %s", reading.reading_id, exc)
            return False

    def _headers(self, secret_key: str | None) -> dict[str, str]:
        # La clave por dispositivo (del claiming) tiene prioridad; si no hay,
        # se usa el token del constructor como respaldo (compatibilidad).
        token = secret_key or self._auth_token
        if not token:
            return {}
        return {EDGE_AUTH_HEADER: token}

    @staticmethod
    def _payload(
        reading: SensorReading, category: str | None, status: FreshnessStatus
    ) -> dict[str, object]:
        return {
            "deviceId": reading.device_id,
            "id": reading.reading_id,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "time": reading.recorded_at.strftime(BACKEND_TIME_FORMAT),
            # El semaforo ya viene clasificado del Edge; el backend solo lo persiste.
            "status": status.value,
            "category": category,
        }
