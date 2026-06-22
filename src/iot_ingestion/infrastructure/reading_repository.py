from __future__ import annotations

from threading import Lock

from src.iot_ingestion.domain.sensor_reading import SensorReading


class InMemoryReadingRepository:
    def __init__(self) -> None:
        self._readings: list[SensorReading] = []
        self._lock = Lock()

    def add(self, reading: SensorReading) -> None:
        with self._lock:
            self._readings.append(reading)

    def all(self) -> list[SensorReading]:
        with self._lock:
            return list(self._readings)
