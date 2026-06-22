from __future__ import annotations

import logging

import requests

from src.iot_ingestion.domain.sensor_reading import SensorReading

logger = logging.getLogger(__name__)

EDGE_AUTH_HEADER = "X-Device-Key"
BACKEND_TIME_FORMAT = "%d/%m/%Y %H:%M"


class BackendForwarder:
    def __init__(self, backend_url: str, timeout: float, auth_token: str = "") -> None:
        self._backend_url = backend_url
        self._timeout = timeout
        self._auth_token = auth_token

    def forward(self, reading: SensorReading) -> bool:
        if not self._backend_url:
            return False
        try:
            response = requests.post(
                self._backend_url,
                json=self._payload(reading),
                timeout=self._timeout,
                headers=self._headers(),
            )
            return 200 <= response.status_code < 300
        except requests.RequestException as exc:
            logger.warning("Fallo el reenvio de la lectura %s: %s", reading.reading_id, exc)
            return False

    def _headers(self) -> dict[str, str]:
        if not self._auth_token:
            return {}
        return {EDGE_AUTH_HEADER: self._auth_token}

    @staticmethod
    def _payload(reading: SensorReading) -> dict[str, object]:
        return {
            "deviceId": reading.device_id,
            "id": reading.reading_id,
            "temperature": reading.temperature,
            "humidity": reading.humidity,
            "time": reading.recorded_at.strftime(BACKEND_TIME_FORMAT),
        }
